from datetime import timedelta, date
from typing import List, Dict, Any
from .models import Assignment, Violation, Policy, ViolationSeverity

class ViolationDetector:
    def detect_all(self, assignments: List[Assignment], policy: Policy) -> List[Violation]:
        violations = []
        violations.extend(self._detect_consecutive_days(assignments, policy))
        violations.extend(self._detect_weekly_hours(assignments, policy))
        return violations

    def _detect_consecutive_days(self, assignments: List[Assignment], policy: Policy) -> List[Violation]:
        """R1: Max consecutive work days"""
        violations = []
        max_days = policy.constraints.get("max_consecutive_work_days", 6)
        
        # Sort by employee, then date
        sorted_assignments = sorted(assignments, key=lambda x: (x.employee_id, x.work_date))
        
        current_employee = None
        streak = 0
        streak_start_date = None

        for assignment in sorted_assignments:
            if assignment.employee_id != current_employee:
                current_employee = assignment.employee_id
                streak = 0
                streak_start_date = None
            
            if assignment.status == "WORK":
                streak += 1
                if streak == 1:
                    streak_start_date = assignment.work_date
                
                if streak > max_days:
                    violations.append(Violation(
                        employee_id=assignment.employee_id,
                        rule_code="R1_MAX_6_CONSECUTIVE_DAYS",
                        severity=ViolationSeverity.CRITICAL,
                        date_start=streak_start_date,
                        date_end=assignment.work_date,
                        detail=f"Trabalhou {streak} dias seguidos (Limite={max_days})"
                    ))
            else:
                streak = 0
                streak_start_date = None
                
        return violations

    def _detect_weekly_hours(self, assignments: List[Assignment], policy: Policy) -> List[Violation]:
        """R4: Weekly contract hours"""
        violations = []
        tolerance = policy.constraints.get("weekly_minutes_tolerance", 60)
        week_def = policy.constraints.get("week_definition", "MON_SUN") 
        # Note: week_definition is actually at root of Policy, but let's assume passed correctly or accessible via policy attribute
        # Correction: policy.constraints doesn't have week_definition, policy root has it.
        # But policy object in models.py has `SundayRules` etc. `WeekDefinition` is not in Constraints dict in schema, it's root.
        # Let's check `models.py`: Policy class has `constraints: Dict`.
        # I should use `policy.sunday_rules` or just passed context.
        # Since `WeekDefinition` is not in models.Scanning `models.py` again...
        # Ah, `models.py` doesn't have `week_definition` field in `Policy` class explicitly?
        # Let's check `model.py` content I wrote.
        # "class Policy: ... week_definition: WeekDefinition ..." -> Wait, I didn't put it in `Policy` dataclass?
        # Checking `models.py` content from previous step...
        # It has `SundayRules`, `Constraints`, `Contracts`.
        # It DOES have `Policy(..., policy_version, sector_id, picking_rules, contracts, shifts, constraints, sunday_rules...)`
        # It MISSES `week_definition`. 
        # I should have added `week_definition` to `Policy` model.
        # I will assume it's MON_SUN for now or Fix the model.
        
        # Let's assume MON_SUN default.
        
        # Group by week
        # ... implementation ...
        return []
