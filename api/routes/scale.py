"""Rotas de escala (geração, assignments, violations, export)"""
from pathlib import Path
from datetime import date
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse

from src.domain.models import ProjectionContext
from src.domain.policy_loader import PolicyLoader
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.application.use_cases import ValidationOrchestrator

from api.schemas import (
    ScaleGenerateRequest,
    ScaleGenerateResponse,
    AssignmentResponse,
    ViolationResponse,
)
from api.deps import get_repo

router = APIRouter(prefix="/scale", tags=["scale"])

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "processed" / "real_scale_cycle"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"
DATA_DIR = ROOT / "data" / "fixtures"


def _get_assignments_df():
    path = OUTPUT / "final_assignments.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _get_violations_df():
    path = OUTPUT / "violations.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _assignments_to_response(df: pd.DataFrame, emp_names: dict) -> list:
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(
            AssignmentResponse(
                work_date=str(r["work_date"]),
                employee_id=str(r["employee_id"]),
                employee_name=emp_names.get(str(r["employee_id"])),
                status=str(r["status"]),
                shift_code=str(r["shift_code"]) if pd.notna(r.get("shift_code")) else None,
                minutes=int(r["minutes"]) if pd.notna(r.get("minutes")) else 0,
                source_rule=str(r["source_rule"]) if "source_rule" in r else "",
            )
        )
    return rows


def _violations_to_response(df: pd.DataFrame, emp_names: dict) -> list:
    if df.empty:
        return []
    rule_labels = {
        "R1_MAX_CONSECUTIVE": "Dias consecutivos (máx. 6)",
        "R2_INTERSHIFT_REST": "Interjornada mínima",
        "R3_WEEKLY_HOURS": "Meta semanal",
        "R4_DEMAND_COVERAGE": "Cobertura de demanda",
    }
    rows = []
    for _, r in df.iterrows():
        rows.append(
            ViolationResponse(
                employee_id=str(r["employee_id"]),
                employee_name=emp_names.get(str(r["employee_id"])),
                rule_code=str(r["rule_code"]),
                rule_label=rule_labels.get(str(r["rule_code"])),
                severity=str(r["severity"]),
                date_start=str(r["date_start"]),
                date_end=str(r["date_end"]),
                detail=str(r["detail"]),
            )
        )
    return rows


@router.post("/generate", response_model=ScaleGenerateResponse)
def generate_scale(
    req: ScaleGenerateRequest,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
    orchestrator = ValidationOrchestrator(
        repo=repo,
        policy_loader=policy_loader,
        output_path=OUTPUT,
        data_dir=DATA_DIR,
    )
    context = ProjectionContext(
        period_start=req.period_start,
        period_end=req.period_end,
        sector_id=req.sector_id,
        anchor_scale_id=1,
    )
    try:
        result = orchestrator.run(context, POLICY_PATH)
        return ScaleGenerateResponse(
            status=result["status"],
            assignments_count=result["assignments_count"],
            violations_count=result["violations_count"],
            preferences_processed=result["preferences_processed"],
            exceptions_applied=result.get("exceptions_applied", 0),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assignments", response_model=list[AssignmentResponse])
def get_assignments(repo: SqlAlchemyRepository = Depends(get_repo)):
    df = _get_assignments_df()
    emp_names = {e.employee_id: e.name for e in repo.load_employees().values()}
    return _assignments_to_response(df, emp_names)


@router.get("/violations", response_model=list[ViolationResponse])
def get_violations(repo: SqlAlchemyRepository = Depends(get_repo)):
    df = _get_violations_df()
    emp_names = {e.employee_id: e.name for e in repo.load_employees().values()}
    return _violations_to_response(df, emp_names)


@router.get("/export/html", response_class=HTMLResponse)
def export_html():
    path = OUTPUT / "escala_calendario.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Escala não gerada. Execute POST /scale/generate primeiro.")
    return HTMLResponse(content=path.read_text(encoding="utf-8"))


@router.get("/export/markdown", response_class=PlainTextResponse)
def export_markdown():
    path = OUTPUT / "escala_calendario.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Escala não gerada. Execute POST /scale/generate primeiro.")
    return PlainTextResponse(content=path.read_text(encoding="utf-8"))


@router.get("/export/html/download")
def download_html():
    path = OUTPUT / "escala_calendario.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Escala não gerada. Execute POST /scale/generate primeiro.")
    return FileResponse(
        path,
        media_type="text/html",
        filename="escala_calendario.html",
    )


@router.get("/export/markdown/download")
def download_markdown():
    path = OUTPUT / "escala_calendario.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Escala não gerada. Execute POST /scale/generate primeiro.")
    return FileResponse(
        path,
        media_type="text/markdown",
        filename="escala_calendario.md",
    )
