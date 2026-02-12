import json
from pathlib import Path
from typing import Dict, Any, List
from .models import (
    Policy, Contract, Shift, ShiftDayScope,
    PickingRules, PickingStrategy, WeekDefinition
)

class PolicyLoader:
    def __init__(self, schemas_path: Path):
        self.schemas_path = schemas_path

    def load_policy(self, policy_path: Path) -> Policy:
        """Loads and parses the policy JSON into a Domain Entity."""
        data = json.loads(policy_path.read_text(encoding="utf-8"))
        
        # 1. Parse Picking Rules
        picking_data = data.get("picking_rules", {})
        picking_rules = PickingRules(
            strategy=PickingStrategy(picking_data.get("strategy", "WEIGHTED_SCORE")),
            criteria=picking_data.get("criteria", [])
        )

        # 2. Parse Contracts
        contracts = {}
        for c in data.get("contracts", []):
            contracts[c["contract_code"]] = Contract(
                contract_code=c["contract_code"],
                weekly_minutes=int(c["weekly_minutes"]),
                sector_id=data.get("sector_id", "UNKNOWN"),
                allowed_shifts=c.get("allowed_weekday_shift_codes", []),
                sunday_mode=c.get("sunday_mode", "WORK_WITH_COMPENSATION")
            )

        # 3. Parse Shifts
        shifts = {}
        # Weekday shifts
        for s in data.get("shift_catalog", {}).get("weekday_shifts", []):
            shifts[s["code"]] = Shift(
                code=s["code"],
                minutes=int(s["minutes"]),
                day_scope=ShiftDayScope.WEEKDAY,
                sector_id=data.get("sector_id", "UNKNOWN"),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                tags=s.get("tags", [])
            )
        # Sunday shift
        sunday_s = data.get("shift_catalog", {}).get("sunday_shift")
        if sunday_s:
            shifts[sunday_s["code"]] = Shift(
                code=sunday_s["code"],
                minutes=int(sunday_s["minutes"]),
                day_scope=ShiftDayScope.SUNDAY,
                sector_id=data.get("sector_id", "UNKNOWN"),
                start_time=sunday_s.get("start_time"),
                end_time=sunday_s.get("end_time"),
                tags=sunday_s.get("tags", [])
            )

        return Policy(
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            sector_id=data.get("sector_id", "UNKNOWN"),
            week_definition=WeekDefinition(data.get("week_definition", "MON_SUN")),
            picking_rules=picking_rules,
            contracts=contracts,
            shifts=shifts,
            constraints=data.get("constraints", {}),
            sunday_rules=data.get("sunday_policy", {}),
            preference_rules=data.get("employee_preference_policy", {})
        )
