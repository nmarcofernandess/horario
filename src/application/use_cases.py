from pathlib import Path
from typing import Dict, Any, List
import json
import pandas as pd
from datetime import date

from src.domain.models import ProjectionContext, Violation, ShiftDayScope, Shift
from src.domain.policy_loader import PolicyLoader
from src.domain.engines import CycleGenerator, PolicyEngine
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter

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
        self.data_dir = data_dir or (Path(__file__).resolve().parents[2] / "data" / "processed")
        self.generator = CycleGenerator()
        self.policy_engine = PolicyEngine()

    def run(self, context: ProjectionContext, policy_path: Path) -> Dict[str, Any]:
        """
        Executes the full validation pipeline using the new Engines.
        """
        # 1. Load Policy
        policy = self.policy_loader.load_policy(policy_path)
        
        # 2. Load Inputs from DB/Repo (fallback to CSV when DB empty)
        sunday_rotation = self.repo.load_sunday_rotation()
        weekday_template_raw = self.repo.load_weekday_template_data()
        
        if sunday_rotation.empty or weekday_template_raw.empty:
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
                "Cadastre o Ciclo de Domingos e o Mosaico Base (página Regras de Negócio) ou execute: python scripts/seed_db_from_csv.py"
            )
        
        # 4. Project
        final_assignments = self.generator.project_cycle_to_period(scale_cycle, context)
        
        # 5. Preferences (TODO: Re-enable when ported)
        processed_requests = [] 
        # preferences = self.repo.load_preferences()
        # final_assignments, processed_requests = ...
        
        # 6. Violations
        # Convert DataFrame assignments back to list if needed, or PolicyEngine works on DF
        violations_cons = self.policy_engine.validate_consecutive_days(final_assignments)
        violations_hours = self.policy_engine.validate_weekly_hours(final_assignments, {})
        
        violations = violations_cons + violations_hours
        
        # 7. Persist Results
        # Export needs list of dicts or DF. The engine usage returns DF.
        # _export_results expects objects, let's adjust it to accept DF or convert
        self._export_results_df(final_assignments, processed_requests, violations, context)
        
        return {
            "status": "SUCCESS",
            "violations_count": len(violations),
            "assignments_count": len(final_assignments),
            "preferences_processed": len(processed_requests)
        }

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




