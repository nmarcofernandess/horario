"""Rotas de rodízio de domingos."""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.schemas import SundayRotationItem
from apps.backend.deps import get_repo

router = APIRouter(prefix="/sunday-rotation", tags=["sunday-rotation"])


@router.get("")
def list_sunday_rotation(
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    """Retorna lista de {scale_index, employee_id, sunday_date, folga_date}."""
    df = repo.load_sunday_rotation(sector_id=sector_id)
    if df.empty:
        return []
    return [
        {
            "scale_index": int(row["scale_index"]),
            "employee_id": str(row["employee_id"]),
            "sunday_date": str(row["sunday_date"]),
            "folga_date": str(row["folga_date"]) if pd.notna(row.get("folga_date")) else None,
        }
        for _, row in df.iterrows()
    ]


@router.post("")
def save_sunday_rotation(
    data: list[SundayRotationItem],
    sector_id: str = "CAIXA",
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    """Aceita lista de {scale_index, employee_id, sunday_date, folga_date} e salva."""
    if not data:
        return {"ok": True, "count": 0}
    df = pd.DataFrame([item.model_dump() for item in data])
    if "folga_date" not in df.columns:
        df["folga_date"] = None
    try:
        repo.save_sunday_rotation(df, sector_id=sector_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "count": len(df)}
