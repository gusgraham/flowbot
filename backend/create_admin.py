from database import engine
from sqlmodel import Session
from domain.auth import User
from services.auth import AuthService
from repositories.auth import UserRepository

session = Session(engine)
auth_service = AuthService()

repo = UserRepository(session)
existing = repo.get_by_username("admin@flowbot.com")

if not existing:
    hashed = auth_service.get_password_hash("admin123")
    user = User(
        username="admin@flowbot.com",
        email="admin@flowbot.com",
        hashed_password=hashed,
        full_name="Admin User",
        role="Admin",
        is_superuser=True
    )
    session.add(user)
    session.commit()
    print("✓ User created successfully!")
else:
    print("✓ User already exists!")

session.close()
