"""Rotas de pedidos (preferências)"""
from fastapi import APIRouter, Depends, HTTPException
from apps.backend.src.domain.models import PreferenceRequest, RequestType, RequestDecision
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import PreferenceCreate, PreferenceDecision, PreferenceResponse
from apps.backend.deps import get_repo

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=list[PreferenceResponse])
def list_preferences(repo: SqlAlchemyRepository = Depends(get_repo)):
    prefs = repo.load_preferences()
    return [
        PreferenceResponse(
            request_id=p.request_id,
            employee_id=p.employee_id,
            request_date=p.request_date,
            request_type=p.request_type.value,
            priority=p.priority,
            target_shift_code=p.target_shift_code,
            note=p.note,
            decision=p.decision.value,
            decision_reason=p.decision_reason,
        )
        for p in prefs
    ]


@router.post("", response_model=PreferenceResponse)
def create_preference(
    data: PreferenceCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    req = PreferenceRequest(
        request_id=data.request_id,
        employee_id=data.employee_id,
        request_date=data.request_date,
        request_type=RequestType(data.request_type),
        priority=data.priority,
        target_shift_code=data.target_shift_code,
        note=data.note or "",
    )
    repo.add_preference(req)
    return PreferenceResponse(
        request_id=req.request_id,
        employee_id=req.employee_id,
        request_date=req.request_date,
        request_type=req.request_type.value,
        priority=req.priority,
        target_shift_code=req.target_shift_code,
        note=req.note,
        decision="PENDING",
        decision_reason=None,
    )


@router.patch("/{request_id}/decision")
def update_preference_decision(
    request_id: str,
    data: PreferenceDecision,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    prefs = repo.load_preferences()
    pref = next((p for p in prefs if p.request_id == request_id), None)
    if not pref:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    decision = RequestDecision(data.decision)
    reason = data.reason or ""
    repo.update_preference_decision(request_id, decision, reason)
    return {"ok": True, "request_id": request_id, "decision": data.decision}
