
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlmodel import Session, select, create_engine, SQLModel

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from domain.fsm import FsmProject, Site, Monitor, Install, TimeSeries, RawDataSettings
from services.processing import ProcessingService
from infra.storage import StorageService
import random
import string

def get_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def verify_project_processing():
    print("Starting Project Processing Verification...")
    
    SQLModel.metadata.create_all(engine)
    
    run_id = get_random_string()
    
    with Session(engine) as session:
        # 1. Setup Test Data
        # Create Project
        project = FsmProject(
            name=f"Test Processing Project {run_id}",
            client="Test Client",
            job_number=f"J{run_id}",
            default_download_path="C:/Temp/Data"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        print(f"Created Project: {project.id}")
        
        # Create Site
        site = Site(
            site_id=f"SITE-{run_id}",
            project_id=project.id,
            site_type="Flow Monitor"
        )
        session.add(site)
        session.commit()
        session.refresh(site)
        
        # Create Monitor
        monitor = Monitor(
            monitor_asset_id=f"MON-{run_id}",
            project_id=project.id,
            monitor_type="Flow Monitor"
        )
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        
        # Create Install
        install = Install(
            install_id=f"INST-{run_id}",
            project_id=project.id,
            site_id=site.id,
            monitor_id=monitor.id,
            install_type="Flow Monitor",
            install_date=datetime.now() - timedelta(days=7),
            fm_pipe_shape="CIRC",
            fm_pipe_height_mm=300
        )
        session.add(install)
        session.commit()
        session.refresh(install)
        print(f"Created Install: {install.id}")
        
        # 2. Create Raw Data
        # 1 week of data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        depths = np.random.uniform(0.05, 0.25, size=100) # 50mm to 250mm
        velocities = np.random.uniform(0.1, 0.8, size=100) # 0.1 to 0.8 m/s
        
        # Save Parquet
        storage = StorageService()
        
        # Depth
        df_depth = pd.DataFrame({'time': dates, 'value': depths})
        depth_path = f"timeseries/installs/{install.id}/Depth_Raw.parquet"
        storage.save_parquet(depth_path, df_depth)
        
        # Velocity
        df_vel = pd.DataFrame({'time': dates, 'value': velocities})
        vel_path = f"timeseries/installs/{install.id}/Velocity_Raw.parquet"
        storage.save_parquet(vel_path, df_vel)
        
        # 3. Create TimeSeries Records
        ts_depth = TimeSeries(
            install_id=install.id,
            monitor_id=monitor.id,
            variable="Depth",
            data_type="Raw",
            filename=depth_path,
            start_time=dates[0],
            end_time=dates[-1],
            unit="m",
            interval_minutes=15
        )
        ts_vel = TimeSeries(
            install_id=install.id,
            monitor_id=monitor.id,
            variable="Velocity",
            data_type="Raw",
            filename=vel_path,
            start_time=dates[0],
            end_time=dates[-1],
            unit="m/s",
            interval_minutes=15
        )
        session.add(ts_depth)
        session.add(ts_vel)
        session.commit()
        print("Created TimeSeries records and data files.")
        
        # 4. Run Project Processing
        print("Running ProcessingService.process_project...")
        service = ProcessingService(session, storage)
        results = service.process_project(project.id)
        
        print("Results:", results)
        
        # 5. Verify Results
        if results['success'] == 1 and results['failed'] == 0:
            print("SUCCESS: Processing reported success.")
        else:
            print("FAILURE: Processing results mismatch.")
            
        # Check if processed TimeSeries exist
        processed_ts = session.exec(select(TimeSeries).where(
            TimeSeries.install_id == install.id,
            TimeSeries.data_type == 'Processed'
        )).all()
        
        if len(processed_ts) >= 3: # Depth, Velocity, Flow
            print(f"SUCCESS: Found {len(processed_ts)} processed TimeSeries records.")
            for ts in processed_ts:
                print(f" - {ts.variable}: {ts.filename}")
        else:
            print(f"FAILURE: Expected 3 processed TimeSeries, found {len(processed_ts)}")
            
        # Cleanup (Optional - keep for manual inspection if needed)
        # session.delete(install)
        # session.delete(monitor)
        # session.delete(site)
        # session.delete(project)
        # session.commit()

if __name__ == "__main__":
    verify_project_processing()
