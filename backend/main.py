from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from api import fsm, verification, wq, auth, fsa, users
from database import get_session, create_db_and_tables
from domain.auth import User, UserCreate
from services.auth import AuthService
from repositories.auth import UserRepository

app = FastAPI(title="FlowBot Hub")

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(fsm.router, prefix="/api", tags=["fsm"])
app.include_router(fsa.router, prefix="/api")
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(wq.router, prefix="/api", tags=["wq"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Create default user if not exists
    from database import engine
    try:
        with Session(engine) as session:
            user_repo = UserRepository(session)
            existing_user = user_repo.get_by_username("admin@flowbot.com")
            if not existing_user:
                auth_service = AuthService()
                hashed_pwd = auth_service.get_password_hash("admin123")
                admin_user = User(
                    username="admin@flowbot.com",
                    email="admin@flowbot.com",
                    hashed_password=hashed_pwd,
                    full_name="Admin User",
                    role="Admin",
                    is_superuser=True
                )
                session.add(admin_user)
                session.commit()
                print("Created default admin user: admin@flowbot.com / admin123")
    except Exception as e:
        print(f"Warning: Could not create default user: {e}")
        print("You may need to create users manually or check the database.")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowBot Hub"}
