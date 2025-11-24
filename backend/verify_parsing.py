import sys
import os

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from services.importers import import_fdv_file

file_path = r"data/analysis/1/F0001.fdv"

try:
    print(f"Attempting to parse {file_path}...")
    if not os.path.exists(file_path):
        print("File does not exist!")
        sys.exit(1)
        
    data = import_fdv_file(file_path)
    print("Successfully parsed file!")
    print(f"Name: {data.get('name')}")
    print(f"Type: {data.get('type')}")
    print(f"Data points: {len(data.get('data', {}).get('flow', []))}")
    
except Exception as e:
    print(f"Error parsing file: {e}")
    import traceback
    traceback.print_exc()
