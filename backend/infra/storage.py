import os
import shutil
from pathlib import Path
import pandas as pd

class StorageService:
    def __init__(self, base_path: str = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Default to backend/data/fsm relative to this file
            # This file is in backend/infra/storage.py
            # We want backend/data/fsm
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.base_path = current_dir.parent / "data" / "fsm"
            
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, content: bytes, filename: str, subfolder: str = "") -> str:
        folder = self.base_path / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        
        file_path = folder / filename
        with open(file_path, "wb") as f:
            f.write(content)
            
        return str(file_path)

    def get_file_path(self, filename: str, subfolder: str = "") -> str:
        return str(self.base_path / subfolder / filename)

    def read_parquet(self, relative_path: str) -> pd.DataFrame:
        """Read parquet file from storage."""
        # Check if path is absolute or relative to base
        # If relative_path starts with data/fsm, strip it? 
        # Or assume relative_path is relative to working dir?
        # The ProcessingService passed: timeseries/installs/{id}/filename
        # Logic: 
        # If relative_path is 'timeseries/installs/...', join with base_path?
        # But base_path is 'data/fsm'. 
        
        # Let's handle both relative within base and relative from root
        p = Path(relative_path)
        if not p.is_absolute():
            # Check if it exists as is (relative to CWD)
            if p.exists():
                return pd.read_parquet(p)
            
            # Try joining with base path
            full_path = self.base_path / relative_path
            if full_path.exists():
                 return pd.read_parquet(full_path)
                 
        return pd.read_parquet(relative_path)

    def save_parquet(self, relative_path: str, df: pd.DataFrame):
        """Save dataframe as parquet."""
        full_path = self.base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(full_path, index=False)

