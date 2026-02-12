"""Rotas de turnos"""
from fastapi import APIRouter, Depends
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.schemas import ShiftResponse
from api.deps import get_repo

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
