from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
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
def list_projects(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    service: ProjectService = Depends(get_service)
):
    return service.list_projects(offset, limit)

@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, service: ProjectService = Depends(get_service)):
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, project: ProjectCreate, service: ProjectService = Depends(get_service)):
    updated_project = service.update_project(project_id, project)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, service: ProjectService = Depends(get_service)):
    success = service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success"}

@router.post("/projects/import-csv")
async def import_project_csv(file: UploadFile = File(...), service: ProjectService = Depends(get_service)):
    content = await file.read()
    try:
        service.import_project_from_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    return {"status": "success"}

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
    try:
        return service.create_monitor(monitor)
    except Exception as e:
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg or "monitor_asset_id" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail=f"A monitor with asset ID '{monitor.monitor_asset_id}' already exists. Please use a different asset ID."
            )
        import traceback
        print(f"Error creating monitor: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create monitor: {str(e)}")

@router.get("/monitors", response_model=List[MonitorRead])
def list_monitors(offset: int = 0, limit: int = 100, service: ProjectService = Depends(get_service)):
    return service.list_monitors(offset, limit)

@router.get("/sites/{site_id}/monitors", response_model=List[MonitorRead])
def list_site_monitors(site_id: int, service: ProjectService = Depends(get_service)):
    return service.list_monitors_by_site(site_id)

@router.get("/projects/{project_id}/monitors", response_model=List[MonitorRead])
def list_project_monitors(project_id: int, service: ProjectService = Depends(get_service)):
    try:
        monitors = service.list_monitors_by_project(project_id)
        return monitors if monitors else []
    except Exception as e:
        print(f"Error listing monitors: {e}")
        return []

# Installs
@router.post("/installs", response_model=InstallRead)
def create_install(install: InstallCreate, service: ProjectService = Depends(get_service)):
    return service.create_install(install)

@router.get("/projects/{project_id}/installs", response_model=List[InstallRead])
def list_project_installs(project_id: int, service: ProjectService = Depends(get_service)):
    return service.list_installs(project_id)

@router.get("/sites/{site_id}/installs", response_model=List[InstallRead])
def list_site_installs(site_id: int, service: ProjectService = Depends(get_service)):
    all_installs = service.install_repo.list(limit=1000)
    return [i for i in all_installs if i.site_id == site_id]

@router.get("/monitors/{monitor_id}/installs", response_model=List[InstallRead])
def list_monitor_installs(monitor_id: int, service: ProjectService = Depends(get_service)):
    all_installs = service.install_repo.list(limit=1000)
    return [i for i in all_installs if i.monitor_id == monitor_id]


