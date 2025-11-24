import sys
import os
from sqlmodel import Session, select, create_engine

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from domain.analysis import AnalysisDataset
from database import engine

try:
    print("Attempting to query AnalysisDataset...")
    with Session(engine) as session:
        datasets = session.exec(select(AnalysisDataset)).all()
        print(f"Successfully fetched {len(datasets)} datasets.")
        for d in datasets:
            print(d)
except Exception as e:
    print(f"Error querying database: {e}")
    import traceback
    traceback.print_exc()
