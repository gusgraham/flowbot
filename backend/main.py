from fastapi import FastAPI
from api import projects, installs, dashboard, qa

app = FastAPI(title="FlowBot Hub")

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(installs.router, prefix="/api", tags=["installs"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(qa.router, prefix="/api", tags=["qa"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowBot Hub"}
