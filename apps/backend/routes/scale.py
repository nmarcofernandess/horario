"""Rotas de escala (geração, assignments, violations, export)"""
from pathlib import Path
from datetime import date
import json
import os
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse

from apps.backend.src.domain.models import ProjectionContext
from apps.backend.src.domain.policy_loader import PolicyLoader
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository
from apps.backend.src.application.use_cases import ValidationOrchestrator

from apps.backend.schemas import (
    ScaleGenerateRequest,
    ScaleGenerateResponse,
    ScaleSimulateResponse,
    PreflightResponse,
    PreflightIssue,
    WeeklyAnalysisRequest,
    WeeklyAnalysisResponse,
    WeeklySummaryRow,
    AssignmentResponse,
    ViolationResponse,
)
from apps.backend.deps import get_repo

router = APIRouter(prefix="/scale", tags=["scale"])

ROOT = Path(__file__).resolve().parents[3]
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
        "R2_MIN_INTERSHIFT_REST": "Intervalo entre jornadas (mín. 11h)",
        "R4_WEEKLY_TARGET": "Meta semanal de horas",
        "R5_DEMAND_COVERAGE": "Cobertura insuficiente",
        "R6_MAX_DAILY_MINUTES": "Limite diário de jornada",
        # Compat legado para arquivos antigos já gerados.
        "R2_INTERSHIFT_REST": "Intervalo entre jornadas (mín. 11h)",
        "R3_WEEKLY_HOURS": "Meta semanal de horas",
        "R4_DEMAND_COVERAGE": "Cobertura insuficiente",
    }
    rows = []
    for _, r in df.iterrows():
        rule_code = str(r["rule_code"]).strip()
        rows.append(
            ViolationResponse(
                employee_id=str(r["employee_id"]),
                employee_name=emp_names.get(str(r["employee_id"])),
                rule_code=rule_code,
                rule_label=rule_labels.get(rule_code),
                severity=str(r["severity"]),
                date_start=str(r["date_start"]),
                date_end=str(r["date_end"]),
                detail=str(r["detail"]),
            )
        )
    return rows


def _build_weekly_summary_rows(
    assignments_df: pd.DataFrame,
    contract_profiles: dict,
    employee_names: dict,
    tolerance: int,
    week_definition: str,
) -> list[WeeklySummaryRow]:
    if assignments_df.empty:
        return []
    df = assignments_df.copy()
    df["work_date"] = pd.to_datetime(df["work_date"])
    if week_definition == "SUN_SAT":
        df["week_start"] = df["work_date"] - pd.to_timedelta((df["work_date"].dt.weekday + 1) % 7, unit="D")
    else:
        df["week_start"] = df["work_date"] - pd.to_timedelta(df["work_date"].dt.weekday, unit="D")
    grouped = df.groupby(["employee_id", "week_start"], as_index=False)["minutes"].sum()
    rows: list[WeeklySummaryRow] = []
    for _, r in grouped.iterrows():
        employee_id = str(r["employee_id"])
        profile = contract_profiles.get(employee_id, {"contract_code": "UNKNOWN", "weekly_minutes": 2640})
        target = int(profile.get("weekly_minutes", 2640))
        contract_code = str(profile.get("contract_code", "UNKNOWN"))
        actual = int(r["minutes"])
        delta = actual - target
        status = "OK" if abs(delta) <= tolerance else "OUT"
        week_start = r["week_start"]
        week_end = week_start + pd.Timedelta(days=6)
        rows.append(
            WeeklySummaryRow(
                window=week_definition,
                week_start=str(week_start.date()),
                week_end=str(week_end.date()),
                employee_id=employee_id,
                employee_name=employee_names.get(employee_id),
                contract_code=contract_code,
                actual_minutes=actual,
                target_minutes=target,
                delta_minutes=delta,
                status=status,
            )
        )
    return rows


def _collect_external_dependencies(policy_data: dict) -> list[str]:
    pending: list[str] = []
    marker_semantics = policy_data.get("constraints", {}).get("marker_semantics", {})
    unresolved_markers = [k for k, v in marker_semantics.items() if str(v).upper() == "UNKNOWN"]
    if unresolved_markers:
        pending.append(
            f"Semântica dos marcadores {', '.join(unresolved_markers)} ainda está UNKNOWN na policy."
        )

    cct_id = str(policy_data.get("jurisdiction", {}).get("collective_agreement_id", ""))
    if "PLACEHOLDER" in cct_id.upper():
        pending.append("Acordo Coletivo (CCT) pendente de identificação formal; governança jurídica incompleta.")
    if not cct_id.strip():
        pending.append("Base coletiva (CCT) está vazia; informe o identificador vigente.")

    legal_ok = bool(policy_data.get("jurisdiction", {}).get("sunday_holiday_legal_validated", False))
    if not legal_ok:
        pending.append("Validação jurídica de domingo/feriado não está marcada como concluída.")

    legal_refs = policy_data.get("legal_references", [])
    has_sunday_ref = any(str(item.get("rule_code")) == "R3_SUNDAY_AND_HOLIDAY_GOVERNANCE" for item in legal_refs)
    if not has_sunday_ref:
        pending.append("Referência legal de domingo/feriado (R3) não foi encontrada na policy.")
    return pending


def _load_policy_data() -> dict:
    policy_data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return policy_data


def _resolve_runtime_mode(policy_data: dict) -> str:
    env_name = os.getenv("ESCALAFLOW_ENV", "development").lower().strip()
    explicit_strict = os.getenv("ESCALAFLOW_STRICT_GOVERNANCE", "").lower().strip() in {"1", "true", "yes"}
    if explicit_strict or env_name in {"prod", "production"}:
        return "ESTRITO"
    raw_mode = str(policy_data.get("runtime_mode", {}).get("mode", "NORMAL")).strip().upper()
    if raw_mode not in {"NORMAL", "ESTRITO"}:
        return "NORMAL"
    return raw_mode


def _build_preflight(req: ScaleGenerateRequest, repo: SqlAlchemyRepository) -> PreflightResponse:
    blockers: list[PreflightIssue] = []
    if req.period_start > req.period_end:
        blockers.append(
            PreflightIssue(
                code="LOGIC_INVALID_PERIOD",
                message="Período inválido: data inicial maior que a data final.",
                recommended_action="Ajuste o período para início <= fim.",
            )
        )

    sector_ids = {sector_id for sector_id, _ in repo.load_sectors()}
    if req.sector_id not in sector_ids:
        blockers.append(
            PreflightIssue(
                code="LOGIC_UNKNOWN_SECTOR",
                message=f"Setor '{req.sector_id}' não encontrado.",
                recommended_action="Selecione um setor cadastrado em Configuração.",
            )
        )

    employees = [e for e in repo.load_employees().values() if e.sector_id == req.sector_id]
    if not employees:
        blockers.append(
            PreflightIssue(
                code="LOGIC_NO_EMPLOYEES",
                message=f"Não há colaboradores ativos no setor '{req.sector_id}'.",
                recommended_action="Cadastre ou ative colaboradores antes de gerar a escala.",
            )
        )

    shifts = repo.load_shifts(req.sector_id)
    if not shifts:
        blockers.append(
            PreflightIssue(
                code="LOGIC_NO_SHIFTS",
                message=f"Não há turnos cadastrados para o setor '{req.sector_id}'.",
                recommended_action="Cadastre turnos na aba de Configuração.",
            )
        )

    weekday_template = repo.load_weekday_template_data(req.sector_id)
    if weekday_template.empty:
        blockers.append(
            PreflightIssue(
                code="LOGIC_EMPTY_TEMPLATE",
                message=f"Mosaico semanal vazio para o setor '{req.sector_id}'.",
                recommended_action="Preencha o mosaico semanal antes de gerar ou simular.",
            )
        )

    policy_data = _load_policy_data()
    runtime_mode = _resolve_runtime_mode(policy_data)
    legal_pending = _collect_external_dependencies(policy_data)
    critical_warnings = [
        PreflightIssue(
            code=f"LEGAL_SOFT_{idx + 1}",
            message=message,
            recommended_action="Registrar decisão na aba de Governança e seguir com justificativa se necessário.",
        )
        for idx, message in enumerate(legal_pending)
    ]
    can_proceed = len(blockers) == 0
    ack_required = can_proceed and runtime_mode == "ESTRITO" and len(critical_warnings) > 0
    return PreflightResponse(
        mode=runtime_mode,
        blockers=blockers,
        critical_warnings=critical_warnings,
        can_proceed=can_proceed,
        ack_required=ack_required,
    )


def _enforce_runtime_gate(
    req: ScaleGenerateRequest,
    operation: str,
    repo: SqlAlchemyRepository,
) -> PreflightResponse:
    preflight = _build_preflight(req, repo)
    if not preflight.can_proceed:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Bloqueio por inconsistência lógica (LOGIC_HARD).",
                "blockers": [issue.model_dump() for issue in preflight.blockers],
            },
        )
    if preflight.ack_required:
        ack = req.risk_ack
        if ack is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Modo estrito exige confirmação de risco legal para continuar.",
                    "critical_warnings": [issue.model_dump() for issue in preflight.critical_warnings],
                },
            )
        repo.add_governance_audit_event(
            operation=operation,
            mode=preflight.mode,
            actor_role=ack.actor_role.strip().upper(),
            actor_name=ack.actor_name,
            reason=ack.reason,
            warnings=[issue.message for issue in preflight.critical_warnings],
            sector_id=req.sector_id,
            period_start=str(req.period_start),
            period_end=str(req.period_end),
        )
    return preflight


@router.post("/preflight", response_model=PreflightResponse)
def scale_preflight(
    req: ScaleGenerateRequest,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    return _build_preflight(req, repo)


@router.post("/generate", response_model=ScaleGenerateResponse)
def generate_scale(
    req: ScaleGenerateRequest,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    _enforce_runtime_gate(req, operation="GENERATE", repo=repo)
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


@router.post("/simulate", response_model=ScaleSimulateResponse)
def simulate_scale(
    req: ScaleGenerateRequest,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    _enforce_runtime_gate(req, operation="SIMULATE", repo=repo)
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
        result = orchestrator.run(
            context,
            POLICY_PATH,
            persist_results=False,
            include_preview=True,
        )
        assignments_df = pd.DataFrame(result.get("preview_assignments", []))
        violations_df = pd.DataFrame(result.get("preview_violations", []))
        emp_names = {e.employee_id: e.name for e in repo.load_employees().values()}
        return ScaleSimulateResponse(
            status=result["status"],
            assignments_count=result["assignments_count"],
            violations_count=result["violations_count"],
            preferences_processed=result["preferences_processed"],
            exceptions_applied=result.get("exceptions_applied", 0),
            assignments=_assignments_to_response(assignments_df, emp_names),
            violations=_violations_to_response(violations_df, emp_names),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weekly-analysis", response_model=WeeklyAnalysisResponse)
def weekly_analysis(
    req: WeeklyAnalysisRequest,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
    policy = policy_loader.load_policy(POLICY_PATH)
    policy_data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    tolerance = int(policy.constraints.get("weekly_minutes_tolerance", 120))
    emp_names = {e.employee_id: e.name for e in repo.load_employees().values()}
    contract_profiles = repo.load_contract_profiles(req.sector_id)

    if req.mode.upper() == "SIMULATION":
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
        result = orchestrator.run(
            context,
            POLICY_PATH,
            persist_results=False,
            include_preview=True,
        )
        assignments_df = pd.DataFrame(result.get("preview_assignments", []))
    else:
        assignments_df = _get_assignments_df()
        if not assignments_df.empty:
            work_date = pd.to_datetime(assignments_df["work_date"])
            assignments_df = assignments_df[
                (work_date >= pd.Timestamp(req.period_start))
                & (work_date <= pd.Timestamp(req.period_end))
            ]

    mon_sun_rows = _build_weekly_summary_rows(
        assignments_df,
        contract_profiles,
        emp_names,
        tolerance=tolerance,
        week_definition="MON_SUN",
    )
    sun_sat_rows = _build_weekly_summary_rows(
        assignments_df,
        contract_profiles,
        emp_names,
        tolerance=tolerance,
        week_definition="SUN_SAT",
    )
    return WeeklyAnalysisResponse(
        period_start=str(req.period_start),
        period_end=str(req.period_end),
        sector_id=req.sector_id,
        policy_week_definition=getattr(policy.week_definition, "value", "MON_SUN"),
        tolerance_minutes=tolerance,
        summaries_mon_sun=mon_sun_rows,
        summaries_sun_sat=sun_sat_rows,
        external_dependencies_open=_collect_external_dependencies(policy_data),
    )


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
