import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import event
# Import domain models to ensure they are registered with SQLModel
from domain import admin, auth, fsm, fsa, wq, verification, interim, ssd

# Load environment variables from .env file
load_dotenv()

# Get DB URL from env, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flowbot.db")

# Configure engine args based on DB type
# Configure engine args based on DB type
# Configure engine args based on DB type
connect_args = {}
db_schema = os.getenv("DB_SCHEMA")

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
elif DATABASE_URL.startswith("postgresql") and db_schema:
    connect_args = {"options": f"-c search_path={db_schema}"}

# Create engine
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

# Apply DB-specific configurations
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

elif DATABASE_URL.startswith("postgresql") and db_schema:
    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Create schema if it doesn't exist
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {db_schema}")
        # Ensure search path is set for this connection
        cursor.execute(f"SET search_path TO {db_schema}")
        cursor.close()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def SessionLocal():
    """Create a new session for background tasks"""
    return Session(engine)
