import sys
import os

# Add backend directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Attempting to import services.analysis...")
    from services import analysis
    print("Successfully imported services.analysis")
except Exception as e:
    print(f"Error importing services.analysis: {e}")
    import traceback
    traceback.print_exc()
