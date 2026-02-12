"""Rotas de demand profile (slots de demanda por faixa horária)."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from apps.backend.src.domain.models import DemandSlot
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import DemandSlotCreate, DemandSlotResponse, DemandSlotUpdate
from apps.backend.deps import get_repo

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


@router.patch("", response_model=DemandSlotResponse)
def update_demand_slot(
    data: DemandSlotUpdate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    removed = repo.remove_demand_slot(
        sector_id=data.sector_id,
        work_date=data.original_work_date,
        slot_start=data.original_slot_start,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Slot original não encontrado")
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


@router.delete("")
def delete_demand_slot(
    work_date: date,
    slot_start: str,
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    removed = repo.remove_demand_slot(
        sector_id=sector_id,
        work_date=work_date,
        slot_start=slot_start,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Slot não encontrado")
    return {"ok": True}
