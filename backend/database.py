from sqlmodel import create_engine, SQLModel, Session
from domain import project, monitor, events, auth, visit, qa, fsm, fsa

# SQLite database URL
DATABASE_URL = "sqlite:///./flowbot.db"

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
