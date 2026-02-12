"""
Camada de apresentação para usuário final (RH).
Traduz colunas técnicas em labels humanizados.
"""

from typing import Dict

# Mapeamento de códigos de turno para labels legíveis
SHIFT_LABELS: Dict[str, str] = {
    "CAI1": "Manhã (9h30)",
    "CAI2": "Manhã (6h)",
    "CAI3": "Tarde (8h30)",
    "CAI4": "Manhã (5h)",
    "CAI5": "Tarde (5h30)",
    "CAI6": "Manhã (5h30)",
    "DOM_08_12_30": "Domingo (4h30)",
    "H_DOM": "Domingo",
}

# Status
STATUS_LABELS: Dict[str, str] = {
    "WORK": "Trabalho",
    "FOLGA": "Folga",
    "ABSENCE": "Ausência",
}

# Colunas de escala → labels para exibição
COLUMN_LABELS = {
    "work_date": "Data",
    "employee_id": "Colaborador",
    "status": "Status",
    "shift_code": "Turno",
    "minutes": "Carga (min)",
    "source_rule": "Origem",
    "source": "Origem",
    "scale_id": "Ciclo",
}

# Colunas de violação
VIOLATION_LABELS = {
    "employee_id": "Colaborador",
    "rule_code": "Regra",
    "severity": "Gravidade",
    "date_start": "Início",
    "date_end": "Fim",
    "detail": "Detalhe",
}

# Regras de compliance → labels amigáveis
RULE_LABELS: Dict[str, str] = {
    "R1_MAX_CONSECUTIVE": "Dias consecutivos (máx. 6)",
    "R4_WEEKLY_TARGET": "Meta semanal de horas",
}

# Gravidade
SEVERITY_LABELS = {
    "CRITICAL": "Crítico",
    "HIGH": "Alto",
    "MEDIUM": "Médio",
    "LOW": "Baixo",
}


def humanize_shift(code: str) -> str:
    return SHIFT_LABELS.get(code, code or "—")


def humanize_status(status: str) -> str:
    return STATUS_LABELS.get(status, status or "—")


def humanize_severity(sev: str) -> str:
    return SEVERITY_LABELS.get(sev, sev)


def humanize_df_scale(df, employee_names: Dict[str, str] = None):
    """Renomeia colunas e valores de um DataFrame de escala para exibição."""
    out = df.rename(columns=COLUMN_LABELS).copy()
    if "Status" in out.columns:
        out["Status"] = out["Status"].map(humanize_status)
    if "Turno" in out.columns:
        out["Turno"] = out["Turno"].map(humanize_shift)
    if employee_names and "Colaborador" in out.columns:
        out["Colaborador"] = out["Colaborador"].map(lambda x: employee_names.get(x, x))
    return out


def humanize_rule(code: str) -> str:
    return RULE_LABELS.get(code, code or "—")


def humanize_df_violations(df, employee_names: Dict[str, str] = None):
    """Renomeia colunas e valores de violações para exibição."""
    out = df.rename(columns=VIOLATION_LABELS).copy()
    if "Gravidade" in out.columns:
        out["Gravidade"] = out["Gravidade"].map(humanize_severity)
    if "Regra" in out.columns:
        out["Regra"] = out["Regra"].map(humanize_rule)
    if employee_names and "Colaborador" in out.columns:
        out["Colaborador"] = out["Colaborador"].map(lambda x: employee_names.get(x, x))
    return out
