"""Regressão: modo estrito exige ACK para risco legal e bloqueia LOGIC_HARD."""
from fastapi.testclient import TestClient

from apps.backend.main import app
from apps.backend.schemas import PreflightIssue, PreflightResponse
import apps.backend.routes.scale as scale_routes


client = TestClient(app)


class _FakeOrchestrator:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        return {
            "status": "SUCCESS",
            "assignments_count": 0,
            "violations_count": 0,
            "preferences_processed": 0,
            "exceptions_applied": 0,
            "preview_assignments": [],
            "preview_violations": [],
        }


def test_strict_without_ack_returns_409(monkeypatch):
    monkeypatch.setattr(scale_routes, "ValidationOrchestrator", _FakeOrchestrator)
    monkeypatch.setattr(
        scale_routes,
        "_build_preflight",
        lambda req, repo: PreflightResponse(
            mode="ESTRITO",
            blockers=[],
            critical_warnings=[
                PreflightIssue(
                    code="LEGAL_SOFT_1",
                    message="Pendência jurídica de domingo/feriado.",
                    recommended_action="Registrar justificativa operacional.",
                )
            ],
            can_proceed=True,
            ack_required=True,
        ),
    )
    res = client.post(
        "/scale/simulate",
        json={"period_start": "2026-02-10", "period_end": "2026-02-16", "sector_id": "CAIXA"},
    )
    assert res.status_code == 409
    assert "Modo estrito exige confirmação" in res.json()["detail"]["message"]


def test_strict_with_ack_returns_200(monkeypatch):
    monkeypatch.setattr(scale_routes, "ValidationOrchestrator", _FakeOrchestrator)
    monkeypatch.setattr(
        scale_routes,
        "_build_preflight",
        lambda req, repo: PreflightResponse(
            mode="ESTRITO",
            blockers=[],
            critical_warnings=[
                PreflightIssue(
                    code="LEGAL_SOFT_1",
                    message="Pendência jurídica de domingo/feriado.",
                    recommended_action="Registrar justificativa operacional.",
                )
            ],
            can_proceed=True,
            ack_required=True,
        ),
    )
    res = client.post(
        "/scale/simulate",
        json={
            "period_start": "2026-02-10",
            "period_end": "2026-02-16",
            "sector_id": "CAIXA",
            "risk_ack": {"actor_role": "OPERADOR", "reason": "Operação precisa continuar no fechamento."},
        },
    )
    assert res.status_code == 200


def test_logic_hard_blocks_even_in_normal(monkeypatch):
    monkeypatch.setattr(scale_routes, "ValidationOrchestrator", _FakeOrchestrator)
    monkeypatch.setattr(
        scale_routes,
        "_build_preflight",
        lambda req, repo: PreflightResponse(
            mode="NORMAL",
            blockers=[
                PreflightIssue(
                    code="LOGIC_EMPTY_TEMPLATE",
                    message="Mosaico semanal vazio.",
                    recommended_action="Preencher mosaico.",
                )
            ],
            critical_warnings=[],
            can_proceed=False,
            ack_required=False,
        ),
    )
    res = client.post(
        "/scale/generate",
        json={"period_start": "2026-02-10", "period_end": "2026-02-16", "sector_id": "CAIXA"},
    )
    assert res.status_code == 422
    assert "LOGIC_HARD" in res.json()["detail"]["message"]
