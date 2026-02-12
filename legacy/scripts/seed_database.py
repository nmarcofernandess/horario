from datetime import date
from src.infrastructure.database.setup import init_db, SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import Employee, PreferenceRequest, RequestType

def seed():
    print("Initializing Database...")
    init_db()
    
    session = SessionLocal()
    repo = SqlAlchemyRepository(session)
    
    # 1. Sector
    print("Seeding Sector: CAIXA")
    repo.add_sector("CAIXA", "Frente de Caixa")
    
    # 2. Contracts
    print("Seeding Contracts...")
    repo.add_contract("H44_CAIXA", "CAIXA", 2640) # 44h
    repo.add_contract("H36_CAIXA", "CAIXA", 2160) # 36h
    repo.add_contract("H30_CAIXA", "CAIXA", 1800) # 30h
    
    # 3. Employees (Cleonice & Co.)
    print("Seeding Employees...")
    meta = {
        "CLE": {"name": "CLEONICE", "contract_code": "H44_CAIXA", "rank": 1},
        "ANJ": {"name": "ANA JULIA", "contract_code": "H44_CAIXA", "rank": 2},
        "GAB": {"name": "GABRIEL", "contract_code": "H36_CAIXA", "rank": 3},
        "ALI": {"name": "ALICE", "contract_code": "H30_CAIXA", "rank": 4},
        "MAY": {"name": "MAYUMI", "contract_code": "H30_CAIXA", "rank": 5},
        "HEL": {"name": "HELOISA", "contract_code": "H30_CAIXA", "rank": 6},
    }
    
    for eid, info in meta.items():
        repo.add_employee(Employee(
            employee_id=eid,
            name=info["name"],
            contract_code=info["contract_code"],
            sector_id="CAIXA",
            rank=info["rank"]
        ))
        
    print("Database Seeded Successfully!")
    session.close()

if __name__ == "__main__":
    seed()
