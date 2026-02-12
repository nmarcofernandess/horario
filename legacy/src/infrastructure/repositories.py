import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, date

from src.domain.models import Employee, PreferenceRequest, RequestType

class FileSystemRepository:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        # Hardcoded metadata from mock script for now
        self.EMPLOYEE_META = {
            "CLE": {"name": "CLEONICE", "contract_code": "H44_CAIXA", "rank": 1},
            "ANJ": {"name": "ANA JULIA", "contract_code": "H44_CAIXA", "rank": 2},
            "GAB": {"name": "GABRIEL", "contract_code": "H36_CAIXA", "rank": 3},
            "ALI": {"name": "ALICE", "contract_code": "H30_CAIXA", "rank": 4},
            "MAY": {"name": "MAYUMI", "contract_code": "H30_CAIXA", "rank": 5},
            "HEL": {"name": "HELOISA", "contract_code": "H30_CAIXA", "rank": 6},
        }

    def load_employees(self) -> Dict[str, Employee]:
        employees = {}
        for eid, meta in self.EMPLOYEE_META.items():
            employees[eid] = Employee(
                employee_id=eid,
                name=meta["name"],
                contract_code=meta["contract_code"],
                sector_id="CAIXA", # Default for pilot
                rank=meta.get("rank", 999),
                active=True
            )
        return employees

    def load_sunday_rotation(self) -> pd.DataFrame:
        file_path = self.data_path / "xlsx_caixas_sunday_rotation.csv"
        if not file_path.exists():
            return pd.DataFrame()
        df = pd.read_csv(file_path)
        
        # Mapping Name -> ID
        name_to_id = { meta["name"]: eid for eid, meta in self.EMPLOYEE_META.items() }
        
        # Assumption: input CSV has 'employee_norm' column with names like "CLEONICE"
        if "employee_norm" in df.columns:
            df["employee_id"] = df["employee_norm"].map(name_to_id)
            # Filter unknowns
            df = df[df["employee_id"].notna()].copy()
        else:
            print("Warning: 'employee_norm' column missing in sunday rotation CSV.")
            
        return df

    def load_preferences(self) -> List[PreferenceRequest]:
        # Mocking preferences as per the script, 
        # or we could read from a JSON/CSV if we had one.
        # For this refactor, I will embed the mock data generator here
        # to ensure the same behavior as the script.
        
        rows = [
            {
                "request_id": "REQ-001", "employee_id": "GAB", "request_date": "2026-02-15",
                "request_type": "AVOID_SUNDAY_DATE", "priority": "HIGH", "note": "Evento familiar"
            },
            {
                "request_id": "REQ-002", "employee_id": "HEL", "request_date": "2026-02-17",
                "request_type": "SHIFT_CHANGE_ON_DATE", "priority": "MEDIUM", "target_shift_code": "CAI5"
            },
            {
                "request_id": "REQ-003", "employee_id": "ALI", "request_date": "2026-02-11",
                "request_type": "FOLGA_ON_DATE", "priority": "HIGH", "note": "Consulta medica"
            },
            {
                "request_id": "REQ-004", "employee_id": "MAY", "request_date": "2026-02-24",
                "request_type": "SHIFT_CHANGE_ON_DATE", "priority": "LOW", "target_shift_code": "CAI6"
            },
            {
                "request_id": "REQ-005", "employee_id": "CLE", "request_date": "2026-02-27",
                "request_type": "FOLGA_ON_DATE", "priority": "HIGH", "note": "Compromisso pessoal"
            },
            {
                "request_id": "REQ-006", "employee_id": "ANJ", "request_date": "2026-03-03",
                "request_type": "SHIFT_CHANGE_ON_DATE", "priority": "MEDIUM", "target_shift_code": "CAI2"
            },
        ]
        
        reqs = []
        for r in rows:
            reqs.append(PreferenceRequest(
                request_id=r["request_id"],
                employee_id=r["employee_id"],
                request_date=datetime.strptime(r["request_date"], "%Y-%m-%d").date(),
                request_type=RequestType(r["request_type"]),
                priority=r["priority"],
                target_shift_code=r.get("target_shift_code"),
                note=r.get("note", "")
            ))
        return reqs

    def load_weekday_template_data(self) -> pd.DataFrame:
        # returns the totals dataframe used to infer shifts
        return pd.read_csv(self.data_path / "pdf_rita1_totals.csv")
