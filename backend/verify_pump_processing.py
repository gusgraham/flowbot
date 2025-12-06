
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from sqlmodel import Session, select, SQLModel

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from domain.fsm import FsmProject, Install, TimeSeries, RawDataSettings
from services.processing import ProcessingService
from infra.storage import StorageService
import random
import string

def get_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def verify_pump_processing():
    print("Starting Pump Logger Processing Verification...")
    
    SQLModel.metadata.create_all(engine)
    
    run_id = get_random_string()
    
    with Session(engine) as session:
        # 1. Setup Data
        project = FsmProject(name=f"Test Pump Project {run_id}", client="Test Client", job_number=f"J{run_id}")
        session.add(project)
        session.commit()
        session.refresh(project)
        
        install = Install(
            install_id=f"PUMP-{run_id}",
            project_id=project.id,
            install_type="Pump Logger",
            install_date=datetime(2024, 1, 1)
        )
        session.add(install)
        session.commit()
        session.refresh(install)
        
        # 2. Configure Settings
        # Timing correction: +60 minutes (1 hour) starting from 12:00
        # Frontend sends 'datetime' and 'offset' (minutes)
        timing_json = json.dumps([
            {"datetime": "2024-01-01 12:00:00", "offset": 60, "comment": "Shift forward 1 hour"}
        ])
        
        # Added event: Force ON at 14:00 (which is outside original range + shift)
        # Frontend sends 'datetime' and 'state' (ON/OFF)
        added_json = json.dumps([
            {"datetime": "2024-01-01 14:00:00", "state": "ON", "comment": "Force ON event"}
        ])
        
        settings = RawDataSettings(
            install_id=install.id,
            pl_timing_corr=timing_json,
            pl_added_onoffs=added_json
        )
        session.add(settings)
        session.commit()
        
        # 3. Create Raw Data
        # 12:00 to 13:00. Value 0.
        dates = pd.date_range(start='2024-01-01 12:00:00', end='2024-01-01 13:00:00', freq='15min')
        # existing timestamps: 12:00, 12:15, 12:30, 12:45, 13:00
        # After correction (+1h): 13:00, 13:15, 13:30, 13:45, 14:00
        
        # Wait, if I start at 12:00, and correction applies >= 12:00.
        # All points should shift.
        
        vals = np.zeros(len(dates))
        
        df = pd.DataFrame({'time': dates, 'value': vals})
        
        storage = StorageService()
        path = f"timeseries/installs/{install.id}/Pump_State_Raw.parquet"
        storage.save_parquet(path, df)
        
        ts = TimeSeries(
            install_id=install.id,
            variable="Pump_State",
            data_type="Raw",
            filename=path,
            start_time=dates[0],
            end_time=dates[-1],
            unit="",
            interval_minutes=15
        )
        session.add(ts)
        session.commit()
        
        # 4. Run Processing
        print(f"Processing Install {install.id}...")
        service = ProcessingService(session, storage)
        service.process_install(install.id)
        
        # 5. Verify
        # Fetch processed series
        proc_ts = session.exec(select(TimeSeries).where(
            TimeSeries.install_id == install.id, 
            TimeSeries.variable == 'Pump_State',
            TimeSeries.data_type == 'Processed'
        )).first()
        
        if not proc_ts:
            print("FAILURE: No processed TimeSeries found.")
            return

        print(f"Processed file: {proc_ts.filename}")
        df_proc = storage.read_parquet(proc_ts.filename)
        print("Processed Data:")
        print(df_proc)
        
        # Checks
        # 1. Check Shift
        # First point was originally 12:00. Should now be 13:00.
        first_time = pd.to_datetime(df_proc['time'].iloc[0])
        print(f"First timestamp: {first_time}")
        if first_time == pd.Timestamp("2024-01-01 13:00:00"):
            print("SUCCESS: Timing correction applied.")
        else:
            print(f"FAILURE: Expected 13:00, got {first_time}")
            
        # 2. Check Added Event
        # Look for 14:00 with value 1
        # Original last point was 13:00 -> 14:00 (value 0)
        # Added point is 14:00 (value 1).
        # Since we append and sort, and we have duplicates at 14:00 ?? 
        # (One from shifted 13:00->14:00 which was 0, one from added event which is 1)
        # Let's see what happens.
        
        matches = df_proc[df_proc['time'] == pd.Timestamp("2024-01-01 14:00:00")]
        print("Points at 14:00:")
        print(matches)
        
        if len(matches) > 0 and 1 in matches['value'].values:
             print("SUCCESS: Added Event found.")
        else:
             print("FAILURE: Added Event not found or value mismatch.")

if __name__ == "__main__":
    verify_pump_processing()
