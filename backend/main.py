from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from api import fsm, verification, wq, auth, fsa, users, ssd, dry_day, admin, fsa_dwf
from database import get_session, create_db_and_tables
from domain.auth import User, UserCreate
from services.auth import AuthService
from repositories.auth import UserRepository

app = FastAPI(title="FlowBot Hub")

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://GLWS-150447-BMF:5173",
    "http://glws-150447-bmf:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usage logging middleware for cost tracking
from middleware.usage_logging import UsageLoggingMiddleware
app.add_middleware(UsageLoggingMiddleware)

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(fsm.router, prefix="/api", tags=["fsm"])
app.include_router(fsa.router, prefix="/api")
app.include_router(fsa_dwf.router, prefix="/api") # DWF endpoints
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(dry_day.router, prefix="/api")  # Dry Day Analysis endpoints
app.include_router(wq.router, prefix="/api", tags=["wq"])
app.include_router(ssd.router, prefix="/api", tags=["ssd"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

from api import ingestion
app.include_router(ingestion.router, prefix="/api", tags=["ingestion"])

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
            
            # Seed default module weights if not exist
            from domain.admin import ModuleWeight
            existing_weights = session.exec(select(ModuleWeight)).all()
            if not existing_weights:
                default_modules = [
                    ("FSM", "Flow Survey Management"),
                    ("FSA", "Flow Survey Analysis"),
                    ("WQ", "Water Quality"),
                    ("VER", "Verification"),
                    ("SSD", "Spill Storage Design"),
                ]
                for module, desc in default_modules:
                    session.add(ModuleWeight(module=module, weight=1.0, description=desc))
                session.commit()
                print("Seeded default module weights")
    except Exception as e:
        print(f"Warning: Could not create default user: {e}")
        print("You may need to create users manually or check the database.")

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowBot Hub"}

from apscheduler.schedulers.background import BackgroundScheduler
from services.storage import create_storage_snapshots
from datetime import date

scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(create_storage_snapshots, 'cron', hour=0, minute=0, id='daily_storage_snapshot', replace_existing=True)
    scheduler.start()
    print("Scheduler started: Daily storage snapshots scheduled for 00:00")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
