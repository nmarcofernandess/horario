
import pandas as pd
from pathlib import Path
from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter
from src.domain.models import Employee

def seed_everything():
    print("🌱 Iniciando População Safada via CSV Legacy...")
    init_db()
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)
    
    DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
    importer = LegacyCSVImporter(DATA_DIR)
    
    # 1. Sectors & Contracts (Mocked based on CAIXA)
    print("- Criando Setores e Contratos...")
    repo.add_sector("CAIXA", "Setor de Caixas")
    repo.add_contract("CLT_44H", "CAIXA", 2640)
    
    # 2. Employees (from slots + rotation para cobrir todos)
    print("- Cadastrando Funcionários...")
    df_slots = importer.load_base_slots()
    df_rot = importer.load_sunday_rotation()
    unique_emps = set()
    if not df_slots.empty:
        unique_emps.update(df_slots['employee_id'].dropna().astype(str).unique().tolist())
    if not df_rot.empty and 'employee_id' in df_rot.columns:
        unique_emps.update(df_rot['employee_id'].dropna().astype(str).unique().tolist())
    for emp_name in sorted(unique_emps):
        if emp_name and len(emp_name) > 2:
            repo.add_employee(Employee(
                employee_id=emp_name,
                name=emp_name,
                contract_code="CLT_44H",
                sector_id="CAIXA",
                rank=999,
                active=True
            ))
            
    # 3. Shifts
    print("- Populando Catálogo de Turnos...")
    df_shifts = importer.load_shift_catalog()
    if not df_shifts.empty:
        df_shifts = df_shifts.drop_duplicates("shift_code").copy()
    if "day_scope" not in df_shifts.columns and not df_shifts.empty:
        df_shifts["day_scope"] = "WEEKDAY"
    sunday_row = pd.DataFrame([{
        "shift_code": "DOM_08_12_30",
        "minutes_median": 270,
        "day_scope": "SUNDAY"
    }])
    df_shifts = pd.concat([df_shifts, sunday_row]) if not df_shifts.empty else sunday_row
    repo.save_shifts(df_shifts)
        
    # 4. Weekday Template (Mosaic/Slots)
    print("- Populando Mosaico Base...")
    if not df_slots.empty:
        # We need to ensure we don't have duplicates for (emp, day) 
        # in the template used by DB CycleTemplateORM
        df_tpl = df_slots.drop_duplicates(['employee_id', 'day_name'])
        repo.save_weekday_template(df_tpl)
        
    # 5. Sunday Rotations
    print("- Populando Ciclos de Domingo...")
    df_rot = importer.load_sunday_rotation()
    if not df_rot.empty:
        repo.save_sunday_rotation(df_rot)
        
    print("✅ População Concluída! Banco local pronto para uso.")
    session.close()

if __name__ == "__main__":
    seed_everything()
