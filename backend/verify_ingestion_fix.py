
import sys
import os
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select, create_engine, SQLModel

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from domain.fsm import TimeSeries
from services.timeseries import TimeSeriesService
import random
import string

def get_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def verify_ingestion_fix():
    print("Verifying Ingestion Fix...")
    
    SQLModel.metadata.create_all(engine)
    
    run_id = get_random_string()
    install_id = 99999 + random.randint(1, 1000)
    monitor_id = 88888 + random.randint(1, 1000)
    
    with Session(engine) as session:
        service = TimeSeriesService(session)
        
        # Create dummy data
        df = pd.DataFrame({
            'time': [datetime(2024, 1, 1, 12, 0), datetime(2024, 1, 1, 12, 15)],
            'value': [1.0, 1.1]
        })
        
        print(f"Saving dataframe for Install {install_id}, Monitor {monitor_id}...")
        
        # Call save_dataframe with new args
        ts = service.save_dataframe(
            df, 
            install_id, 
            "Depth", 
            data_type="Raw", 
            monitor_id=monitor_id, 
            unit="m"
        )
        
        print(f"Created TimeSeries ID: {ts.id}")
        
        # Verify fields
        if ts.monitor_id != monitor_id:
            print(f"FAILURE: monitor_id mismatch. Expected {monitor_id}, got {ts.monitor_id}")
        else:
            print("SUCCESS: monitor_id saved correctly.")
            
        if ts.unit != "m":
            print(f"FAILURE: unit mismatch. Expected 'm', got {ts.unit}")
        else:
            print("SUCCESS: unit saved correctly.")
            
        # Verify Filename formatting
        print(f"Saved Filename: {ts.filename}")
        if "data/fsm" in ts.filename:
            print("FAILURE: Filename contains redundant 'data/fsm' prefix.")
        elif os.path.isabs(ts.filename):
             print("FAILURE: Filename is absolute.")
        elif ts.filename.startswith("timeseries/installs/"):
             print("SUCCESS: Filename appears relative and correct.")
        else:
             print("WARNING: Filename format unexpected, check manually.")

if __name__ == "__main__":
    verify_ingestion_fix()
