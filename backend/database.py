import os
from sqlmodel import create_engine, SQLModel, Session
from domain import auth, fsm, fsa, wq, verification, interim, ssd

# SQLite database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flowbot.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False, "timeout": 30})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def SessionLocal():
    """Create a new session for background tasks"""
    return Session(engine)
