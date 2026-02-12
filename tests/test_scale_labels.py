"""Regressão de labels de violação na API de escala."""
from datetime import date

import pandas as pd

from apps.backend.routes.scale import _violations_to_response


def test_violations_labels_cover_current_and_legacy_codes():
    """Mapeia códigos atuais/legado e normaliza rule_code com espaços."""
    df = pd.DataFrame(
        [
            {
                "employee_id": "ALICE",
                "rule_code": "R4_WEEKLY_TARGET ",
                "severity": "HIGH",
                "date_start": date(2026, 2, 1),
                "date_end": date(2026, 2, 7),
                "detail": "Teste",
            },
            {
                "employee_id": "ALICE",
                "rule_code": "R4_DEMAND_COVERAGE",
                "severity": "MEDIUM",
                "date_start": date(2026, 2, 8),
                "date_end": date(2026, 2, 8),
                "detail": "Teste legado",
            },
            {
                "employee_id": "ALICE",
                "rule_code": "R6_MAX_DAILY_MINUTES",
                "severity": "HIGH",
                "date_start": date(2026, 2, 9),
                "date_end": date(2026, 2, 9),
                "detail": "Teste diário",
            },
        ]
    )

    rows = _violations_to_response(df, {"ALICE": "Alice"})
    assert len(rows) == 3
    assert rows[0].rule_code == "R4_WEEKLY_TARGET"
    assert rows[0].rule_label == "Meta semanal de horas"
    assert rows[1].rule_label == "Cobertura insuficiente"
    assert rows[2].rule_label == "Limite diário de jornada"
