from sqlmodel import Session, select, SQLModel
from database import engine, create_db_and_tables
from domain.fsa import FsaProject

print("Initializing DB...")
try:
    create_db_and_tables()
    print("Tables created (if they didn't exist).")
except Exception as e:
    print(f"Error creating tables: {e}")

print("Testing Query...")
try:
    with Session(engine) as session:
        projects = session.exec(select(FsaProject)).all()
        print(f"Projects found: {len(projects)}")
except Exception as e:
    print(f"Error querying projects: {e}")
