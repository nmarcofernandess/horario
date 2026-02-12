from typing import List, Dict, Any, Tuple
from datetime import date
from .models import (
    PreferenceRequest, Employee, Policy, PickingStrategy, 
    RequestDecision, Assignment
)

class PreferenceEngine:
    def __init__(self):
        pass

    def sort_requests(self, requests: List[PreferenceRequest], employees: Dict[str, Employee], policy: Policy) -> List[PreferenceRequest]:
        """Sorts requests based on the picking strategy defined in the policy."""
        strategy = policy.picking_rules.strategy

        if strategy == PickingStrategy.MANUAL_RANK:
            return sorted(
                requests,
                key=lambda req: (
                    employees.get(req.employee_id).rank if employees.get(req.employee_id) else 999,
                    req.request_date,
                    0 if req.priority == "HIGH" else 1 if req.priority == "MEDIUM" else 2
                )
            )
        elif strategy == PickingStrategy.MANUAL_ONLY:
            # No sorting, just raw list or specific criteria
            return requests 
        else:
            # Fallback to FIFO by date
            return sorted(requests, key=lambda r: r.request_date)

    def process_requests(
        self, 
        requests: List[PreferenceRequest], 
        assignments: List[Assignment], 
        employees: Dict[str, Employee], 
        policy: Policy
    ) -> Tuple[List[Assignment], List[PreferenceRequest]]:
        """
        Processes a list of requests, applying them to assignments if they don't break strict rules.
        Returns (updated_assignments, detailed_requests_with_decisions).
        """
        sorted_requests = self.sort_requests(requests, employees, policy)
        
        # Fast lookup for assignments
        assignment_map = { (a.employee_id, a.work_date): a for a in assignments }
        processed_requests = []

        # Limits from policy
        max_approved = policy.preference_rules.get("max_approved_requests_per_employee_per_cycle", 2)
        approved_count = { eid: 0 for eid in employees }

        for req in sorted_requests:
            emp_id = req.employee_id
            
            # 1. Validation: Employee exists
            if emp_id not in employees:
                req.decision = RequestDecision.REJECTED
                req.decision_reason = "EMPLOYEE_NOT_FOUND"
                processed_requests.append(req)
                continue

            # 2. Validation: Limit reached
            if approved_count[emp_id] >= max_approved:
                req.decision = RequestDecision.REJECTED
                req.decision_reason = "LIMIT_REACHED"
                processed_requests.append(req)
                continue

            # 3. Simulate Application on Assignment
            key = (emp_id, req.request_date)
            current_assignment = assignment_map.get(key)
            
            if not current_assignment:
                 # Request for a date outside processed cycle or missing
                req.decision = RequestDecision.REJECTED
                req.decision_reason = "DATE_NOT_IN_CYCLE"
                processed_requests.append(req)
                continue

            # Business Logic for Types
            # Simplification: Only implementing FOLGA_ON_DATE for now as MVP
            if req.request_type == "FOLGA_ON_DATE":
                if current_assignment.status != "WORK":
                    req.decision = RequestDecision.REJECTED
                    req.decision_reason = "ALREADY_OFF"
                else:
                    # APPLY CHANGE
                    # We need to treat assignments as immutable-ish, so replace in map
                    new_assignment = Assignment(
                        assignment_id=current_assignment.assignment_id,
                        employee_id=emp_id,
                        work_date=req.request_date,
                        sector_id=current_assignment.sector_id,
                        status="FOLGA",
                        shift_code=None,
                        minutes=0,
                        source="PREFERENCE_APPROVED",
                        scale_id=current_assignment.scale_id,
                        cycle_day=current_assignment.cycle_day
                    )
                    assignment_map[key] = new_assignment
                    
                    req.decision = RequestDecision.APPROVED
                    req.decision_reason = "RANK_PRIORITY"
                    approved_count[emp_id] += 1
            
            # Add other types (SHIFT_CHANGE, AVOID_SUNDAY) here...
            
            processed_requests.append(req)

        # Reconstruct list
        updated_assignments = list(assignment_map.values())
        return updated_assignments, processed_requests
