"""Rotas de configuração"""
from fastapi import APIRouter, Depends
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.deps import get_repo

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config(repo: SqlAlchemyRepository = Depends(get_repo)):
    """Retorna configuração básica da aplicação."""
    sectors = repo.load_sectors()
    return {
        "sectors": [{"sector_id": s[0], "name": s[1]} for s in sectors],
        "default_sector_id": "CAIXA",
    }
