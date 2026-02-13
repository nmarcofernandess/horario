from typing import List, Dict, Optional
from datetime import date
from sqlalchemy.orm import Session
import pandas as pd
from apps.backend.src.domain.models import Employee, PreferenceRequest, RequestType, RequestDecision, Shift, ShiftDayScope, ScheduleException, ExceptionType, DemandSlot
from apps.backend.src.infrastructure.database.orm_models import (
    EmployeeORM,
    PreferenceORM,
    SectorORM,
    ContractORM,
    GovernanceAuditEventORM,
)
from apps.backend.src.infrastructure.database.extended_orm import ShiftORM, CycleTemplateORM, SundayRotationORM, ExceptionORM, DemandProfileORM

class SqlAlchemyRepository:
    def __init__(self, session: Session):
        self.session = session

    def load_employees(self) -> Dict[str, Employee]:
        # Fetch active or all? Let's fetch all active.
        orm_employees = self.session.query(EmployeeORM).filter(EmployeeORM.active == True).all()
        employees = {}
        for oe in orm_employees:
            employees[oe.employee_id] = Employee(
                employee_id=oe.employee_id,
                name=oe.name,
                contract_code=oe.contract_code,
                sector_id=oe.sector_id,
                rank=oe.rank,
                active=oe.active
            )
        return employees

    def load_preferences(self) -> List[PreferenceRequest]:
        orm_prefs = self.session.query(PreferenceORM).all()
        reqs = []
        for op in orm_prefs:
            reqs.append(PreferenceRequest(
                request_id=op.request_id,
                employee_id=op.employee_id,
                request_date=op.request_date,
                request_type=RequestType(op.request_type),
                priority=op.priority,
                target_shift_code=op.target_shift_code,
                note=op.note,
                decision=RequestDecision(op.decision) if op.decision else RequestDecision.PENDING,
                decision_reason=op.decision_reason
            ))
        return reqs
    
    # WRITE METHODS (For CRUD UI and Seeding)
    
    def load_contract_targets(self, sector_id: str = "CAIXA") -> Dict[str, int]:
        """Retorna mapeamento employee_id -> weekly_minutes para validação de meta semanal."""
        orm_emps = self.session.query(EmployeeORM).filter(
            EmployeeORM.active == True,
            EmployeeORM.sector_id == sector_id
        ).all()
        orm_contracts = {c.contract_code: c.weekly_minutes for c in self.session.query(ContractORM).all()}
        return {e.employee_id: orm_contracts.get(e.contract_code, 2640) for e in orm_emps}

    def load_contract_profiles(self, sector_id: str = "CAIXA") -> Dict[str, Dict[str, int | str]]:
        """Retorna mapeamento employee_id -> {contract_code, weekly_minutes, max_consecutive_sundays}."""
        orm_emps = self.session.query(EmployeeORM).filter(
            EmployeeORM.active == True,
            EmployeeORM.sector_id == sector_id
        ).all()
        orm_contracts = {
            c.contract_code: {
                "contract_code": c.contract_code, 
                "weekly_minutes": c.weekly_minutes,
                "max_consecutive_sundays": c.max_consecutive_sundays or 2
            }
            for c in self.session.query(ContractORM).all()
        }
        result: Dict[str, Dict[str, int | str]] = {}
        for e in orm_emps:
            profile = orm_contracts.get(e.contract_code, {
                "contract_code": e.contract_code, 
                "weekly_minutes": 2640,
                "max_consecutive_sundays": 2
            })
            result[e.employee_id] = profile
        return result

    def add_governance_audit_event(
        self,
        *,
        operation: str,
        mode: str,
        actor_role: str,
        actor_name: Optional[str],
        reason: Optional[str],
        warnings: List[str],
        sector_id: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> int:
        event = GovernanceAuditEventORM(
            operation=operation,
            mode=mode,
            actor_role=actor_role,
            actor_name=actor_name,
            reason=reason,
            warnings_json=warnings,
            sector_id=sector_id,
            period_start=period_start,
            period_end=period_end,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return int(event.id)

    def list_governance_audit_events(self, limit: int = 50) -> List[dict]:
        rows = (
            self.session.query(GovernanceAuditEventORM)
            .order_by(GovernanceAuditEventORM.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "event_id": int(r.id),
                "created_at": str(r.created_at),
                "operation": str(r.operation),
                "mode": str(r.mode),
                "actor_role": str(r.actor_role),
                "actor_name": r.actor_name,
                "reason": r.reason,
                "warnings": [str(w) for w in (r.warnings_json or [])],
                "sector_id": r.sector_id,
                "period_start": r.period_start,
                "period_end": r.period_end,
            }
            for r in rows
        ]

    def load_sectors(self) -> List[tuple]:
        """Retorna lista de (sector_id, name) ordenados por nome."""
        orm_sectors = self.session.query(SectorORM).filter(SectorORM.active == True).all()
        return [(s.sector_id, s.name) for s in sorted(orm_sectors, key=lambda x: x.name)]

    def add_sector(self, sector_id: str, name: str):
        if self.session.get(SectorORM, sector_id) is None:
            self.session.add(SectorORM(sector_id=sector_id, name=name))
            self.session.commit()

    def add_contract(self, code: str, sector_id: str, minutes: int, max_consecutive_sundays: int = 2):
        if self.session.get(ContractORM, code) is None:
            self.session.add(ContractORM(
                contract_code=code, 
                sector_id=sector_id, 
                weekly_minutes=minutes,
                max_consecutive_sundays=max_consecutive_sundays
            ))
            self.session.commit()

    def add_employee(self, e: Employee):
        """Adiciona ou atualiza colaborador (upsert). Atualiza nome para formato agradável quando já existe."""
        existing = self.session.get(EmployeeORM, e.employee_id)
        if existing is None:
            self.session.add(EmployeeORM(
                employee_id=e.employee_id,
                name=e.name,
                contract_code=e.contract_code,
                sector_id=e.sector_id,
                rank=e.rank,
                active=e.active
            ))
        else:
            existing.name = e.name
            existing.contract_code = e.contract_code
        self.session.commit()

    def update_employee_rank(self, employee_id: str, rank: int):
        emp = self.session.get(EmployeeORM, employee_id)
        if emp:
            emp.rank = rank
            self.session.commit()

    def add_preference(self, req: PreferenceRequest):
        if self.session.get(PreferenceORM, req.request_id) is None:
            self.session.add(PreferenceORM(
                request_id=req.request_id,
                employee_id=req.employee_id,
                request_date=req.request_date,
                request_type=req.request_type.value,
                priority=req.priority,
                target_shift_code=req.target_shift_code,
                note=req.note
            ))
            self.session.commit()
    
    def update_preference_decision(self, request_id: str, decision: RequestDecision, reason: str):
         pref = self.session.get(PreferenceORM, request_id)
         if pref:
             pref.decision = decision.value
             pref.decision_reason = reason
             self.session.commit()

    # Exceptions (férias, atestado, trocas, bloqueios)
    def load_exceptions(self, sector_id: str = None, period_start=None, period_end=None) -> list:
        """Carrega exceções, opcionalmente filtradas por setor e período."""
        q = self.session.query(ExceptionORM)
        if sector_id:
            q = q.filter(ExceptionORM.sector_id == sector_id)
        if period_start:
            q = q.filter(ExceptionORM.exception_date >= period_start)
        if period_end:
            q = q.filter(ExceptionORM.exception_date <= period_end)
        rows = q.all()
        return [
            ScheduleException(
                sector_id=r.sector_id,
                employee_id=r.employee_id,
                exception_date=r.exception_date,
                exception_type=ExceptionType(r.exception_type),
                note=r.note or ""
            )
            for r in rows
        ]

    def add_exception(self, exc: ScheduleException):
        """Adiciona exceção (evita duplicata por sector+employee+date+type)."""
        existing = self.session.query(ExceptionORM).filter(
            ExceptionORM.sector_id == exc.sector_id,
            ExceptionORM.employee_id == exc.employee_id,
            ExceptionORM.exception_date == exc.exception_date,
            ExceptionORM.exception_type == exc.exception_type.value,
        ).first()
        if not existing:
            self.session.add(ExceptionORM(
                sector_id=exc.sector_id,
                employee_id=exc.employee_id,
                exception_date=exc.exception_date,
                exception_type=exc.exception_type.value,
                note=exc.note
            ))
            self.session.commit()

    def remove_exception(self, sector_id: str, employee_id: str, exception_date, exception_type: str) -> bool:
        """Remove exceção específica."""
        deleted = self.session.query(ExceptionORM).filter(
            ExceptionORM.sector_id == sector_id,
            ExceptionORM.employee_id == employee_id,
            ExceptionORM.exception_date == exception_date,
            ExceptionORM.exception_type == exception_type,
        ).delete()
        self.session.commit()
        return deleted > 0

    # Demand profile (cobertura por faixa horária)
    def load_demand_profile(self, sector_id: str, period_start=None, period_end=None) -> list:
        """Carrega demand_profile para validação de cobertura."""
        q = self.session.query(DemandProfileORM).filter(DemandProfileORM.sector_id == sector_id)
        if period_start:
            q = q.filter(DemandProfileORM.work_date >= period_start)
        if period_end:
            q = q.filter(DemandProfileORM.work_date <= period_end)
        rows = q.all()
        return [
            DemandSlot(
                sector_id=r.sector_id,
                work_date=r.work_date,
                slot_start=r.slot_start,
                min_required=r.min_required,
            )
            for r in rows
        ]

    def add_demand_slot(self, slot: DemandSlot):
        """Adiciona slot de demanda (evita duplicata)."""
        existing = self.session.query(DemandProfileORM).filter(
            DemandProfileORM.sector_id == slot.sector_id,
            DemandProfileORM.work_date == slot.work_date,
            DemandProfileORM.slot_start == slot.slot_start,
        ).first()
        if not existing:
            self.session.add(DemandProfileORM(
                sector_id=slot.sector_id,
                work_date=slot.work_date,
                slot_start=slot.slot_start,
                min_required=slot.min_required,
            ))
            self.session.commit()

    def remove_demand_slot(self, sector_id: str, work_date, slot_start: str) -> bool:
        """Remove slot de demanda específico."""
        deleted = self.session.query(DemandProfileORM).filter(
            DemandProfileORM.sector_id == sector_id,
            DemandProfileORM.work_date == work_date,
            DemandProfileORM.slot_start == slot_start,
        ).delete()
        self.session.commit()
        return deleted > 0

    def save_demand_profile_bulk(self, items: list):
        """Substitui demand_profile do setor/período por nova lista."""
        if not items:
            return
        sector_id = items[0].sector_id
        dates = {i.work_date for i in items}
        self.session.query(DemandProfileORM).filter(
            DemandProfileORM.sector_id == sector_id,
            DemandProfileORM.work_date.in_(dates),
        ).delete(synchronize_session=False)
        for slot in items:
            self.session.add(DemandProfileORM(
                sector_id=slot.sector_id,
                work_date=slot.work_date,
                slot_start=slot.slot_start,
                min_required=slot.min_required,
            ))
        self.session.commit()

    # Helpers for existing pipeline (Sunday Rotation / Template)
    # These are still file-based or could be moved to DB tables (Phase 2)
    # For now, we reuse FileSystemRepository for these specific reads
    # Or implement dummy if we want pure DB.
    # The requirement is "Accept our data to register everything".
    # So we need to support registration.
    

    def load_sunday_rotation(self, sector_id: str = "CAIXA"):
        # Scope por setor via colaboradores vinculados ao setor.
        sector_employee_ids = [
            row[0]
            for row in self.session.query(EmployeeORM.employee_id).filter(EmployeeORM.sector_id == sector_id).all()
        ]
        if not sector_employee_ids:
            return pd.DataFrame()

        rotations = self.session.query(SundayRotationORM).filter(
            SundayRotationORM.employee_id.in_(sector_employee_ids)
        ).all()
        if not rotations:
            return pd.DataFrame() # Empty
            
        data = []
        for r in rotations:
            data.append({
                "scale_index": r.scale_index,
                "employee_id": r.employee_id,
                "sunday_date": r.sunday_date,
                "folga_date": r.folga_date
            })
        return pd.DataFrame(data)

    def load_weekday_template_data(self, sector_id: str = "CAIXA"):
         # Escopo por setor usando source namespaced: TEMPLATE_BASE:<SECTOR_ID>.
         source_key = f"TEMPLATE_BASE:{sector_id}"
         temps = self.session.query(CycleTemplateORM).filter(CycleTemplateORM.source == source_key).all()
         # Fallback para legado sem namespace (piloto CAIXA já existente).
         if not temps and sector_id == "CAIXA":
             temps = self.session.query(CycleTemplateORM).filter(CycleTemplateORM.source == "TEMPLATE_BASE").all()
         if not temps:
             return pd.DataFrame()
             
         data = []
         for t in temps:
             data.append({
                 "employee_id": t.employee_id,
                 "day_key": t.day_key, # MON, TUE
                 "shift_code": t.shift_code,
                 "minutes": t.minutes
             })
         # Pivot back to user friendly? Or just return raw
         return pd.DataFrame(data)

    def save_sunday_rotation(self, df_rot, sector_id: str = "CAIXA"):
        # Replace scoped por setor (via employee_id vinculado ao setor).
        sector_employee_ids = [
            row[0]
            for row in self.session.query(EmployeeORM.employee_id).filter(EmployeeORM.sector_id == sector_id).all()
        ]
        self.session.query(SundayRotationORM).filter(
            SundayRotationORM.employee_id.in_(sector_employee_ids)
        ).delete(synchronize_session=False)

        for _, row in df_rot.iterrows():
            # Convert to Python date objects (SQLite requirement)
            s_date = pd.to_datetime(row['sunday_date']).date()
            f_date = pd.to_datetime(row['folga_date']).date() if pd.notna(row['folga_date']) else None
            employee_id = row['employee_id']
            if employee_id not in sector_employee_ids:
                raise ValueError(f"employee_id '{employee_id}' não pertence ao setor '{sector_id}'")
            
            self.session.add(SundayRotationORM(
                scale_index=int(row['scale_index']),
                employee_id=employee_id,
                sunday_date=s_date,
                folga_date=f_date
            ))
        self.session.commit()


    def load_shifts(self, sector_id: str = "CAIXA") -> Dict[str, Shift]:
        orm_shifts = self.session.query(ShiftORM).filter(ShiftORM.sector_id == sector_id).all()
        return {
            s.shift_code: Shift(
                code=s.shift_code,
                minutes=s.minutes,
                day_scope=ShiftDayScope(s.day_scope),
                sector_id=s.sector_id
            ) for s in orm_shifts
        }

    def upsert_shift(self, shift_code: str, sector_id: str, minutes: int, day_scope: str) -> Shift:
        existing = self.session.get(ShiftORM, shift_code)
        if existing and existing.sector_id != sector_id:
            raise ValueError(f"shift_code '{shift_code}' já existe em outro setor")
        if existing is None:
            existing = ShiftORM(
                shift_code=shift_code,
                sector_id=sector_id,
                minutes=minutes,
                day_scope=day_scope,
            )
            self.session.add(existing)
        else:
            existing.minutes = minutes
            existing.day_scope = day_scope
            existing.sector_id = sector_id
        self.session.commit()
        return Shift(
            code=existing.shift_code,
            sector_id=existing.sector_id,
            minutes=existing.minutes,
            day_scope=ShiftDayScope(existing.day_scope),
        )

    def remove_shift(self, shift_code: str, sector_id: str = "CAIXA") -> bool:
        deleted = self.session.query(ShiftORM).filter(
            ShiftORM.shift_code == shift_code,
            ShiftORM.sector_id == sector_id,
        ).delete(synchronize_session=False)
        self.session.commit()
        return deleted > 0

    def save_shifts(self, df_shifts, sector_id: str = "CAIXA"):
        # Replace shifts for this sector only
        self.session.query(ShiftORM).filter(ShiftORM.sector_id == sector_id).delete(synchronize_session=False)
        # Ensure we don't have duplicates in the DF itself
        df_clean = df_shifts.drop_duplicates('shift_code')
        for _, row in df_clean.iterrows():
            self.session.add(ShiftORM(
                shift_code=row['shift_code'],
                sector_id=sector_id,
                minutes=int(row.get('minutes_median', row.get('minutes', 480))),
                day_scope=row.get('day_scope', 'WEEKDAY')
            ))
        self.session.commit()

    def save_weekday_template(self, df_slots, sector_id: str = "CAIXA"):
        # Clear scoped template records
        source_key = f"TEMPLATE_BASE:{sector_id}"
        self.session.query(CycleTemplateORM).filter(CycleTemplateORM.source == source_key).delete(synchronize_session=False)
        # Migração suave: no setor piloto CAIXA, limpar legado não namespaced.
        if sector_id == "CAIXA":
            self.session.query(CycleTemplateORM).filter(CycleTemplateORM.source == "TEMPLATE_BASE").delete(synchronize_session=False)
        day_col = 'day_name' if 'day_name' in df_slots.columns else 'day_key'
        for _, row in df_slots.iterrows():
            self.session.add(CycleTemplateORM(
                scale_id=1, # Default anchor
                cycle_day=1, # This is a template, day mapping happens in engine
                employee_id=row['employee_id'],
                day_key=row[day_col], # SEG, TER, MON...
                shift_code=row['shift_code'],
                minutes=int(row.get('minutes_median', 0)),
                status="WORK",
                source=source_key
            ))
        self.session.commit()
