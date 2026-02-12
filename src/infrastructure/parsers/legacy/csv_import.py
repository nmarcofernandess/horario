
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

class LegacyCSVImporter:
    """
    Importer de fixtures CSV para seed e UI de Regras.
    Padrão: data/fixtures/
    """
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def load_shift_catalog(self) -> pd.DataFrame:
        """
        Loads the catalog of shift definitions (CAI1, CAI2, etc) per day.
        Source: pdf_rita1_shift_catalog_by_day.csv
        """
        path = self.data_dir / "pdf_rita1_shift_catalog_by_day.csv"
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)

    def load_base_slots(self) -> pd.DataFrame:
        """
        Loads the standard daily slot assignments (Mosaic).
        Source: pdf_rita1_slots.csv
        """
        path = self.data_dir / "pdf_rita1_slots.csv"
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path)
        # RENAMING for Domain compatibility
        if 'employee_norm' in df.columns:
            df = df.rename(columns={'employee_norm': 'employee_id'})
        elif 'employee' in df.columns:
             df = df.rename(columns={'employee': 'employee_id'})
        return df

    def load_sunday_rotation(self) -> pd.DataFrame:
        """
        Loads the cyclical Sunday rotation rules.
        Source: pdf_rita_sunday_rotation.csv
        """
        path = self.data_dir / "pdf_rita_sunday_rotation.csv"
        if not path.exists():
            return pd.DataFrame()
        # Ensure dates are parsed correctly if needed, but for display string is fine
        df = pd.read_csv(path)
        # RENAMING
        if 'employee_norm' in df.columns:
             df = df.rename(columns={'employee_norm': 'employee_id'})
        elif 'employee' in df.columns:
             df = df.rename(columns={'employee': 'employee_id'})
             
        return df
        
    def load_day_off_matrix(self) -> pd.DataFrame:
        """
        Loads the specific day-off matrix (Folgas).
        Source: dom_folgas_matrix.csv
        """
        path = self.data_dir / "dom_folgas_matrix.csv"
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)
