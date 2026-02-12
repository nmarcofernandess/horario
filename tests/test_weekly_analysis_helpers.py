"""Regressão E3/E4: comparativo semanal e dependências externas."""
from datetime import date

import pandas as pd

from apps.backend.routes.scale import _build_weekly_summary_rows, _collect_external_dependencies


def test_weekly_summary_supports_both_week_windows():
    assignments = pd.DataFrame(
        [
            {"work_date": date(2026, 2, 8), "employee_id": "ALICE", "minutes": 270},  # domingo
            {"work_date": date(2026, 2, 9), "employee_id": "ALICE", "minutes": 480},  # segunda
        ]
    )
    contracts = {"ALICE": {"contract_code": "H30_CAIXA", "weekly_minutes": 1800}}
    names = {"ALICE": "Alice"}

    mon_sun = _build_weekly_summary_rows(assignments, contracts, names, tolerance=30, week_definition="MON_SUN")
    sun_sat = _build_weekly_summary_rows(assignments, contracts, names, tolerance=30, week_definition="SUN_SAT")

    assert mon_sun and sun_sat
    assert mon_sun[0].window == "MON_SUN"
    assert sun_sat[0].window == "SUN_SAT"
    # A semana de referência muda entre os cortes.
    assert mon_sun[0].week_start != sun_sat[0].week_start


def test_collect_external_dependencies_flags_unknown_marker_and_placeholder():
    policy_data = {
        "constraints": {"marker_semantics": {"5": "UNKNOWN", "6": "DEFINED"}},
        "jurisdiction": {"collective_agreement_id": "CCT_PLACEHOLDER"},
        "legal_references": [],
    }
    open_items = _collect_external_dependencies(policy_data)
    assert any("marcadores 5" in item for item in open_items)
    assert any("placeholder" in item.lower() for item in open_items)
    assert any("R3" in item for item in open_items)
