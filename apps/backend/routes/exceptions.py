"""Rotas de exceções (férias, atestado, trocas, bloqueios)"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from apps.backend.src.domain.models import ScheduleException, ExceptionType
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import ExceptionCreate, ExceptionResponse, ExceptionUpdate
from apps.backend.deps import get_repo

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
    try:
        exc = ScheduleException(
            sector_id=data.sector_id,
            employee_id=data.employee_id,
            exception_date=data.exception_date,
            exception_type=ExceptionType(data.exception_type),
            note=data.note or "",
        )
    except ValueError as exc_err:
        raise HTTPException(status_code=422, detail=f"exception_type inválido: {data.exception_type}") from exc_err
    repo.add_exception(exc)
    return ExceptionResponse(
        sector_id=exc.sector_id,
        employee_id=exc.employee_id,
        exception_date=exc.exception_date,
        exception_type=exc.exception_type.value,
        note=exc.note or None,
    )


@router.patch("", response_model=ExceptionResponse)
def update_exception(
    data: ExceptionUpdate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    removed = repo.remove_exception(
        sector_id=data.sector_id,
        employee_id=data.original_employee_id,
        exception_date=data.original_exception_date,
        exception_type=data.original_exception_type,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Exceção original não encontrada")
    try:
        exc = ScheduleException(
            sector_id=data.sector_id,
            employee_id=data.employee_id,
            exception_date=data.exception_date,
            exception_type=ExceptionType(data.exception_type),
            note=data.note or "",
        )
    except ValueError as exc_err:
        raise HTTPException(status_code=422, detail=f"exception_type inválido: {data.exception_type}") from exc_err
    repo.add_exception(exc)
    return ExceptionResponse(
        sector_id=exc.sector_id,
        employee_id=exc.employee_id,
        exception_date=exc.exception_date,
        exception_type=exc.exception_type.value,
        note=exc.note or None,
    )


@router.delete("")
def delete_exception(
    employee_id: str,
    exception_date: date,
    exception_type: str,
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    removed = repo.remove_exception(
        sector_id=sector_id,
        employee_id=employee_id,
        exception_date=exception_date,
        exception_type=exception_type,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Exceção não encontrada")
    return {"ok": True}
