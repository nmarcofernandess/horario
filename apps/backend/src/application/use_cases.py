from pathlib import Path
from typing import Dict, Any, List
import json
import pandas as pd
from datetime import date

from apps.backend.src.domain.models import ProjectionContext, Violation, ShiftDayScope, Shift
from apps.backend.src.domain.policy_loader import PolicyLoader
from apps.backend.src.domain.engines import CycleGenerator, PolicyEngine
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter
from apps.backend.src.infrastructure.presenters.export_calendar import export_calendar_files

class ValidationOrchestrator:
    def __init__(
        self,
        repo: SqlAlchemyRepository,
        policy_loader: PolicyLoader,
        output_path: Path,
        data_dir: Path = None
    ):
        self.repo = repo
        self.policy_loader = policy_loader
        self.output_path = output_path
        self.data_dir = data_dir or (Path(__file__).resolve().parents[4] / "data" / "fixtures")
        self.generator = CycleGenerator()
        self.policy_engine = PolicyEngine()

    def run(
        self,
        context: ProjectionContext,
        policy_path: Path,
        persist_results: bool = True,
        include_preview: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes the full validation pipeline using the new Engines.
        """
        # 1. Load Policy
        policy = self.policy_loader.load_policy(policy_path)
        
        # 2. Load Inputs from DB/Repo (fallback to CSV when DB empty)
        sunday_rotation = self.repo.load_sunday_rotation(sector_id=context.sector_id)
        weekday_template_raw = self.repo.load_weekday_template_data(sector_id=context.sector_id)
        
        if (sunday_rotation.empty or weekday_template_raw.empty) and context.sector_id == "CAIXA":
            importer = LegacyCSVImporter(self.data_dir)
            if sunday_rotation.empty:
                sunday_rotation = importer.load_sunday_rotation()
            if weekday_template_raw.empty:
                weekday_template_raw = importer.load_base_slots()
                if not weekday_template_raw.empty:
                    weekday_template_raw = weekday_template_raw.drop_duplicates(["employee_id", "day_name"])
        
        # Build Shift Objects from Policy (or DB if available)
        shifts = policy.shifts
        sunday_shift = policy.shifts.get("DOM_08_12_30")
        if sunday_shift:
            sunday_code, sunday_mins = sunday_shift.code, sunday_shift.minutes
        else:
            sunday_code, sunday_mins = "H_DOM", 300
        
        # 3. Build Scale Cycle
        if "day_name" not in weekday_template_raw.columns and "day_key" in weekday_template_raw.columns:
            weekday_template_raw = weekday_template_raw.copy()
            weekday_template_raw["day_name"] = weekday_template_raw["day_key"]

        week_template = self.generator.build_weekday_template(weekday_template_raw, shifts)
        
        scale_cycle = self.generator.build_scale_cycle(
            sunday_rotation, 
            week_template, 
            sunday_code,
            sunday_mins
        )
        
        if scale_cycle.empty:
            raise ValueError(
                "Não há dados suficientes para gerar a escala. "
                "Execute o seed (python scripts/seed.py) ou configure Mosaico e Rodízio de domingos na página Configuração."
            )
        
        # 4. Project — anchor_date = primeiro domingo do rodízio para alinhar ciclo ao calendário
        anchor_date = None
        if not sunday_rotation.empty and "sunday_date" in sunday_rotation.columns:
            min_sun = pd.to_datetime(sunday_rotation["sunday_date"]).min()
            if pd.notna(min_sun):
                anchor_date = min_sun.date() if hasattr(min_sun, "date") else min_sun
        context_proj = ProjectionContext(
            period_start=context.period_start,
            period_end=context.period_end,
            sector_id=context.sector_id,
            anchor_scale_id=context.anchor_scale_id,
            anchor_date=anchor_date,
        )
        final_assignments = self.generator.project_cycle_to_period(scale_cycle, context_proj)
        
        # 5. Preferences: aplicar pedidos aprovados
        processed_requests = []
        preferences = self.repo.load_preferences()
        approved = [p for p in preferences if p.decision.value == "APPROVED"]
        for pref in approved:
            mask = (final_assignments["employee_id"] == pref.employee_id) & \
                   (pd.to_datetime(final_assignments["work_date"]) == pd.Timestamp(pref.request_date))
            if not mask.any():
                continue
            if pref.request_type.value == "FOLGA_ON_DATE":
                final_assignments.loc[mask, ["status", "shift_code", "minutes", "source_rule"]] = ["FOLGA", "", 0, "PREFERENCE_APPLIED"]
                processed_requests.append({"request_id": pref.request_id, "applied": True})
            elif pref.request_type.value == "AVOID_SUNDAY_DATE":
                final_assignments.loc[mask, ["status", "shift_code", "minutes", "source_rule"]] = ["FOLGA", "", 0, "PREFERENCE_APPLIED"]
                processed_requests.append({"request_id": pref.request_id, "applied": True})
            elif pref.request_type.value == "SHIFT_CHANGE_ON_DATE" and pref.target_shift_code:
                target_shift = policy.shifts.get(pref.target_shift_code)
                new_mins = int(target_shift.minutes) if target_shift else 480
                final_assignments.loc[mask, ["shift_code", "minutes", "source_rule"]] = [pref.target_shift_code, new_mins, "PREFERENCE_APPLIED"]
                processed_requests.append({"request_id": pref.request_id, "applied": True})

        # 5b. Exceptions: aplicar férias, atestado, trocas, bloqueios (convertem WORK -> ABSENCE)
        exceptions = self.repo.load_exceptions(
            sector_id=context.sector_id,
            period_start=context.period_start,
            period_end=context.period_end,
        )
        exceptions_applied = 0
        for exc in exceptions:
            mask = (final_assignments["employee_id"] == exc.employee_id) & \
                   (pd.to_datetime(final_assignments["work_date"]) == pd.Timestamp(exc.exception_date))
            if mask.any():
                # Converte WORK em ABSENCE (ou FOLGA se já era folga — mantém)
                work_mask = mask & (final_assignments["status"] == "WORK")
                if work_mask.any():
                    final_assignments.loc[work_mask, ["status", "shift_code", "minutes", "source_rule"]] = [
                        "ABSENCE", "", 0, f"EXCEPTION_{exc.exception_type.value}"
                    ]
                    exceptions_applied += 1

        # 6. Violations — contract_targets do DB (employee -> meta semanal)
        contract_targets = self.repo.load_contract_profiles(context.sector_id)
        violations_cons = self.policy_engine.validate_consecutive_days(final_assignments)
        violations_hours = self.policy_engine.validate_weekly_hours(final_assignments, contract_targets)
        violations_intershift = self.policy_engine.validate_intershift_rest(
            final_assignments, policy.shifts, policy.constraints
        )
        violations_daily = self.policy_engine.validate_daily_minutes(
            final_assignments, policy.constraints
        )
        demand_slots = self.repo.load_demand_profile(
            context.sector_id, context.period_start, context.period_end
        )
        violations_demand = self.policy_engine.validate_demand_coverage(
            final_assignments, demand_slots, policy.shifts
        )

        violations = violations_cons + violations_hours + violations_intershift + violations_daily + violations_demand
        
        # 7. Persist Results (apenas geração oficial)
        if persist_results:
            self._export_results_df(final_assignments, processed_requests, violations, context)

        # 8. Export HTML/Markdown calendário + resumo semanal (PRD)
        emp_names = {e.employee_id: e.name for e in self.repo.load_employees().values()}
        week_def = getattr(policy.week_definition, "value", "MON_SUN") if hasattr(policy, "week_definition") else "MON_SUN"
        export_paths = {}
        if persist_results:
            try:
                export_paths = export_calendar_files(
                    self.output_path,
                    final_assignments,
                    violations,
                    contract_targets,
                    context.period_start,
                    context.period_end,
                    employee_names=emp_names,
                    week_definition=week_def,
                )
            except Exception:
                pass

        result = {
            "status": "SUCCESS",
            "violations_count": len(violations),
            "assignments_count": len(final_assignments),
            "preferences_processed": len(processed_requests),
            "exceptions_applied": exceptions_applied,
            "export_paths": export_paths,
        }
        if include_preview:
            result["preview_assignments"] = final_assignments.to_dict("records")
            result["preview_violations"] = [
                {
                    "employee_id": v.employee_id,
                    "rule_code": v.rule_code,
                    "severity": v.severity.value,
                    "date_start": v.date_start,
                    "date_end": v.date_end,
                    "detail": v.detail,
                }
                for v in violations
            ]
        return result

    def _export_results_df(self, assignments_df, requests, violations, context):
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Assignments
        assignments_df.to_csv(self.output_path / "final_assignments.csv", index=False)
        
        # Preferences (Empty for now)
        pd.DataFrame(requests).to_csv(self.output_path / "preference_decisions.csv", index=False)
        
        # Violations
        v_data = [{
            "employee_id": v.employee_id, 
            "rule_code": v.rule_code, 
            "severity": v.severity.value, 
            "date_start": v.date_start, 
            "date_end": v.date_end,
            "detail": v.detail
        } for v in violations]
        pd.DataFrame(v_data).to_csv(self.output_path / "violations.csv", index=False)




