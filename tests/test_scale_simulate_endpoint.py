"""Regressão do endpoint /scale/simulate."""
from fastapi.testclient import TestClient

from apps.backend.main import app
import apps.backend.routes.scale as scale_routes


client = TestClient(app)


def test_simulate_endpoint_uses_preview_mode(monkeypatch):
    """O endpoint deve executar sem persistir resultado oficial."""
    captured = {}

    def fake_run(self, context, policy_path, persist_results=True, include_preview=False):
        captured["persist_results"] = persist_results
        captured["include_preview"] = include_preview
        return {
            "status": "SUCCESS",
            "assignments_count": 1,
            "violations_count": 1,
            "preferences_processed": 0,
            "exceptions_applied": 0,
            "preview_assignments": [
                {
                    "work_date": "2026-02-10",
                    "employee_id": "ALICE",
                    "status": "WORK",
                    "shift_code": "CAI1",
                    "minutes": 480,
                    "source_rule": "TEST",
                }
            ],
            "preview_violations": [
                {
                    "employee_id": "ALICE",
                    "rule_code": "R5_DEMAND_COVERAGE",
                    "severity": "MEDIUM",
                    "date_start": "2026-02-10",
                    "date_end": "2026-02-10",
                    "detail": "Teste",
                }
            ],
        }

    monkeypatch.setattr(scale_routes.ValidationOrchestrator, "run", fake_run)

    res = client.post(
        "/scale/simulate",
        json={"period_start": "2026-02-10", "period_end": "2026-02-16", "sector_id": "CAIXA"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["assignments_count"] == 1
    assert data["violations_count"] == 1
    assert len(data["assignments"]) == 1
    assert len(data["violations"]) == 1
    assert captured["persist_results"] is False
    assert captured["include_preview"] is True
