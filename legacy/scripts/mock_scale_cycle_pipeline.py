#!/usr/bin/env python3
"""Build a scale-cycle-first mock pipeline from extracted datasets."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT_DIR = PROCESSED / "mock_scale_cycle"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"

DAY_TO_INDEX = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
PT_DAY = {"SEG": "MON", "TER": "TUE", "QUA": "WED", "QUI": "THU", "SEX": "FRI", "SAB": "SAT", "DOM": "SUN"}
CYCLE_WEEK_ORDER = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

NAME_TO_EMPLOYEE_ID = {
    "CLEONICE": "CLE",
    "ANA JULIA": "ANJ",
    "GABRIEL": "GAB",
    "ALICE": "ALI",
    "MAYUMI": "MAY",
    "MAYUME": "MAY",
    "HELOISA": "HEL",
}

EMPLOYEE_META = {
    "CLE": {"name": "CLEONICE", "contract_code": "H44_CAIXA", "rank": 1},
    "ANJ": {"name": "ANA JULIA", "contract_code": "H44_CAIXA", "rank": 2},
    "GAB": {"name": "GABRIEL", "contract_code": "H36_CAIXA", "rank": 3},
    "ALI": {"name": "ALICE", "contract_code": "H30_CAIXA", "rank": 4},
    "MAY": {"name": "MAYUMI", "contract_code": "H30_CAIXA", "rank": 5},
    "HEL": {"name": "HELOISA", "contract_code": "H30_CAIXA", "rank": 6},
}


@dataclass(frozen=True)
class ProjectionContext:
    period_start: date
    period_end: date
    sector_id: str
    anchor_scale_id: int = 1


def parse_hms_to_minutes(value: str) -> int:
    parts = value.strip().split(":")
    if len(parts) != 3:
        return 0
    h, m, _ = parts
    return int(h) * 60 + int(m)


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def build_shift_minutes(policy: dict) -> dict[str, int]:
    minutes = {}
    for item in policy["shift_catalog"]["weekday_shifts"]:
        minutes[item["code"]] = int(item["minutes"])
    sunday_shift = policy["shift_catalog"]["sunday_shift"]
    minutes[sunday_shift["code"]] = int(sunday_shift["minutes"])
    return minutes


def build_contract_targets(policy: dict) -> dict[str, int]:
    target = {}
    contract_minutes = {
        contract["contract_code"]: int(contract["weekly_minutes"]) for contract in policy["contracts"]
    }
    for employee_id, meta in EMPLOYEE_META.items():
        target[employee_id] = contract_minutes[meta["contract_code"]]
    return target


def build_employee_registry() -> pd.DataFrame:
    rows = []
    for employee_id, meta in EMPLOYEE_META.items():
        rows.append(
            {
                "employee_id": employee_id,
                "name": meta["name"],
                "contract_code": meta["contract_code"],
                "active": True,
            }
        )
    return pd.DataFrame(rows).sort_values("employee_id")


def load_sunday_rotation() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "xlsx_caixas_sunday_rotation.csv")
    df["employee_id"] = df["employee_norm"].map(NAME_TO_EMPLOYEE_ID)
    df = df[df["employee_id"].notna()].copy()
    df["sunday_date"] = pd.to_datetime(df["sunday_date"]).dt.date
    df["folga_date"] = pd.to_datetime(df["folga_date"]).dt.date
    return df.sort_values(["scale_index", "employee_id", "sunday_date"])


def validate_preflight_consistency(sunday_rotation: pd.DataFrame, weekday_template: pd.DataFrame) -> list[str]:
    """Fail-fast check: conflicts between inputs before expensive processing."""
    errors = []
    
    # Check 1: Employee defined in rotation but missing from template
    rot_employees = set(sunday_rotation["employee_id"].unique())
    tmpl_employees = set(weekday_template["employee_id"].unique())
    missing = rot_employees - tmpl_employees
    if missing:
        errors.append(f"PREFLIGHT_ERROR: Employees in sunday_rotation missing from weekday_template: {missing}")

    # Check 2: Duplicate sunday dates for same employee
    dupes = sunday_rotation[sunday_rotation.duplicated(["employee_id", "sunday_date"])]
    if not dupes.empty:
        errors.append(f"PREFLIGHT_ERROR: Duplicate sunday rotation entries found: {len(dupes)} conflicts.")

    return errors


def build_weekday_template(policy: dict) -> tuple[pd.DataFrame, dict[str, str]]:
    totals = pd.read_csv(PROCESSED / "pdf_rita1_totals.csv")
    totals["employee_id"] = totals["employee_norm"].map(NAME_TO_EMPLOYEE_ID)
    totals["day_key"] = totals["day_name"].map(PT_DAY)
    totals = totals[totals["employee_id"].notna() & totals["day_key"].notna()].copy()
    totals["minutes"] = totals["day_total_hms"].map(parse_hms_to_minutes)

    shift_minutes = build_shift_minutes(policy)

    # Per employee/day use median from known good table.
    weekday_template = (
        totals.groupby(["employee_id", "day_key", "inferred_shift_code"], as_index=False)["minutes"]
        .median()
        .sort_values(["employee_id", "day_key", "minutes"], ascending=[True, True, False])
        .drop_duplicates(["employee_id", "day_key"])
        .rename(columns={"inferred_shift_code": "shift_code", "minutes": "minutes_hint"})
    )

    # Fallback weekday shift per employee.
    default_shift = (
        totals.groupby(["employee_id", "inferred_shift_code"])
        .size()
        .reset_index(name="count")
        .sort_values(["employee_id", "count"], ascending=[True, False])
        .drop_duplicates("employee_id")
        .set_index("employee_id")["inferred_shift_code"]
        .to_dict()
    )

    rows = []
    for employee_id in EMPLOYEE_META:
        for day_key in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            row = weekday_template[
                (weekday_template["employee_id"] == employee_id)
                & (weekday_template["day_key"] == day_key)
            ]
            if not row.empty:
                shift_code = str(row.iloc[0]["shift_code"])
                minutes = int(row.iloc[0]["minutes_hint"])
            else:
                shift_code = default_shift.get(employee_id, "CAI4")
                minutes = int(shift_minutes.get(shift_code, 0))
            rows.append(
                {
                    "employee_id": employee_id,
                    "day_key": day_key,
                    "shift_code": shift_code,
                    "minutes": minutes,
                }
            )

    return pd.DataFrame(rows), default_shift


def build_scale_cycle_template(
    sunday_rotation: pd.DataFrame,
    weekday_template: pd.DataFrame,
    sunday_shift_code: str,
) -> pd.DataFrame:
    scale_count = int(sunday_rotation["scale_index"].max())
    cycle_length_days = scale_count * 7

    template_index = {}
    for _, row in weekday_template.iterrows():
        template_index[(row["employee_id"], row["day_key"])] = (row["shift_code"], int(row["minutes"]))

    rows = []
    for scale_id in range(1, scale_count + 1):
        for employee_id in EMPLOYEE_META:
            for day_idx, day_key in enumerate(CYCLE_WEEK_ORDER):
                cycle_day = (scale_id - 1) * 7 + day_idx + 1
                if day_key == "SUN":
                    status = "FOLGA"
                    shift_code = ""
                    minutes = 0
                else:
                    status = "WORK"
                    shift_code, minutes = template_index[(employee_id, day_key)]
                rows.append(
                    {
                        "scale_id": scale_id,
                        "cycle_day": cycle_day,
                        "employee_id": employee_id,
                        "day_key": day_key,
                        "status": status,
                        "shift_code": shift_code,
                        "minutes": minutes,
                        "source": "MOCK_BASE_WEEKDAY_TEMPLATE",
                    }
                )

    df = pd.DataFrame(rows)

    # Sunday work + linked compensation from known-good sunday rotation table.
    for _, row in sunday_rotation.iterrows():
        scale_id = int(row["scale_index"])
        employee_id = row["employee_id"]
        sunday_day = (scale_id - 1) * 7 + 1
        delta = int((row["folga_date"] - row["sunday_date"]).days)
        compensation_day = sunday_day + delta if 0 <= delta <= 6 else None

        sunday_mask = (
            (df["scale_id"] == scale_id)
            & (df["employee_id"] == employee_id)
            & (df["cycle_day"] == sunday_day)
        )
        df.loc[sunday_mask, ["status", "shift_code", "minutes", "source"]] = [
            "WORK",
            sunday_shift_code,
            270,
            "SUNDAY_ROTATION",
        ]

        if compensation_day is not None and 1 <= compensation_day <= cycle_length_days:
            folga_mask = (
                (df["scale_id"] == scale_id)
                & (df["employee_id"] == employee_id)
                & (df["cycle_day"] == compensation_day)
            )
            df.loc[folga_mask, ["status", "shift_code", "minutes", "source"]] = [
                "FOLGA",
                "",
                0,
                "SUNDAY_COMPENSATION",
            ]

    return df.sort_values(["scale_id", "cycle_day", "employee_id"])


def project_cycle_to_days(template: pd.DataFrame, context: ProjectionContext) -> pd.DataFrame:
    rows = []
    cycle_length_days = int(template["cycle_day"].max())
    base_cycle_day = ((context.anchor_scale_id - 1) * 7) + 1
    cursor = context.period_start
    while cursor <= context.period_end:
        cycle_offset = (cursor - context.period_start).days
        cycle_day = ((base_cycle_day - 1 + cycle_offset) % cycle_length_days) + 1
        scale_id = ((cycle_day - 1) // 7) + 1
        day_rows = template[template["cycle_day"] == cycle_day]
        for _, tr in day_rows.iterrows():
            calendar_day_key = [k for k, v in DAY_TO_INDEX.items() if v == cursor.weekday()][0]
            rows.append(
                {
                    "work_date": cursor.isoformat(),
                    "employee_id": tr["employee_id"],
                    "employee_name": EMPLOYEE_META[tr["employee_id"]]["name"],
                    "scale_id": int(scale_id),
                    "cycle_day": int(cycle_day),
                    "day_key": tr["day_key"],
                    "calendar_day_key": calendar_day_key,
                    "status": tr["status"],
                    "shift_code": tr["shift_code"],
                    "minutes": int(tr["minutes"]),
                    "template_source": tr["source"],
                }
            )
        cursor += timedelta(days=1)
    return pd.DataFrame(rows).sort_values(["work_date", "employee_id"])


def build_weekly_view(day_assignments: pd.DataFrame, contract_target: dict[str, int], week_mode: str) -> pd.DataFrame:
    df = day_assignments.copy()
    df["work_date"] = pd.to_datetime(df["work_date"])
    if week_mode == "MON_SUN":
        week_start = df["work_date"] - pd.to_timedelta(df["work_date"].dt.weekday, unit="D")
    elif week_mode == "SUN_SAT":
        week_start = df["work_date"] - pd.to_timedelta((df["work_date"].dt.weekday + 1) % 7, unit="D")
    else:
        raise ValueError(f"Unknown week mode: {week_mode}")
    df["week_start"] = week_start.dt.date
    grouped = (
        df.groupby(["employee_id", "week_start"], as_index=False)
        .agg(worked_minutes=("minutes", "sum"), day_count=("work_date", "nunique"))
    )
    grouped["target_minutes"] = grouped["employee_id"].map(contract_target)
    grouped["delta_minutes"] = grouped["worked_minutes"] - grouped["target_minutes"]
    grouped["week_mode"] = week_mode
    return grouped.sort_values(["week_start", "employee_id"])


def detect_consecutive_violations(day_assignments: pd.DataFrame, max_days: int = 6) -> pd.DataFrame:
    df = day_assignments.copy().sort_values(["employee_id", "work_date"])
    violations = []
    for employee_id, group in df.groupby("employee_id"):
        streak = 0
        streak_start = None
        for _, row in group.iterrows():
            is_work = row["status"] == "WORK"
            if is_work:
                streak += 1
                if streak == 1:
                    streak_start = row["work_date"]
                if streak > max_days:
                    violations.append(
                        {
                            "employee_id": employee_id,
                            "rule_code": "R1_MAX_6_CONSECUTIVE_DAYS",
                            "severity": "CRITICAL",
                            "date_start": streak_start,
                            "date_end": row["work_date"],
                            "detail": f"Streak={streak} days",
                        }
                    )
            else:
                streak = 0
                streak_start = None
    return pd.DataFrame(violations)


def detect_weekly_violations(weekly: pd.DataFrame, tolerance: int, week_mode: str) -> pd.DataFrame:
    rows = []
    for _, row in weekly.iterrows():
        if int(row["day_count"]) < 7:
            continue
        if abs(int(row["delta_minutes"])) > tolerance:
            rows.append(
                {
                    "employee_id": row["employee_id"],
                    "rule_code": "R4_WEEKLY_CONTRACT_TARGET",
                    "severity": "LOW",
                    "date_start": row["week_start"].isoformat(),
                    "date_end": (row["week_start"] + timedelta(days=6)).isoformat(),
                    "detail": f"{week_mode} delta={int(row['delta_minutes'])} min",
                }
            )
    return pd.DataFrame(rows)


def build_mock_employee_preferences(context: ProjectionContext) -> pd.DataFrame:
    rows = [
        {
            "request_id": "REQ-001",
            "employee_id": "GAB",
            "request_date": "2026-02-15",
            "request_type": "AVOID_SUNDAY_DATE",
            "target_shift_code": "",
            "priority": "HIGH",
            "note": "Evento familiar no domingo",
        },
        {
            "request_id": "REQ-002",
            "employee_id": "HEL",
            "request_date": "2026-02-17",
            "request_type": "SHIFT_CHANGE_ON_DATE",
            "target_shift_code": "CAI5",
            "priority": "MEDIUM",
            "note": "Preferencia por turno CAI5",
        },
        {
            "request_id": "REQ-003",
            "employee_id": "ALI",
            "request_date": "2026-02-11",
            "request_type": "FOLGA_ON_DATE",
            "target_shift_code": "",
            "priority": "HIGH",
            "note": "Consulta medica",
        },
        {
            "request_id": "REQ-004",
            "employee_id": "MAY",
            "request_date": "2026-02-24",
            "request_type": "SHIFT_CHANGE_ON_DATE",
            "target_shift_code": "CAI6",
            "priority": "LOW",
            "note": "Troca de turno",
        },
        {
            "request_id": "REQ-005",
            "employee_id": "CLE",
            "request_date": "2026-02-27",
            "request_type": "FOLGA_ON_DATE",
            "target_shift_code": "",
            "priority": "HIGH",
            "note": "Compromisso pessoal",
        },
        {
            "request_id": "REQ-006",
            "employee_id": "ANJ",
            "request_date": "2026-03-03",
            "request_type": "SHIFT_CHANGE_ON_DATE",
            "target_shift_code": "CAI2",
            "priority": "MEDIUM",
            "note": "Preferencia por ajuste pontual",
        },
    ]
    df = pd.DataFrame(rows)
    df = df[
        (df["request_date"] >= context.period_start.isoformat())
        & (df["request_date"] <= context.period_end.isoformat())
    ].copy()
    return df.sort_values(["request_date", "employee_id", "request_id"])


def _week_start_sun_sat(value: date) -> date:
    return value - timedelta(days=(value.weekday() + 1) % 7)


def _employee_max_streak(day_assignments: pd.DataFrame, employee_id: str) -> int:
    df = day_assignments[day_assignments["employee_id"] == employee_id].copy()
    df = df.sort_values("work_date")
    streak = 0
    max_streak = 0
    for _, row in df.iterrows():
        if row["status"] == "WORK":
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def apply_employee_preferences(
    day_assignments: pd.DataFrame,
    preferences: pd.DataFrame,
    policy: dict,
    contract_target: dict[str, int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if preferences.empty:
        return day_assignments.copy(), pd.DataFrame(
            columns=[
                "request_id",
                "employee_id",
                "request_date",
                "request_type",
                "decision",
                "reason",
                "before_status",
                "after_status",
                "before_shift_code",
                "after_shift_code",
            ]
        )

    # 1. Sort preferences by manual rank (Drag-n-Drop simulated)
    # The 'rank' field comes from the employee registry, which RH can reorder manually.
    preferences["employee_rank"] = preferences["employee_id"].apply(
        lambda eid: EMPLOYEE_META.get(eid, {}).get("rank", 999)
    )
    
    # Sort: Lower rank number = Higher priority (1st, 2nd, 3rd...)
    preferences = preferences.sort_values(
        ["employee_rank", "request_date", "priority"], 
        ascending=[True, True, True]
    ).reset_index(drop=True)

    pref_policy = policy.get("employee_preference_policy", {})
    enabled = bool(pref_policy.get("enabled", False))
    accepted_types = set(pref_policy.get("accepted_request_types", []))
    max_per_employee = int(pref_policy.get("max_approved_requests_per_employee_per_cycle", 0))
    max_weekly_delta = int(pref_policy.get("max_weekly_delta_after_preference_minutes", 0))
    reject_hard = bool(pref_policy.get("reject_if_breaks_hard_constraints", True))
    reject_sunday_coverage = bool(pref_policy.get("reject_if_breaks_sunday_coverage", True))
    coverage_per_sunday = int(policy["sunday_policy"]["coverage_per_sunday"])
    max_streak_allowed = int(policy["constraints"]["max_consecutive_work_days"])

    shift_minutes = build_shift_minutes(policy)
    allowed_shifts: dict[str, set[str]] = {}
    for contract in policy["contracts"]:
        codes = set(contract.get("allowed_weekday_shift_codes", []))
        for employee_id in contract["employees"]:
            allowed_shifts[employee_id] = codes

    out = day_assignments.copy()
    out["work_date"] = pd.to_datetime(out["work_date"]).dt.date
    approved_count: dict[str, int] = defaultdict(int)
    decisions = []

    for _, req in preferences.iterrows():
        request_id = req["request_id"]
        employee_id = req["employee_id"]
        request_date = datetime.strptime(req["request_date"], "%Y-%m-%d").date()
        request_type = req["request_type"]
        target_shift = str(req.get("target_shift_code", "") or "")

        current_mask = (out["employee_id"] == employee_id) & (out["work_date"] == request_date)
        if not current_mask.any():
            decisions.append(
                {
                    "request_id": request_id,
                    "employee_id": employee_id,
                    "request_date": request_date.isoformat(),
                    "request_type": request_type,
                    "decision": "REJECTED",
                    "reason": "DATE_OR_EMPLOYEE_NOT_FOUND",
                    "before_status": "",
                    "after_status": "",
                    "before_shift_code": "",
                    "after_shift_code": "",
                }
            )
            continue

        current_row = out[current_mask].iloc[0]
        before_status = str(current_row["status"])
        before_shift = str(current_row["shift_code"] or "")
        before_minutes = int(current_row["minutes"])

        decision = "REJECTED"
        reason = ""
        after_status = before_status
        after_shift = before_shift
        after_minutes = before_minutes

        if not enabled:
            reason = "PREFERENCE_FEATURE_DISABLED"
        elif request_type not in accepted_types:
            reason = "REQUEST_TYPE_NOT_ALLOWED"
        elif approved_count[employee_id] >= max_per_employee:
            reason = "EMPLOYEE_APPROVAL_LIMIT_REACHED"
        else:
            if request_type in {"FOLGA_ON_DATE", "AVOID_SUNDAY_DATE"}:
                if before_status != "WORK":
                    reason = "ALREADY_NOT_WORKING"
                else:
                    after_status = "FOLGA"
                    after_shift = ""
                    after_minutes = 0
            elif request_type == "SHIFT_CHANGE_ON_DATE":
                if before_status != "WORK":
                    reason = "SHIFT_CHANGE_REQUIRES_WORK_DAY"
                elif not target_shift:
                    reason = "TARGET_SHIFT_REQUIRED"
                elif target_shift not in allowed_shifts.get(employee_id, set()):
                    reason = "TARGET_SHIFT_NOT_ALLOWED_FOR_CONTRACT"
                else:
                    after_status = "WORK"
                    after_shift = target_shift
                    after_minutes = int(shift_minutes.get(target_shift, 0))
            else:
                reason = "UNSUPPORTED_REQUEST_TYPE"

        if not reason:
            simulated = out.copy()
            simulated.loc[current_mask, "status"] = after_status
            simulated.loc[current_mask, "shift_code"] = after_shift
            simulated.loc[current_mask, "minutes"] = after_minutes

            if reject_sunday_coverage and request_date.weekday() == 6:
                sunday_workers = simulated[
                    (simulated["work_date"] == request_date) & (simulated["status"] == "WORK")
                ]["employee_id"].nunique()
                if sunday_workers < coverage_per_sunday:
                    reason = "SUNDAY_COVERAGE_BROKEN"

            if not reason:
                week_start = _week_start_sun_sat(request_date)
                week_end = week_start + timedelta(days=6)
                base_week = out[
                    (out["employee_id"] == employee_id)
                    & (out["work_date"] >= week_start)
                    & (out["work_date"] <= week_end)
                ]["minutes"].sum()
                sim_week = simulated[
                    (simulated["employee_id"] == employee_id)
                    & (simulated["work_date"] >= week_start)
                    & (simulated["work_date"] <= week_end)
                ]["minutes"].sum()
                target = int(contract_target[employee_id])
                if abs(sim_week - target) > max_weekly_delta and abs(sim_week - target) > abs(base_week - target):
                    reason = "WEEKLY_DELTA_LIMIT_EXCEEDED"

            if not reason and reject_hard:
                before_streak = _employee_max_streak(out, employee_id)
                after_streak = _employee_max_streak(simulated, employee_id)
                # RH blocks preference only when request creates/worsens a hard streak breach.
                if after_streak > max_streak_allowed and after_streak > before_streak:
                    reason = "HARD_CONSTRAINT_STREAK_BROKEN"

            if not reason:
                decision = "APPROVED"
                out = simulated
                approved_count[employee_id] += 1
                out.loc[current_mask, "template_source"] = "RH_APPROVED_PREFERENCE"

        decisions.append(
            {
                "request_id": request_id,
                "employee_id": employee_id,
                "request_date": request_date.isoformat(),
                "request_type": request_type,
                "decision": decision,
                "reason": reason or "OK",
                "before_status": before_status,
                "after_status": after_status,
                "before_shift_code": before_shift,
                "after_shift_code": after_shift,
            }
        )

    return out.sort_values(["work_date", "employee_id"]), pd.DataFrame(decisions)


def run(context: ProjectionContext) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    policy = load_policy()
    
    # Validate Sector
    if policy.get("sector_id") != context.sector_id:
        raise ValueError(f"Policy sector ({policy.get('sector_id')}) does not match context sector ({context.sector_id})")

    sunday_rotation = load_sunday_rotation()
    weekday_template, _ = build_weekday_template(policy)

    # Preflight Fail-Fast
    preflight_errors = validate_preflight_consistency(sunday_rotation, weekday_template)
    if preflight_errors:
        raise ValueError(f"Preflight Validation Failed: {preflight_errors}")

    sunday_shift = policy["shift_catalog"]["sunday_shift"]["code"]
    scale_template = build_scale_cycle_template(sunday_rotation, weekday_template, sunday_shift)
    day_assignments = project_cycle_to_days(scale_template, context)
    preferences = build_mock_employee_preferences(context)

    contract_target = build_contract_targets(policy)
    day_assignments, preference_decisions = apply_employee_preferences(
        day_assignments=day_assignments,
        preferences=preferences,
        policy=policy,
        contract_target=contract_target,
    )

    weekly_mon_sun = build_weekly_view(day_assignments, contract_target, "MON_SUN")
    weekly_sun_sat = build_weekly_view(day_assignments, contract_target, "SUN_SAT")

    consecutive_v = detect_consecutive_violations(
        day_assignments, max_days=int(policy["constraints"]["max_consecutive_work_days"])
    )
    tolerance = int(policy["constraints"]["weekly_minutes_tolerance"])
    weekly_v = pd.concat(
        [
            detect_weekly_violations(weekly_mon_sun, tolerance, "MON_SUN"),
            detect_weekly_violations(weekly_sun_sat, tolerance, "SUN_SAT"),
        ],
        ignore_index=True,
    )
    violations = pd.concat([consecutive_v, weekly_v], ignore_index=True).sort_values(
        ["severity", "employee_id", "date_start"]
    )

    employee_registry = build_employee_registry()
    projection_context = {
        "period_start": context.period_start.isoformat(),
        "period_end": context.period_end.isoformat(),
        "anchor_scale_id": context.anchor_scale_id,
        "cycle_length_days": int(scale_template["cycle_day"].max()),
        "scale_count": int(scale_template["scale_id"].max()),
        "model": "SCALE_CYCLE_PRIMARY",
    }

    employee_registry.to_csv(OUT_DIR / "employee_registry.mock.csv", index=False)
    weekday_template.to_csv(OUT_DIR / "weekday_template.mock.csv", index=False)
    sunday_rotation.to_csv(OUT_DIR / "sunday_rotation.mock.csv", index=False)
    scale_template.to_csv(OUT_DIR / "scale_cycle_template.mock.csv", index=False)
    day_assignments.to_csv(OUT_DIR / "day_assignments.mock.csv", index=False)
    preferences.to_csv(OUT_DIR / "employee_preferences.mock.csv", index=False)
    preference_decisions.to_csv(OUT_DIR / "preference_decisions.mock.csv", index=False)
    weekly_mon_sun.to_csv(OUT_DIR / "weekly_summary_mon_sun.mock.csv", index=False)
    weekly_sun_sat.to_csv(OUT_DIR / "weekly_summary_sun_sat.mock.csv", index=False)
    violations.to_csv(OUT_DIR / "violations.mock.csv", index=False)
    (OUT_DIR / "cycle_projection_context.mock.json").write_text(
        json.dumps(projection_context, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = {
        "out_dir": str(OUT_DIR.relative_to(ROOT)),
        "employees": int(employee_registry.shape[0]),
        "scale_count": projection_context["scale_count"],
        "cycle_length_days": projection_context["cycle_length_days"],
        "day_assignments": int(day_assignments.shape[0]),
        "sunday_rotation_rows": int(sunday_rotation.shape[0]),
        "preferences_requested": int(preferences.shape[0]),
        "preferences_approved": int((preference_decisions["decision"] == "APPROVED").sum()),
        "preferences_rejected": int((preference_decisions["decision"] == "REJECTED").sum()),
        "violations": int(violations.shape[0]),
        "files": sorted([p.name for p in OUT_DIR.iterdir() if p.is_file()]),
    }
    (OUT_DIR / "run_summary.mock.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period-start", default="2026-02-08")
    parser.add_argument("--period-end", default="2026-03-31")
    parser.add_argument("--anchor-scale-id", type=int, default=1)
    parser.add_argument("--sector-id", default="CAIXA", help="Target sector ID (must match policy)")
    args = parser.parse_args()

    context = ProjectionContext(
        period_start=parse_date(args.period_start),
        period_end=parse_date(args.period_end),
        anchor_scale_id=args.anchor_scale_id,
        sector_id=args.sector_id,
    )
    summary = run(context)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
