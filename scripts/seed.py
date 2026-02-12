"""
Seed do banco a partir dos dados processados (fixtures).
Extrai colaboradores, turnos, mosaico e rodízio de domingos.
Formato agradável: nomes em maiúsculas, siglas, contratos legíveis.
"""

import pandas as pd
from pathlib import Path
from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter
from src.domain.models import Employee

# Alias para normalizar variantes de nome (ex: MAYUME -> MAYUMI)
NAME_ALIASES = {"MAYUME": "MAYUMI", "MAYUMEI": "MAYUMI"}

# Mapeamento nome cru -> formato agradável (titulo)
def _nome_agradavel(nome: str) -> str:
    """Converte ALICE -> Alice, ANA JULIA -> Ana Julia."""
    if not nome or len(nome) < 2:
        return nome
    n = NAME_ALIASES.get(nome.upper(), nome.upper())
    return " ".join(p.capitalize() for p in n.split())


def _sigla(nome: str) -> str:
    """Gera sigla de 3 letras: ALICE -> ALI, ANA JULIA -> ANJ."""
    n = nome.upper().replace(" ", "")
    if len(n) <= 3:
        return n
    if "JULIA" in nome.upper():
        return "ANJ"  # Ana Julia
    return n[:3]


def seed_everything():
    print("Populando banco a partir de data/fixtures/")
    init_db()
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)

    DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
    importer = LegacyCSVImporter(DATA_DIR)

    # 1. Setores e Contratos
    print("- Setores e contratos...")
    repo.add_sector("CAIXA", "Caixa")
    for code, mins in [("H44_CAIXA", 2640), ("H36_CAIXA", 2160), ("H30_CAIXA", 1800), ("CLT_44H", 2640)]:
        repo.add_contract(code, "CAIXA", mins)

    # 2. Colaboradores (slots + rotação, formato agradável)
    print("- Colaboradores...")
    df_slots = importer.load_base_slots()
    df_rot = importer.load_sunday_rotation()

    unique_raw = set()
    if not df_slots.empty:
        unique_raw.update(df_slots["employee_id"].dropna().astype(str).str.strip().unique().tolist())
    if not df_rot.empty and "employee_id" in df_rot.columns:
        unique_raw.update(df_rot["employee_id"].dropna().astype(str).str.strip().unique().tolist())

    # Normalizar aliases e ordenar
    seen = set()
    for raw in sorted(unique_raw):
        if not raw or len(raw) < 2:
            continue
        canônico = NAME_ALIASES.get(raw.upper(), raw.upper())
        if canônico in seen:
            continue
        seen.add(canônico)

        nome = _nome_agradavel(canônico)
        repo.add_employee(Employee(
            employee_id=canônico,
            name=nome,
            contract_code="H44_CAIXA",
            sector_id="CAIXA",
            rank=99,
            active=True,
        ))

    # 3. Turnos
    print("- Turnos...")
    df_shifts = importer.load_shift_catalog()
    if not df_shifts.empty:
        df_shifts = df_shifts.drop_duplicates("shift_code").copy()
    if "day_scope" not in df_shifts.columns and not df_shifts.empty:
        df_shifts["day_scope"] = "WEEKDAY"
    sunday_row = pd.DataFrame([{"shift_code": "DOM_08_12_30", "minutes_median": 270, "day_scope": "SUNDAY"}])
    df_all = pd.concat([df_shifts, sunday_row]) if not df_shifts.empty else sunday_row
    repo.save_shifts(df_all)

    # 4. Mosaico semanal
    print("- Mosaico...")
    if not df_slots.empty:
        df_tpl = df_slots.drop_duplicates(["employee_id", "day_name"]).copy()
        df_tpl["employee_id"] = df_tpl["employee_id"].str.strip().apply(
            lambda x: NAME_ALIASES.get(str(x).upper(), str(x).upper()) if pd.notna(x) else x
        )
        repo.save_weekday_template(df_tpl)

    # 5. Rodízio de domingos (normalizar employee_id para canônico)
    print("- Rodízio de domingos...")
    if not df_rot.empty:
        df_rot = df_rot.copy()
        df_rot["employee_id"] = df_rot["employee_id"].str.strip().apply(
            lambda x: NAME_ALIASES.get(str(x).upper(), str(x).upper()) if pd.notna(x) else x
        )
        repo.save_sunday_rotation(df_rot)

    print(f"Concluído: {len(seen)} colaboradores, turnos, mosaico e rodízio.")
    session.close()


if __name__ == "__main__":
    seed_everything()
