"""Regressão E4: configuração de governança via API."""
import json

from fastapi.testclient import TestClient

from apps.backend.main import app
import apps.backend.routes.config as config_routes


client = TestClient(app)


def test_governance_get_and_patch_roundtrip(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "constraints": {
                    "accepted_dom_folgas_markers": ["5", "6"],
                    "marker_semantics": {"5": "UNKNOWN", "6": "UNKNOWN"},
                },
                "jurisdiction": {
                    "collective_agreement_id": "CCT_PLACEHOLDER",
                    "sunday_holiday_legal_validated": False,
                },
                "legal_references": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_routes, "POLICY_PATH", policy_path)

    res_get = client.get("/config/governance")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["marker_semantics"]["5"] == "UNKNOWN"
    assert data_get["pending_items"]
    assert data_get["release_checklist"]

    res_patch = client.patch(
        "/config/governance",
        json={
            "marker_semantics": {"5": "COMPENSA_48H", "6": "ESCALA_6X1"},
            "collective_agreement_id": "CCT_CAIXA_PR_2026_01",
            "sunday_holiday_legal_validated": True,
            "legal_validation_note": "Parecer jurídico interno validado.",
        },
    )
    assert res_patch.status_code == 200
    data_patch = res_patch.json()
    assert data_patch["marker_semantics"]["5"] == "COMPENSA_48H"
    assert data_patch["marker_semantics"]["6"] == "ESCALA_6X1"
    assert data_patch["collective_agreement_id"] == "CCT_CAIXA_PR_2026_01"
    assert data_patch["sunday_holiday_legal_validated"] is True


def test_governance_apply_defaults_fills_unknown_markers(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "constraints": {
                    "accepted_dom_folgas_markers": ["5", "6"],
                    "marker_semantics": {"5": "UNKNOWN", "6": "UNKNOWN"},
                },
                "jurisdiction": {
                    "collective_agreement_id": "CCT_PLACEHOLDER",
                    "sunday_holiday_legal_validated": False,
                },
                "legal_references": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_routes, "POLICY_PATH", policy_path)

    res_defaults = client.post("/config/governance/apply-defaults")
    assert res_defaults.status_code == 200
    data = res_defaults.json()
    assert data["marker_semantics"]["5"] == "COMPENSA_48H"
    assert data["marker_semantics"]["6"] == "ESCALA_6X1"


def test_runtime_mode_patch_requires_admin(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "constraints": {
                    "accepted_dom_folgas_markers": ["5", "6"],
                    "marker_semantics": {"5": "UNKNOWN", "6": "UNKNOWN"},
                },
                "jurisdiction": {
                    "collective_agreement_id": "",
                    "sunday_holiday_legal_validated": False,
                },
                "runtime_mode": {"mode": "NORMAL"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config_routes, "POLICY_PATH", policy_path)

    forbidden = client.patch("/config/runtime-mode", json={"mode": "ESTRITO", "actor_role": "OPERADOR"})
    assert forbidden.status_code == 403

    ok = client.patch("/config/runtime-mode", json={"mode": "ESTRITO", "actor_role": "ADMIN"})
    assert ok.status_code == 200
    assert ok.json()["mode"] == "ESTRITO"


def test_governance_audit_endpoint_returns_list():
    res = client.get("/config/governance/audit?limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
