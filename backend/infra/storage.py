import os
import shutil
from pathlib import Path

class StorageService:
    def __init__(self, base_path: str = "data_store"):
        self.base_path = Path(base_path)
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
