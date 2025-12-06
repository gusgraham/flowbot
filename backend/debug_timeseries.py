
import sys
import os
from sqlmodel import Session, select, create_engine

# Add current dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from domain.fsm import TimeSeries

def check_timeseries_variables():
    print("Checking TimeSeries variables...")
    with Session(engine) as session:
        records = session.exec(select(TimeSeries)).all()
        for ts in records:
            print(f"ID: {ts.id}, Install: {ts.install_id}, Type: {ts.data_type}, Variable: '{ts.variable}'")

if __name__ == "__main__":
    check_timeseries_variables()
