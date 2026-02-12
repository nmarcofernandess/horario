"""Rotas de template semanal (mosaico colaborador×dia→turno)."""
import pandas as pd
from fastapi import APIRouter, Depends
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import WeekdayTemplateSlot
from apps.backend.deps import get_repo

router = APIRouter(prefix="/weekday-template", tags=["weekday-template"])


@router.get("")
def list_weekday_template(
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    """Retorna lista de {employee_id, day_key, shift_code, minutes}."""
    df = repo.load_weekday_template_data(sector_id=sector_id)
    if df.empty:
        return []
    return [
        {
            "employee_id": str(row["employee_id"]),
            "day_key": str(row["day_key"]),
            "shift_code": str(row["shift_code"]),
            "minutes": int(row["minutes"]) if pd.notna(row.get("minutes")) else 0,
        }
        for _, row in df.iterrows()
    ]


@router.post("")
def save_weekday_template(
    data: list[WeekdayTemplateSlot],
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    """Aceita lista de {employee_id, day_key, shift_code, minutes} e salva."""
    if not data:
        return {"ok": True, "count": 0}
    df = pd.DataFrame([item.model_dump() for item in data])
    day_col = "day_name" if "day_name" in df.columns else "day_key"
    repo.save_weekday_template(df, sector_id)
    return {"ok": True, "count": len(df)}
