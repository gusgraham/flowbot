from fastapi import FastAPI
from api import projects, installs, dashboard, qa, analysis, verification

app = FastAPI(title="FlowBot Hub")

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(installs.router, prefix="/api", tags=["installs"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(qa.router, prefix="/api", tags=["qa"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(verification.router, prefix="/api", tags=["verification"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FlowBot Hub"}
