"""Seed canônico a partir de JSON único (preset Supermercado Fernandes)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from apps.backend.src.domain.models import (
    DemandSlot,
    Employee,
    ExceptionType,
    PreferenceRequest,
    RequestType,
    ScheduleException,
)
from apps.backend.src.infrastructure.database.setup import SessionLocal, init_db
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository


ROOT = Path(__file__).resolve().parents[1]
SEED_JSON_PATH = ROOT / "data" / "fixtures" / "seed_supermercado_fernandes.json"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"


def _load_seed_data(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Seed JSON não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_governance_policy_patch(seed_data: dict) -> None:
    patch = seed_data.get("governance_policy_patch", {})
    if not patch:
        return
    policy_data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    for section in ("jurisdiction", "constraints", "picking_rules"):
        incoming = patch.get(section)
        if not isinstance(incoming, dict):
            continue
        base = policy_data.setdefault(section, {})
        if isinstance(base, dict):
            base.update(incoming)
        else:
            policy_data[section] = incoming

    POLICY_PATH.write_text(
        json.dumps(policy_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def seed_everything(seed_path: Path = SEED_JSON_PATH) -> None:
    seed_data = _load_seed_data(seed_path)
    print(f"Populando banco a partir de JSON único: {seed_path}")
    init_db()
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)

    try:
        sector = seed_data["sector"]
        sector_id = str(sector["sector_id"])
        repo.add_sector(sector_id, str(sector["name"]))

        print("- Contratos...")
        for contract in seed_data.get("contracts", []):
            repo.add_contract(
                str(contract["contract_code"]),
                sector_id,
                int(contract["weekly_minutes"]),
            )

        print("- Colaboradores...")
        for employee in seed_data.get("employees", []):
            repo.add_employee(
                Employee(
                    employee_id=str(employee["employee_id"]).upper(),
                    name=str(employee["name"]),
                    contract_code=str(employee["contract_code"]),
                    sector_id=sector_id,
                    rank=int(employee.get("rank", 99)),
                    tags=[str(tag) for tag in employee.get("tags", [])],
                    active=bool(employee.get("active", True)),
                )
            )

        print("- Turnos...")
        shifts_df = pd.DataFrame(seed_data.get("shifts", []))
        if not shifts_df.empty:
            repo.save_shifts(shifts_df, sector_id=sector_id)

        print("- Mosaico semanal...")
        template_df = pd.DataFrame(seed_data.get("weekday_template", []))
        if not template_df.empty:
            repo.save_weekday_template(template_df, sector_id=sector_id)

        print("- Rodízio de domingos...")
        rotation_df = pd.DataFrame(seed_data.get("sunday_rotation", []))
        if not rotation_df.empty:
            rotation_df["sunday_date"] = pd.to_datetime(rotation_df["sunday_date"]).dt.date
            rotation_df["folga_date"] = pd.to_datetime(rotation_df["folga_date"]).dt.date
            repo.save_sunday_rotation(rotation_df, sector_id=sector_id)

        print("- Preferências...")
        for pref in seed_data.get("preference_requests", []):
            repo.add_preference(
                PreferenceRequest(
                    request_id=str(pref["request_id"]),
                    employee_id=str(pref["employee_id"]).upper(),
                    request_date=date.fromisoformat(str(pref["request_date"])),
                    request_type=RequestType(str(pref["request_type"])),
                    priority=str(pref.get("priority", "MEDIUM")).upper(),
                    target_shift_code=pref.get("target_shift_code"),
                    note=str(pref.get("note", "")),
                )
            )

        print("- Exceções...")
        for exc in seed_data.get("exceptions", []):
            repo.add_exception(
                ScheduleException(
                    sector_id=str(exc.get("sector_id", sector_id)),
                    employee_id=str(exc["employee_id"]).upper(),
                    exception_date=date.fromisoformat(str(exc["exception_date"])),
                    exception_type=ExceptionType(str(exc["exception_type"])),
                    note=str(exc.get("note", "")),
                )
            )

        print("- Demand profile...")
        for slot in seed_data.get("demand_slots", []):
            repo.add_demand_slot(
                DemandSlot(
                    sector_id=str(slot.get("sector_id", sector_id)),
                    work_date=date.fromisoformat(str(slot["work_date"])),
                    slot_start=str(slot["slot_start"]),
                    min_required=int(slot["min_required"]),
                )
            )

        print("- Patch de governança/policy...")
        _apply_governance_policy_patch(seed_data)

        print(
            f"Concluído: {len(seed_data.get('employees', []))} colaboradores, "
            f"{len(seed_data.get('shifts', []))} turnos, "
            f"{len(seed_data.get('weekday_template', []))} slots de mosaico e "
            f"{len(seed_data.get('sunday_rotation', []))} entradas de rodízio."
        )
    finally:
        session.close()


if __name__ == "__main__":
    seed_everything()
