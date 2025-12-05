from database import engine
from sqlmodel import SQLModel
import domain.auth
import domain.fsm
import domain.fsa
import domain.wq
import domain.verification

print("Creating all tables with new schema...")
SQLModel.metadata.create_all(engine)

print("Database schema created successfully!")
print("All tables created with the latest model definitions.")
