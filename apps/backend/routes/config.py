"""Rotas de configuração"""
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.deps import get_repo
from apps.backend.schemas import (
    GovernanceChecklistItem,
    GovernanceConfigResponse,
    GovernanceConfigUpdate,
    RuntimeModeConfig,
    RuntimeModeUpdate,
    GovernanceAuditEvent,
)

router = APIRouter(prefix="/config", tags=["config"])
ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"


def _load_policy_data() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _save_policy_data(data: dict) -> None:
    POLICY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _pending_items_from_policy(data: dict) -> list[str]:
    pending: list[str] = []
    semantics = data.get("constraints", {}).get("marker_semantics", {})
    unresolved = [m for m, v in semantics.items() if str(v).upper() == "UNKNOWN"]
    if unresolved:
        pending.append(f"Semântica dos marcadores {', '.join(unresolved)} está indefinida.")

    cct_id = str(data.get("jurisdiction", {}).get("collective_agreement_id", ""))
    if not cct_id or "PLACEHOLDER" in cct_id.upper():
        pending.append("Identificador da CCT está vazio ou placeholder.")

    legal_ok = bool(data.get("jurisdiction", {}).get("sunday_holiday_legal_validated", False))
    if not legal_ok:
        pending.append("Validação jurídica de domingo/feriado não foi marcada como concluída.")
    return pending


def _get_runtime_mode(data: dict) -> RuntimeModeConfig:
    runtime_data = data.get("runtime_mode", {})
    mode = str(runtime_data.get("mode", "NORMAL")).strip().upper()
    if mode not in {"NORMAL", "ESTRITO"}:
        mode = "NORMAL"
    return RuntimeModeConfig(
        mode=mode,
        updated_at=runtime_data.get("updated_at"),
        updated_by_role=runtime_data.get("updated_by_role"),
        source="policy",
    )


def _save_runtime_mode(data: dict, mode: str, actor_role: str) -> RuntimeModeConfig:
    data["runtime_mode"] = {
        "mode": mode,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "updated_by_role": actor_role,
    }
    _save_policy_data(data)
    return _get_runtime_mode(data)


def _build_release_checklist(data: dict, pending_items: list[str]) -> list[GovernanceChecklistItem]:
    semantics = data.get("constraints", {}).get("marker_semantics", {})
    unresolved = [m for m, v in semantics.items() if str(v).upper() == "UNKNOWN"]
    cct_id = str(data.get("jurisdiction", {}).get("collective_agreement_id", ""))
    legal_ok = bool(data.get("jurisdiction", {}).get("sunday_holiday_legal_validated", False))
    return [
        GovernanceChecklistItem(
            item_id="E4_MARKERS_DEFINED",
            title="Semântica dos marcadores 5/6 definida",
            done=not unresolved,
            detail=None if not unresolved else f"Marcadores indefinidos: {', '.join(unresolved)}",
        ),
        GovernanceChecklistItem(
            item_id="E4_CCT_REGISTERED",
            title="CCT vigente registrada",
            done=bool(cct_id.strip()) and "PLACEHOLDER" not in cct_id.upper(),
            detail=None if (bool(cct_id.strip()) and "PLACEHOLDER" not in cct_id.upper()) else "CCT vazia ou placeholder.",
        ),
        GovernanceChecklistItem(
            item_id="E4_LEGAL_VALIDATED",
            title="Validação jurídica domingo/feriado concluída",
            done=legal_ok,
            detail=None if legal_ok else "Flag jurídica ainda pendente.",
        ),
        GovernanceChecklistItem(
            item_id="E4_NO_PENDING_ITEMS",
            title="Nenhuma pendência externa aberta",
            done=len(pending_items) == 0,
            detail=None if len(pending_items) == 0 else f"{len(pending_items)} pendência(s) aberta(s).",
        ),
    ]


@router.get("")
def get_config(repo: SqlAlchemyRepository = Depends(get_repo)):
    """Retorna configuração básica da aplicação."""
    sectors = repo.load_sectors()
    return {
        "sectors": [{"sector_id": s[0], "name": s[1]} for s in sectors],
        "default_sector_id": "CAIXA",
    }


@router.get("/governance", response_model=GovernanceConfigResponse)
def get_governance_config():
    data = _load_policy_data()
    constraints = data.setdefault("constraints", {})
    jurisdiction = data.setdefault("jurisdiction", {})
    marker_semantics = constraints.get("marker_semantics", {})
    accepted_markers = constraints.get("accepted_dom_folgas_markers", [])
    pending_items = _pending_items_from_policy(data)
    return GovernanceConfigResponse(
        accepted_dom_folgas_markers=[str(m) for m in accepted_markers],
        marker_semantics={str(k): str(v) for k, v in marker_semantics.items()},
        collective_agreement_id=str(jurisdiction.get("collective_agreement_id", "")),
        sunday_holiday_legal_validated=bool(jurisdiction.get("sunday_holiday_legal_validated", False)),
        legal_validation_note=jurisdiction.get("legal_validation_note"),
        pending_items=pending_items,
        release_checklist=_build_release_checklist(data, pending_items),
    )


@router.patch("/governance", response_model=GovernanceConfigResponse)
def update_governance_config(payload: GovernanceConfigUpdate):
    data = _load_policy_data()
    constraints = data.setdefault("constraints", {})
    jurisdiction = data.setdefault("jurisdiction", {})
    accepted_markers = [str(m) for m in constraints.get("accepted_dom_folgas_markers", [])]
    incoming = {str(k): str(v).strip().upper() for k, v in payload.marker_semantics.items()}

    normalized_semantics: dict[str, str] = {}
    for marker in accepted_markers:
        normalized_semantics[marker] = incoming.get(marker, "UNKNOWN")
    # Permite manter chaves extras explicitamente configuradas.
    for key, value in incoming.items():
        if key not in normalized_semantics:
            normalized_semantics[key] = value

    new_cct = payload.collective_agreement_id.strip()
    if payload.sunday_holiday_legal_validated:
        unresolved = [m for m, v in normalized_semantics.items() if str(v).upper() == "UNKNOWN"]
        if unresolved:
            raise HTTPException(
                status_code=422,
                detail=f"Não é possível concluir validação jurídica com marcadores indefinidos: {', '.join(unresolved)}.",
            )
        if not new_cct or "PLACEHOLDER" in new_cct.upper():
            raise HTTPException(
                status_code=422,
                detail="Não é possível concluir validação jurídica com CCT vazia ou placeholder.",
            )

    constraints["marker_semantics"] = normalized_semantics
    jurisdiction["collective_agreement_id"] = new_cct
    jurisdiction["sunday_holiday_legal_validated"] = payload.sunday_holiday_legal_validated
    jurisdiction["legal_validation_note"] = payload.legal_validation_note or ""
    _save_policy_data(data)
    return get_governance_config()


@router.post("/governance/apply-defaults", response_model=GovernanceConfigResponse)
def apply_governance_defaults():
    """
    Aplica defaults recomendados de semântica dos marcadores.
    Não conclui validação jurídica automaticamente.
    """
    data = _load_policy_data()
    constraints = data.setdefault("constraints", {})
    jurisdiction = data.setdefault("jurisdiction", {})
    accepted = [str(m) for m in constraints.get("accepted_dom_folgas_markers", [])]
    semantics = {str(k): str(v).strip().upper() for k, v in constraints.get("marker_semantics", {}).items()}
    recommended = {
        "5": "COMPENSA_48H",
        "6": "ESCALA_6X1",
    }
    for marker in accepted:
        current = semantics.get(marker, "UNKNOWN").upper()
        if current == "UNKNOWN":
            semantics[marker] = recommended.get(marker, f"MARKER_{marker}_DEFINED")
    constraints["marker_semantics"] = semantics

    if "legal_validation_note" not in jurisdiction or not jurisdiction.get("legal_validation_note"):
        jurisdiction["legal_validation_note"] = "Defaults operacionais aplicados; pendente validação jurídica final."

    _save_policy_data(data)
    return get_governance_config()


@router.get("/runtime-mode", response_model=RuntimeModeConfig)
def get_runtime_mode():
    data = _load_policy_data()
    return _get_runtime_mode(data)


@router.patch("/runtime-mode", response_model=RuntimeModeConfig)
def update_runtime_mode(payload: RuntimeModeUpdate):
    actor_role = payload.actor_role.strip().upper()
    if actor_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Somente ADMIN pode alterar o modo de execução.")
    mode = payload.mode.strip().upper()
    if mode not in {"NORMAL", "ESTRITO"}:
        raise HTTPException(status_code=422, detail="Modo inválido. Use NORMAL ou ESTRITO.")
    data = _load_policy_data()
    return _save_runtime_mode(data, mode=mode, actor_role=actor_role)


@router.get("/governance/audit", response_model=list[GovernanceAuditEvent])
def list_governance_audit_events(
    limit: int = 50,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    safe_limit = max(1, min(limit, 200))
    return [GovernanceAuditEvent(**row) for row in repo.list_governance_audit_events(limit=safe_limit)]
