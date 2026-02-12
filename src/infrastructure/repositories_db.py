from typing import List, Dict, Optional
from datetime import date
from sqlalchemy.orm import Session
import pandas as pd
from src.domain.models import Employee, PreferenceRequest, RequestType, RequestDecision, Shift, ShiftDayScope, ScheduleException, ExceptionType, DemandSlot
from src.infrastructure.database.orm_models import EmployeeORM, PreferenceORM, SectorORM, ContractORM
from src.infrastructure.database.extended_orm import ShiftORM, CycleTemplateORM, SundayRotationORM, ExceptionORM, DemandProfileORM

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

    def load_sectors(self) -> List[tuple]:
        """Retorna lista de (sector_id, name) ordenados por nome."""
        orm_sectors = self.session.query(SectorORM).filter(SectorORM.active == True).all()
        return [(s.sector_id, s.name) for s in sorted(orm_sectors, key=lambda x: x.name)]

    def add_sector(self, sector_id: str, name: str):
        if self.session.get(SectorORM, sector_id) is None:
            self.session.add(SectorORM(sector_id=sector_id, name=name))
            self.session.commit()

    def add_contract(self, code: str, sector_id: str, minutes: int):
        if self.session.get(ContractORM, code) is None:
            self.session.add(ContractORM(
                contract_code=code, sector_id=sector_id, weekly_minutes=minutes
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

    def remove_exception(self, sector_id: str, employee_id: str, exception_date, exception_type: str):
        """Remove exceção específica."""
        self.session.query(ExceptionORM).filter(
            ExceptionORM.sector_id == sector_id,
            ExceptionORM.employee_id == employee_id,
            ExceptionORM.exception_date == exception_date,
            ExceptionORM.exception_type == exception_type,
        ).delete()
        self.session.commit()

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
    

    def load_sunday_rotation(self):
        # Read from DB
        rotations = self.session.query(SundayRotationORM).all()
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

    def load_weekday_template_data(self):
         # This logic requires more thought on how to persist "template". 
         # For now, let's keep CSV fallback or implement CycleTemplateORM loading
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

    def save_sunday_rotation(self, df_rot):
        # Clear existing? Or Upsert? For MVP, clear and insert
        self.session.query(SundayRotationORM).delete()
        for _, row in df_rot.iterrows():
            # Convert to Python date objects (SQLite requirement)
            s_date = pd.to_datetime(row['sunday_date']).date()
            f_date = pd.to_datetime(row['folga_date']).date() if pd.notna(row['folga_date']) else None
            
            self.session.add(SundayRotationORM(
                scale_index=int(row['scale_index']),
                employee_id=row['employee_id'],
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
        # Clear TEMPLATE_BASE records
        self.session.query(CycleTemplateORM).filter(CycleTemplateORM.source == "TEMPLATE_BASE").delete()
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
                source="TEMPLATE_BASE"
            ))
        self.session.commit()
