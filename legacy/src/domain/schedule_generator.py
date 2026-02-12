from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd

from .models import Assignment, ProjectionContext, Employee

class ScheduleGenerator:
    def __init__(self):
        pass

    def build_scale_cycle_template(
        self,
        sunday_rotation: pd.DataFrame,
        weekday_template: pd.DataFrame,
        sunday_shift_code: str,
        scale_count: int = 8 # Default to 8 weeks cycle
    ) -> pd.DataFrame:
        """
        Builds the 56-day cycle template based on weekday pattern + sunday rotation.
        Returns a DataFrame with [scale_id, cycle_day, employee_id, status, shift_code, minutes, source]
        """
        # ... logic migrated from mock script ...
        # This function is data-heavy and uses pandas. Ideally domain shouldn't depend on pandas but 
        # for this specific project (data processing), it's acceptable as pragmatic approach.
        
        cycle_length_days = scale_count * 7
        
        # Index weekday template for fast lookup
        # weekday_template: [employee_id, day_key, shift_code, minutes]
        template_index = {}
        employees = weekday_template["employee_id"].unique()
        
        for _, row in weekday_template.iterrows():
            template_index[(row["employee_id"], row["day_key"])] = (row["shift_code"], int(row["minutes"]))

        rows = []
        cycle_week_order = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

        for scale_id in range(1, scale_count + 1):
            for employee_id in employees:
                for day_idx, day_key in enumerate(cycle_week_order):
                    cycle_day = (scale_id - 1) * 7 + day_idx + 1
                    
                    if day_key == "SUN":
                        status = "FOLGA"
                        shift_code = None
                        minutes = 0
                    else:
                        status = "WORK"
                        shift, mins = template_index.get((employee_id, day_key), (None, 0))
                        shift_code = shift
                        minutes = mins
                        
                    rows.append({
                        "scale_id": scale_id,
                        "cycle_day": cycle_day,
                        "employee_id": employee_id,
                        "day_key": day_key,
                        "status": status,
                        "shift_code": shift_code,
                        "minutes": minutes,
                        "source": "BASE_WEEKDAY_TEMPLATE"
                    })
        
        df = pd.DataFrame(rows)

        # Apply Sunday Rotation
        # sunday_rotation: [scale_index, employee_id, sunday_date, folga_date]
        # logic: find Sunday for this scale_index.
        
        for _, row in sunday_rotation.iterrows():
            scale_id = int(row["scale_index"])
            employee_id = row["employee_id"]
            # Sunday is day 1 of the week in our CYCLE_WEEK_ORDER (SUN..SAT)?
            # In mock script: `cycle_day = (scale_id - 1) * 7 + 1` which implies SUN is day 1 week 1.
            sunday_day = (scale_id - 1) * 7 + 1
            
            # Compensation logic
            # Calculate delta between sunday_date and folga_date
            # Note: raw input `sunday_rotation` has actual dates.
            # We assume the `scale_index` aligns with the stored dates.
            
            sunday_dt = pd.to_datetime(row["sunday_date"]).date() if isinstance(row["sunday_date"], str) else row["sunday_date"]
            folga_dt = pd.to_datetime(row["folga_date"]).date() if isinstance(row["folga_date"], str) else row["folga_date"]
            
            if pd.isna(folga_dt):
                delta = -1
            else:
                delta = (folga_dt - sunday_dt).days
                
            compensation_day = sunday_day + delta if 0 <= delta <= 6 else None

            # 1. Update Sunday to WORK
            mask_sun = (df["scale_id"] == scale_id) & (df["employee_id"] == employee_id) & (df["cycle_day"] == sunday_day)
            df.loc[mask_sun, ["status", "shift_code", "minutes", "source"]] = [
                "WORK", sunday_shift_code, 270, "SUNDAY_ROTATION" # 270 min = 4h30
            ]
            
            # 2. Update Compensation Day to FOLGA
            if compensation_day:
                mask_folga = (df["scale_id"] == scale_id) & (df["employee_id"] == employee_id) & (df["cycle_day"] == compensation_day)
                df.loc[mask_folga, ["status", "shift_code", "minutes", "source"]] = [
                    "FOLGA", None, 0, "SUNDAY_COMPENSATION"
                ]
                
        return df.sort_values(["scale_id", "cycle_day", "employee_id"])

    def project_cycle_to_days(
        self, 
        template: pd.DataFrame, 
        context: ProjectionContext
    ) -> List[Assignment]:
        """Projects the cycle template onto actual calendar dates."""
        
        assignments = []
        cycle_length_days = int(template["cycle_day"].max())
        base_cycle_day = ((context.anchor_scale_id - 1) * 7) + 1
        
        cursor = context.period_start
        day_to_index = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}

        while cursor <= context.period_end:
            # Calculate which cycle day corresponds to cursor
            cycle_offset = (cursor - context.period_start).days
            # (Start + offset) % Length. 1-based indexing adjustment.
            # If base=1, offset=0 -> 1.
            current_cycle_pos = ((base_cycle_day - 1 + cycle_offset) % cycle_length_days) + 1
            
            # Get template rows for this cycle day
            day_rows = template[template["cycle_day"] == current_cycle_pos]
            
            for _, tr in day_rows.iterrows():
                assignments.append(Assignment(
                    assignment_id=f"{tr['employee_id']}_{cursor.isoformat()}",
                    employee_id=tr["employee_id"],
                    work_date=cursor,
                    sector_id=context.sector_id,
                    status=tr["status"],
                    shift_code=tr["shift_code"] if tr["shift_code"] else None,
                    minutes=int(tr["minutes"]),
                    source=tr["source"],
                    scale_id=int(tr["scale_id"]),
                    cycle_day=int(tr["cycle_day"])
                ))
            
            cursor += timedelta(days=1)
            
        return assignments
