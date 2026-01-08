import os
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import event
from domain import admin, auth, fsm, fsa, wq, verification, interim, ssd

# SQLite database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flowbot.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False, "timeout": 30})

# Enable foreign key enforcement for SQLite (required for CASCADE delete to work)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def SessionLocal():
    """Create a new session for background tasks"""
    return Session(engine)
