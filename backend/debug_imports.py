
import sys
import os

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Attempting imports...")
try:
    from services.ingestion import IngestionService
    print("IngestionService imported.")
except Exception as e:
    print(f"FAILED to import IngestionService: {e}")

try:
    from services.timeseries import TimeSeriesService
    print("TimeSeriesService imported.")
except Exception as e:
    print(f"FAILED to import TimeSeriesService: {e}")

print("Import check done.")
