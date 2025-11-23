import pandas as pd
import io
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session
from domain.events import TimeSeries
from repositories.timeseries import TimeSeriesRepository
from infra.storage import StorageService

class TimeSeriesService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = TimeSeriesRepository(session)
        self.storage = StorageService()

    def process_upload(self, install_id: int, file_path: str, original_filename: str) -> List[TimeSeries]:
        """
        Parses a CSV file, converts to Parquet, and creates TimeSeries records.
        Assumes CSV format: Date, Flow, Depth, Velocity
        """
        # 1. Read CSV
        # In a real app, we'd need robust CSV parsing (skip rows, flexible columns)
        # For now, we assume a clean standard format
        try:
            df = pd.read_csv(file_path)
            
            # Standardize columns
            # Expected: Date, Flow, Depth, Velocity
            # Map common variations if needed
            
            if 'Date' not in df.columns:
                # Try to find date column or raise error
                raise ValueError("CSV must have a 'Date' column")
                
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df = df.sort_values('Date')
            
            start_time = df['Date'].iloc[0].to_pydatetime()
            end_time = df['Date'].iloc[-1].to_pydatetime()
            
            # Calculate interval (mode of diff)
            interval = int(df['Date'].diff().mode()[0].total_seconds() / 60)
            
            created_records = []
            
            # 2. Process each variable (Flow, Depth, Velocity)
            for col in ['Flow', 'Depth', 'Velocity']:
                if col in df.columns:
                    # Extract series
                    series_df = df[['Date', col]].copy()
                    series_df.columns = ['time', 'value']
                    
                    # Save as Parquet
                    parquet_filename = f"{original_filename}_{col}.parquet"
                    # We use a temporary buffer to write parquet, then pass to storage
                    # But storage expects bytes. 
                    # Pandas to_parquet can write to BytesIO
                    buf = io.BytesIO()
                    series_df.to_parquet(buf, index=False)
                    buf.seek(0)
                    
                    saved_path = self.storage.save_file(
                        buf.getvalue(), 
                        parquet_filename, 
                        subfolder=f"timeseries/{install_id}"
                    )
                    
                    # 3. Create TimeSeries record
                    ts = TimeSeries(
                        install_id=install_id,
                        variable=col,
                        data_type="Raw",
                        start_time=start_time,
                        end_time=end_time,
                        interval_minutes=interval,
                        filename=saved_path
                    )
                    created_records.append(self.repo.create(ts))
            
            return created_records
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            raise e

    def list_by_install(self, install_id: int) -> List[TimeSeries]:
        return self.repo.list_by_install(install_id)
