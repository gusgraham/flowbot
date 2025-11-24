from database import engine
from sqlmodel import Session, select
from domain.auth import User

session = Session(engine)
users = session.exec(select(User)).all()

print(f"Total users in database: {len(users)}")
for user in users:
    print(f"  - {user.username} ({user.email}) - Active: {user.is_active}")

session.close()
