"""Rotas de turnos."""
from fastapi import APIRouter, Depends, HTTPException
from apps.backend.src.domain.models import ShiftDayScope
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import ShiftResponse, ShiftCreate, ShiftUpdate
from apps.backend.deps import get_repo

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.get("", response_model=list[ShiftResponse])
def list_shifts(
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    shifts = repo.load_shifts(sector_id)
    return [
        ShiftResponse(
            shift_code=s.code,
            sector_id=s.sector_id,
            minutes=s.minutes,
            day_scope=s.day_scope.value,
        )
        for s in shifts.values()
    ]


@router.post("", response_model=ShiftResponse)
def create_shift(
    data: ShiftCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    try:
        day_scope = ShiftDayScope(data.day_scope.upper()).value
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"day_scope inválido: {data.day_scope}") from exc
    try:
        shift = repo.upsert_shift(
            shift_code=data.shift_code,
            sector_id=data.sector_id,
            minutes=data.minutes,
            day_scope=day_scope,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ShiftResponse(
        shift_code=shift.code,
        sector_id=shift.sector_id,
        minutes=shift.minutes,
        day_scope=shift.day_scope.value,
    )


@router.patch("/{shift_code}", response_model=ShiftResponse)
def update_shift(
    shift_code: str,
    data: ShiftUpdate,
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    current = repo.load_shifts(sector_id)
    if shift_code not in current:
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    try:
        day_scope = ShiftDayScope(data.day_scope.upper()).value
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"day_scope inválido: {data.day_scope}") from exc
    shift = repo.upsert_shift(
        shift_code=shift_code,
        sector_id=sector_id,
        minutes=data.minutes,
        day_scope=day_scope,
    )
    return ShiftResponse(
        shift_code=shift.code,
        sector_id=shift.sector_id,
        minutes=shift.minutes,
        day_scope=shift.day_scope.value,
    )


@router.delete("/{shift_code}")
def delete_shift(
    shift_code: str,
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    ok = repo.remove_shift(shift_code=shift_code, sector_id=sector_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    return {"ok": True, "shift_code": shift_code}
