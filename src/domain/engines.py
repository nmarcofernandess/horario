
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.domain.models import Shift, ProjectionContext, Violation, ViolationSeverity

@dataclass
class CycleGenerator:
    """
    Core Domain Service responsible for converting raw rules (Mosaic + Rotation) 
    into a concrete projected schedule (DayAssignments).
    """

    def parse_hms_to_minutes(self, value: str) -> int:
        if not isinstance(value, str): return 0
        parts = value.strip().split(":")
        if len(parts) < 2: return 0
        h, m = parts[0], parts[1]
        return int(h) * 60 + int(m)

    def build_weekday_template(self, mosaic_df: pd.DataFrame, shifts: Dict[str, Shift]) -> pd.DataFrame:
        """
        Converts the standard mosaic (Employee x Day) into a template DataFrame.
        """
        rows = []
        if mosaic_df.empty: return pd.DataFrame()
        
        for _, row in mosaic_df.iterrows():
            shift_code = str(row.get('shift_code', ''))
            minutes = 0
            if shift_code in shifts:
                minutes = shifts[shift_code].minutes
            elif 'minutes' in row: 
                 minutes = int(row['minutes'])
            
            day_val = row.get('day_name') or row.get('day_key', '')
            rows.append({
                "employee_id": row['employee_id'],
                "day_key": self._normalize_day(day_val), # SEG->MON
                "shift_code": shift_code,
                "minutes": minutes
            })
            
        return pd.DataFrame(rows)

    def _normalize_day(self, day_name: str) -> str:
        canonical = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}
        upper = str(day_name or "").upper().strip()
        if upper in canonical:
            return upper
        map_pt = {"SEG": "MON", "TER": "TUE", "QUA": "WED", "QUI": "THU", "SEX": "FRI", "SAB": "SAT", "DOM": "SUN"}
        return map_pt.get(upper, "UNK")

    def build_scale_cycle(self, 
                          sunday_rotation_df: pd.DataFrame, 
                          weekday_template: pd.DataFrame, 
                          sunday_shift_code: str = "H_DOM",
                          sunday_minutes: int = 300) -> pd.DataFrame:
        """
        Combines Weekday Template + Sunday Rotation to create the Full Cycle Definition.
        """
        if sunday_rotation_df.empty:
            return pd.DataFrame()

        scale_count = int(sunday_rotation_df['scale_index'].max()) if 'scale_index' in sunday_rotation_df.columns else 1
        
        template_map = {}
        for _, row in weekday_template.iterrows():
            template_map[(row['employee_id'], row['day_key'])] = (row['shift_code'], row['minutes'])

        employees = weekday_template['employee_id'].unique()
        cycle_week_order = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        
        rows = []
        
        for scale_id in range(1, scale_count + 1):
            for emp_id in employees:
                for day_idx, day_key in enumerate(cycle_week_order):
                    cycle_day = (scale_id - 1) * 7 + day_idx + 1
                    
                    if day_key == "SUN":
                        status = "FOLGA"
                        shift = ""
                        mins = 0
                    else:
                        res = template_map.get((emp_id, day_key))
                        if res:
                            status = "WORK"
                            shift, mins = res
                        else:
                            status = "FOLGA"
                            shift, mins = "", 0
                    
                    rows.append({
                        "scale_id": scale_id,
                        "cycle_day": cycle_day,
                        "employee_id": emp_id,
                        "day_key": day_key,
                        "status": status,
                        "shift_code": shift,
                        "minutes": mins,
                        "source": "TEMPLATE_BASE"
                    })

        df = pd.DataFrame(rows)
        
        for _, rot in sunday_rotation_df.iterrows():
            if 'scale_index' not in rot: continue
            
            scale = int(rot['scale_index'])
            emp = rot['employee_id']
            sunday_cycle_day = (scale - 1) * 7 + 1 
            
            mask_sun = (df['scale_id'] == scale) & (df['employee_id'] == emp) & (df['cycle_day'] == sunday_cycle_day)
            df.loc[mask_sun, ['status', 'shift_code', 'minutes', 'source']] = \
                ['WORK', sunday_shift_code, sunday_minutes, 'ROTATION_SUNDAY']
            
            if 'folga_date' in rot and pd.notna(rot['folga_date']):
                f_date = pd.to_datetime(rot['folga_date'])
                s_date = pd.to_datetime(rot['sunday_date'])
                delta = (f_date - s_date).days
                
                if 0 <= delta <= 6:
                    comp_cycle_day = sunday_cycle_day + delta
                    mask_folga = (df['scale_id'] == scale) & (df['employee_id'] == emp) & (df['cycle_day'] == comp_cycle_day)
                    df.loc[mask_folga, ['status', 'shift_code', 'minutes', 'source']] = \
                        ['FOLGA', '', 0, 'ROTATION_COMPENSATION']

        return df

    def project_cycle_to_period(self, 
                                cycle_template: pd.DataFrame, 
                                context: ProjectionContext) -> pd.DataFrame:
        """
        Projects the abstract cycle onto a concrete calendar period.
        anchor_date: domingo de referência do ciclo. Se None, assume period_start = dia 1.
        """
        if cycle_template.empty: return pd.DataFrame()

        cycle_len = int(cycle_template['cycle_day'].max())
        anchor = context.anchor_date if context.anchor_date else context.period_start
        rows = []
        cursor = context.period_start
        
        while cursor <= context.period_end:
            offset = (cursor - anchor).days
            cycle_day = (offset % cycle_len) + 1
            day_defs = cycle_template[cycle_template['cycle_day'] == cycle_day]
            
            for _, d in day_defs.iterrows():
                rows.append({
                    "work_date": cursor,
                    "employee_id": d['employee_id'],
                    "status": d['status'],
                    "shift_code": d['shift_code'],
                    "minutes": d['minutes'],
                    "source_rule": d['source']
                })
            
            cursor += timedelta(days=1)
            
        return pd.DataFrame(rows)

@dataclass
class PolicyEngine:
    """
    Domain Service responsible for validating the generated schedule against compliance rules.
    """

    def validate_consecutive_days(self, day_assignments: pd.DataFrame, max_days: int = 6) -> List[Violation]:
        violations = []
        if day_assignments.empty: return violations

        df = day_assignments.sort_values(['employee_id', 'work_date'])
        
        for employee_id, group in df.groupby('employee_id'):
            streak = 0
            streak_start = None
            
            for _, row in group.iterrows():
                if row['status'] == 'WORK':
                    streak += 1
                    if streak == 1:
                        streak_start = row['work_date']
                    
                    if streak > max_days:
                        violations.append(Violation(
                            employee_id=employee_id,
                            rule_code="R1_MAX_CONSECUTIVE",
                            severity=ViolationSeverity.CRITICAL,
                            date_start=streak_start,
                            date_end=row['work_date'],
                            detail=f"Trabalhou {streak} dias seguidos (Max: {max_days})",
                            evidence={"streak": streak}
                        ))
                else:
                    streak = 0
                    streak_start = None
        
        return violations

    def validate_weekly_hours(self, 
                              day_assignments: pd.DataFrame, 
                              contract_targets: Dict[str, int], 
                              tolerance: int = 120) -> List[Violation]:
        violations = []
        if day_assignments.empty: return violations

        df = day_assignments.copy()
        df['work_date'] = pd.to_datetime(df['work_date'])
        df['week_start'] = df['work_date'] - pd.to_timedelta(df['work_date'].dt.weekday, unit='D')
        
        grouped = df.groupby(['employee_id', 'week_start'])['minutes'].sum().reset_index()
        
        for _, row in grouped.iterrows():
            emp_id = row['employee_id']
            actual = row['minutes']
            target = contract_targets.get(emp_id, 2640) # Default 44h
            
            delta = actual - target
            
            if abs(delta) > tolerance:
                severity = ViolationSeverity.HIGH if abs(delta) > 600 else ViolationSeverity.MEDIUM
                violations.append(Violation(
                    employee_id=emp_id,
                    rule_code="R4_WEEKLY_TARGET",
                    severity=severity,
                    date_start=row['week_start'].date(),
                    date_end=(row['week_start'] + timedelta(days=6)).date(),
                    detail=f"Desvio de {delta} min (Meta: {target}, Real: {actual})",
                    evidence={"delta": delta, "actual": actual, "target": target}
                ))
                
        return violations
