"""
Export de escala em formato calendário (HTML/Markdown) e resumo semanal.
Conforme PRD: fácil de compartilhar, imprimir e colar na parede.
"""

from pathlib import Path
from datetime import date, timedelta
from typing import Dict, List, Any
import pandas as pd


# Labels curtos para calendário (economia de espaço)
SHIFT_SHORT: Dict[str, str] = {
    "CAI1": "CAI1",
    "CAI2": "CAI2",
    "CAI3": "CAI3",
    "CAI4": "CAI4",
    "CAI5": "CAI5",
    "CAI6": "CAI6",
    "DOM_08_12_30": "DOM",
    "H_DOM": "DOM",
}


def _cell_value(row: dict) -> str:
    """Retorna valor da célula para calendário: turno ou FOL."""
    status = row.get("status", "")
    shift = row.get("shift_code", "")
    if status == "FOLGA":
        return "FOL"
    if status == "ABSENCE":
        return "AUS"
    if shift:
        return SHIFT_SHORT.get(shift, shift[:6] if len(shift) > 6 else shift)
    return "—"


def _build_weekly_summary(
    df: pd.DataFrame,
    contract_targets: Dict[str, int],
    week_definition: str = "MON_SUN",
) -> List[Dict[str, Any]]:
    """Resumo por semana: horas de cada colaborador vs contrato."""
    if df.empty:
        return []
    df = df.copy()
    df["work_date"] = pd.to_datetime(df["work_date"])
    if week_definition == "MON_SUN":
        df["week_start"] = df["work_date"] - pd.to_timedelta(df["work_date"].dt.weekday, unit="D")
    else:
        df["week_start"] = df["work_date"] - pd.to_timedelta((df["work_date"].dt.weekday + 1) % 7, unit="D")
    grouped = df.groupby(["employee_id", "week_start"])["minutes"].sum().reset_index()
    rows = []
    for _, r in grouped.iterrows():
        target = contract_targets.get(r["employee_id"], 2640)
        actual = int(r["minutes"])
        delta = actual - target
        ok = abs(delta) <= 120
        rows.append({
            "employee_id": r["employee_id"],
            "week_start": r["week_start"].date(),
            "week_end": (r["week_start"] + timedelta(days=6)).date(),
            "actual_minutes": actual,
            "target_minutes": target,
            "delta": delta,
            "ok": ok,
        })
    return rows


def export_markdown(
    assignments_df: pd.DataFrame,
    violations: List,
    contract_targets: Dict[str, int],
    period_start: date,
    period_end: date,
    employee_names: Dict[str, str] = None,
    week_definition: str = "MON_SUN",
) -> str:
    """Gera Markdown com calendário dia a dia e resumo por semana."""
    emp_names = employee_names or {}
    lines = [
        "# EscalaFlow",
        "",
        f"**Período:** {period_start} a {period_end}",
        f"**Corte semanal:** {week_definition}",
        "",
        "---",
        "",
        "## Calendário (dia a dia)",
        "",
    ]
    # Agrupar por data
    df = assignments_df.copy()
    df["work_date"] = pd.to_datetime(df["work_date"])
    dates = sorted(df["work_date"].drop_duplicates().tolist())
    employees = sorted(df["employee_id"].unique().tolist(), key=lambda x: emp_names.get(x, x))
    # Cabeçalho
    header = "| Data | " + " | ".join(emp_names.get(e, e) for e in employees) + " |"
    sep = "|" + "---|" * (len(employees) + 1)
    lines.append(header)
    lines.append(sep)
    for d in dates:
        row_vals = [d.strftime("%d/%m") if hasattr(d, "strftime") else str(d)]
        for emp in employees:
            r = df[(df["work_date"] == d) & (df["employee_id"] == emp)]
            val = _cell_value(r.iloc[0].to_dict()) if len(r) > 0 else "—"
            row_vals.append(val)
        lines.append("| " + " | ".join(row_vals) + " |")
    lines.extend(["", "**Legenda:** CAI1–CAI6 = turnos, DOM = domingo 4h30, FOL = folga, AUS = ausência", ""])

    # Resumo semanal
    weekly = _build_weekly_summary(assignments_df, contract_targets, week_definition)
    if weekly:
        lines.extend(["---", "", "## Resumo por semana", ""])
        weeks = sorted(set((w["week_start"], w["week_end"]) for w in weekly))
        for ws, we in weeks:
            week_rows = [r for r in weekly if r["week_start"] == ws]
            lines.append(f"### Semana {ws} a {we}")
            lines.append("")
            lines.append("| Colaborador | Real | Meta | Δ | Status |")
            lines.append("|-------------|------|------|---|--------|")
            for r in week_rows:
                nome = emp_names.get(r["employee_id"], r["employee_id"])
                status = "✓" if r["ok"] else f"⚠ {r['delta']:+}"
                lines.append(f"| {nome} | {r['actual_minutes']} min | {r['target_minutes']} min | {r['delta']:+} | {status} |")
            lines.append("")

    # Violações
    if violations:
        lines.extend(["---", "", "## Violações de conformidade", ""])
        for v in violations:
            emp = getattr(v, "employee_id", "?")
            detail = getattr(v, "detail", "")
            lines.append(f"- **{emp_names.get(emp, emp)}:** {detail}")
        lines.append("")

    return "\n".join(lines)


def export_html(
    assignments_df: pd.DataFrame,
    violations: List,
    contract_targets: Dict[str, int],
    period_start: date,
    period_end: date,
    employee_names: Dict[str, str] = None,
    week_definition: str = "MON_SUN",
) -> str:
    """Gera HTML com calendário estilo grade para impressão/cola na parede."""
    emp_names = employee_names or {}
    df = assignments_df.copy()
    df["work_date"] = pd.to_datetime(df["work_date"])
    dates = sorted(df["work_date"].drop_duplicates().tolist())
    employees = sorted(df["employee_id"].unique().tolist(), key=lambda x: emp_names.get(x, x))

    # Build grid
    rows_html = []
    for d in dates:
        cells = []
        for emp in employees:
            r = df[(df["work_date"] == d) & (df["employee_id"] == emp)]
            if len(r) == 0:
                val, css = "—", "cell-empty"
            else:
                row_dict = r.iloc[0].to_dict()
                val = _cell_value(row_dict)
                status = row_dict.get("status", "")
                if status == "FOLGA":
                    css = "cell-folga"
                elif status == "ABSENCE":
                    css = "cell-absence"
                elif "DOM" in str(row_dict.get("shift_code", "")):
                    css = "cell-dom"
                else:
                    css = "cell-work"
            cells.append(f'<td class="{css}">{val}</td>')
        day_str = d.strftime("%d/%m") if hasattr(d, "strftime") else str(d)
        weekday = d.strftime("%a") if hasattr(d, "strftime") else ""
        rows_html.append(f'<tr><th class="col-date">{day_str}<br><small>{weekday}</small></th>' + "".join(cells) + "</tr>")

    header_cells = "".join(f'<th>{emp_names.get(e, e)}</th>' for e in employees)
    grid = f'<table class="calendar-grid"><thead><tr><th>Data</th>{header_cells}</tr></thead><tbody>' + "".join(rows_html) + "</tbody></table>"

    # Semanal
    weekly = _build_weekly_summary(assignments_df, contract_targets, week_definition)
    weekly_html = ""
    if weekly:
        weeks = sorted(set((w["week_start"], w["week_end"]) for w in weekly))
        for ws, we in weeks:
            week_rows = [r for r in weekly if r["week_start"] == ws]
            rows_ww = []
            for r in week_rows:
                nome = emp_names.get(r["employee_id"], r["employee_id"])
                status_class = "ok" if r["ok"] else "warn"
                rows_ww.append(f'<tr><td>{nome}</td><td>{r["actual_minutes"]} min</td><td>{r["target_minutes"]} min</td><td>{r["delta"]:+}</td><td class="{status_class}">{"✓" if r["ok"] else "⚠"}</td></tr>')
            weekly_html += f'<div class="weekly-block"><h3>Semana {ws} a {we}</h3><table class="weekly-table"><thead><tr><th>Colaborador</th><th>Real</th><th>Meta</th><th>Δ</th><th>Status</th></tr></thead><tbody>' + "".join(rows_ww) + "</tbody></table></div>"

    viol_html = ""
    if violations:
        viol_items = []
        for v in violations:
            emp = getattr(v, "employee_id", "?")
            detail = getattr(v, "detail", "")
            viol_items.append(f"<li><strong>{emp_names.get(emp, emp)}:</strong> {detail}</li>")
        viol_html = f'<div class="violations"><h3>Violações</h3><ul>{"".join(viol_items)}</ul></div>'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EscalaFlow — {period_start} a {period_end}</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, sans-serif; margin: 20px; color: #333; }}
h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
.meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
.calendar-grid {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; margin-bottom: 2rem; }}
.calendar-grid th, .calendar-grid td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: center; }}
.calendar-grid th {{ background: #f5f5f5; font-weight: 600; }}
.calendar-grid .col-date {{ min-width: 50px; }}
.cell-work {{ background: #e8f5e9; }}
.cell-folga {{ background: #fff3e0; }}
.cell-dom {{ background: #e3f2fd; }}
.cell-absence {{ background: #ffebee; }}
.cell-empty {{ background: #fafafa; color: #999; }}
.weekly-block {{ margin-bottom: 1.5rem; }}
.weekly-table {{ border-collapse: collapse; font-size: 0.9rem; }}
.weekly-table th, .weekly-table td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
.weekly-table .ok {{ color: #2e7d32; }}
.weekly-table .warn {{ color: #c62828; }}
.violations {{ margin-top: 1.5rem; padding: 1rem; background: #fff8e1; border-radius: 8px; }}
.violations ul {{ margin: 0; padding-left: 1.2rem; }}
@media print {{ body {{ margin: 0; }} .calendar-grid {{ page-break-inside: avoid; }} }}
</style>
</head>
<body>
<h1>EscalaFlow</h1>
<p class="meta">Período: {period_start} a {period_end} | Corte: {week_definition}</p>
{grid}
<div class="weekly-summary">
<h2>Resumo por semana</h2>
{weekly_html}
</div>
{viol_html}
</body>
</html>"""
    return html


def export_calendar_files(
    output_path: Path,
    assignments_df: pd.DataFrame,
    violations: List,
    contract_targets: Dict[str, int],
    period_start: date,
    period_end: date,
    employee_names: Dict[str, str] = None,
    week_definition: str = "MON_SUN",
) -> Dict[str, Path]:
    """Exporta HTML e Markdown para o output_path. Retorna paths dos arquivos gerados."""
    output_path.mkdir(parents=True, exist_ok=True)
    emp_names = employee_names or {}
    md = export_markdown(assignments_df, violations, contract_targets, period_start, period_end, emp_names, week_definition)
    html = export_html(assignments_df, violations, contract_targets, period_start, period_end, emp_names, week_definition)
    md_path = output_path / "escala_calendario.md"
    html_path = output_path / "escala_calendario.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    return {"markdown": md_path, "html": html_path}
