"""Rotas de exceções (férias, atestado, trocas, bloqueios)"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.domain.models import ScheduleException, ExceptionType
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.schemas import ExceptionCreate, ExceptionResponse
from api.deps import get_repo

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


@router.get("", response_model=list[ExceptionResponse])
def list_exceptions(
    sector_id: str = "CAIXA",
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    excs = repo.load_exceptions(sector_id=sector_id, period_start=period_start, period_end=period_end)
    return [
        ExceptionResponse(
            sector_id=e.sector_id,
            employee_id=e.employee_id,
            exception_date=e.exception_date,
            exception_type=e.exception_type.value,
            note=e.note or None,
        )
        for e in excs
    ]


@router.post("", response_model=ExceptionResponse)
def create_exception(
    data: ExceptionCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    exc = ScheduleException(
        sector_id=data.sector_id,
        employee_id=data.employee_id,
        exception_date=data.exception_date,
        exception_type=ExceptionType(data.exception_type),
        note=data.note or "",
    )
    repo.add_exception(exc)
    return ExceptionResponse(
        sector_id=exc.sector_id,
        employee_id=exc.employee_id,
        exception_date=exc.exception_date,
        exception_type=exc.exception_type.value,
        note=exc.note or None,
    )
