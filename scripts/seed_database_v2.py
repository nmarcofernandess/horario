import pandas as pd
from pathlib import Path
from src.infrastructure.database.setup import init_db, SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import Employee

ROOT = Path(__file__).resolve().parents[1]
EXCEL_RAW_DIR = ROOT / "data" / "processed" / "excel_raw" / "horario_de_trabalho_padrao_novo_2026_revisao_de_escala"

BLACKLISTED_SHEETS = [
    "parametros", "cargos", "setores", "resumo_dep", "resumo_func", "planilha1"
]

def load_and_seed_v2():
    print("Initializing Database...")
    init_db()
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)
    
    print(f"Scanning {EXCEL_RAW_DIR}...")
    
    # 1. Iterate over CSVs
    files = list(EXCEL_RAW_DIR.glob("*.csv"))
    
    for f in files:
        if f.stem in BLACKLISTED_SHEETS:
            continue
            
        sector_slug = f.stem.upper().replace("_", " ").replace("2026", "").replace("2025", "").replace("ESC", "").strip()
        print(f"Processing Sector: {sector_slug} from {f.name}...")
        
        # Add Sector
        repo.add_sector(sector_slug, sector_slug)
        
        # Parse Employees
        try:
            df = pd.read_csv(f, header=None) # Raw read to find structure
            
            # Heuristic: Find column "NOME"
            col_name_idx = -1
            
            # Scan first 20 rows for "NOME" cell
            for r_idx in range(min(50, len(df))):
                for c_idx in range(len(df.columns)):
                    val = str(df.iloc[r_idx, c_idx]).strip().upper()
                    if val == "NOME":
                        col_name_idx = c_idx
                        break
                if col_name_idx != -1:
                    break
            
            if col_name_idx != -1:
                # Extract names from that column downwards
                # We assume names are strings, uppercase, len > 3, exclude numbers/dates.
                raw_names = df.iloc[r_idx+1:, col_name_idx].dropna().unique()
                
                valid_names = []
                for n in raw_names:
                    s = str(n).strip().upper()
                    # Filter noise
                    if len(s) < 3 or s.replace(":","").isdigit() or "00:00" in s or "TOTAL" in s:
                        continue
                    valid_names.append(s)
                
                valid_names = sorted(list(set(valid_names)))
                print(f"  > Found {len(valid_names)} employees: {valid_names[:5]}...")
                
                count = 0
                for name in valid_names:
                    # Create generic emp code: FIRST3 + SEC3
                    sec_prefix = sector_slug[:3].replace(" ", "X")
                    name_prefix = name[:3].replace(" ", "X")
                    emp_id = f"{sec_prefix}-{name_prefix}-{count:02d}"
                    count += 1
                    
                    repo.add_employee(Employee(
                        employee_id=emp_id,
                        name=name,
                        contract_code="H44_CAIXA", # Default for now
                        sector_id=sector_slug,
                        rank=999
                    ))
            else:
                print("  ! Column 'NOME' not found.")
                
        except Exception as e:
            print(f"  ! Error reading {f.name}: {e}")
            
    session.close()
    print("Seed V2 Complete.")

if __name__ == "__main__":
    load_and_seed_v2()
