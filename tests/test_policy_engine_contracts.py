"""Regressão das regras operacionais de contrato/jornada."""
from datetime import date

import pandas as pd

from apps.backend.src.domain.engines import PolicyEngine


def test_weekly_target_violation_includes_contract_code():
    engine = PolicyEngine()
    df = pd.DataFrame(
        [
            {
                "employee_id": "ALICE",
                "work_date": date(2026, 2, 9),
                "minutes": 1000,
                "status": "WORK",
            },
            {
                "employee_id": "ALICE",
                "work_date": date(2026, 2, 10),
                "minutes": 1000,
                "status": "WORK",
            },
            {
                "employee_id": "ALICE",
                "work_date": date(2026, 2, 11),
                "minutes": 1000,
                "status": "WORK",
            },
        ]
    )
    violations = engine.validate_weekly_hours(
        df,
        {"ALICE": {"contract_code": "H30_CAIXA", "weekly_minutes": 1800}},
        tolerance=30,
    )
    assert violations
    assert "[H30_CAIXA]" in violations[0].detail
    assert violations[0].evidence["contract_code"] == "H30_CAIXA"


def test_daily_minutes_violation_uses_operational_limit():
    engine = PolicyEngine()
    df = pd.DataFrame(
        [
            {
                "employee_id": "ALICE",
                "work_date": date(2026, 2, 9),
                "minutes": 590,
                "status": "WORK",
            }
        ]
    )
    violations = engine.validate_daily_minutes(
        df,
        {"max_daily_minutes_operational": 585, "max_daily_minutes_hard": 600},
    )
    assert len(violations) == 1
    assert violations[0].rule_code == "R6_MAX_DAILY_MINUTES"
    assert violations[0].severity.value == "HIGH"
