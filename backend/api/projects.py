from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from database import get_session
from domain.project import ProjectRead, ProjectCreate, SiteRead, SiteCreate, InstallRead, InstallCreate
from domain.monitor import MonitorRead, MonitorCreate
from services.project import ProjectService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> ProjectService:
    return ProjectService(session)

# Projects
@router.post("/projects", response_model=ProjectRead)
def create_project(project: ProjectCreate, service: ProjectService = Depends(get_service)):
    return service.create_project(project)

@router.get("/projects", response_model=List[ProjectRead])
def list_projects(offset: int = 0, limit: int = 100, service: ProjectService = Depends(get_service)):
    return service.list_projects(offset, limit)

@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, service: ProjectService = Depends(get_service)):
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Sites
@router.post("/sites", response_model=SiteRead)
def create_site(site: SiteCreate, service: ProjectService = Depends(get_service)):
    return service.create_site(site)

@router.get("/projects/{project_id}/sites", response_model=List[SiteRead])
def list_project_sites(project_id: int, service: ProjectService = Depends(get_service)):
    return service.list_sites(project_id)

# Monitors
@router.post("/monitors", response_model=MonitorRead)
def create_monitor(monitor: MonitorCreate, service: ProjectService = Depends(get_service)):
    return service.create_monitor(monitor)

@router.get("/monitors", response_model=List[MonitorRead])
def list_monitors(offset: int = 0, limit: int = 100, service: ProjectService = Depends(get_service)):
    return service.list_monitors(offset, limit)

# Installs
@router.post("/installs", response_model=InstallRead)
def create_install(install: InstallCreate, service: ProjectService = Depends(get_service)):
    return service.create_install(install)

@router.get("/projects/{project_id}/installs", response_model=List[InstallRead])
def list_project_installs(project_id: int, service: ProjectService = Depends(get_service)):
    return service.list_installs(project_id)
