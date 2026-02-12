"""Rotas de demand profile (slots de demanda por faixa horária)"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.domain.models import DemandSlot
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.schemas import DemandSlotCreate, DemandSlotResponse
from api.deps import get_repo

router = APIRouter(prefix="/demand-profile", tags=["demand-profile"])


@router.get("", response_model=list[DemandSlotResponse])
def list_demand_slots(
    sector_id: str = "CAIXA",
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    slots = repo.load_demand_profile(sector_id=sector_id, period_start=period_start, period_end=period_end)
    return [
        DemandSlotResponse(
            sector_id=s.sector_id,
            work_date=s.work_date,
            slot_start=s.slot_start,
            min_required=s.min_required,
        )
        for s in slots
    ]


@router.post("", response_model=DemandSlotResponse)
def create_demand_slot(
    data: DemandSlotCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    slot = DemandSlot(
        sector_id=data.sector_id,
        work_date=data.work_date,
        slot_start=data.slot_start,
        min_required=data.min_required,
    )
    repo.add_demand_slot(slot)
    return DemandSlotResponse(
        sector_id=slot.sector_id,
        work_date=slot.work_date,
        slot_start=slot.slot_start,
        min_required=slot.min_required,
    )
