"""Rotas de setores"""
from fastapi import APIRouter, Depends
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.schemas import SectorCreate, SectorResponse
from api.deps import get_repo

router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("", response_model=list[SectorResponse])
def list_sectors(repo: SqlAlchemyRepository = Depends(get_repo)):
    sectors = repo.load_sectors()
    return [
        SectorResponse(sector_id=sid, name=name, active=True)
        for sid, name in sectors
    ]


@router.post("", response_model=SectorResponse)
def create_sector(
    data: SectorCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    repo.add_sector(data.sector_id, data.name)
    return SectorResponse(sector_id=data.sector_id, name=data.name, active=True)
