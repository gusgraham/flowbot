from database import engine
from sqlmodel import SQLModel
import domain.project
import domain.monitor
import domain.fsm
import domain.qa
import domain.analysis
import domain.wq
import domain.auth

print("Dropping all tables...")
SQLModel.metadata.drop_all(engine)

print("Creating all tables with updated schema...")
SQLModel.metadata.create_all(engine)

print("Database schema updated successfully!")
print("All tables recreated with the latest model definitions.")
