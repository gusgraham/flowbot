"""
Field Survey Management (FSM) API Endpoints
All API endpoints related to field survey management are consolidated here.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlmodel import Session
from database import get_session
from domain.fsm import (
    FsmProjectRead, FsmProjectCreate, FsmProjectUpdate, 
    SiteRead, SiteCreate, 
    InstallRead, InstallCreate,
    MonitorRead, MonitorCreate,
    VisitRead, VisitCreate,
    NoteRead, NoteCreate,
    AttachmentRead, AttachmentCreate,
    RawDataSettingsRead, RawDataSettingsCreate, RawDataSettingsUpdate
)
from domain.auth import User
from api.deps import get_current_active_user
from services.project import ProjectService
from services.install import InstallService
from services.qa import QAService
from services.dashboard import DashboardService

router = APIRouter()

# ==========================================
# FSM PROJECTS
# ==========================================

def get_project_service(session: Session = Depends(get_session)) -> ProjectService:
    return ProjectService(session)

@router.post("/projects", response_model=FsmProjectRead)
def create_project(
    project: FsmProjectCreate, 
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    return service.create_project(project, owner_id=current_user.id)

@router.get("/projects", response_model=List[FsmProjectRead])
def list_projects(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_superuser or current_user.role == 'Admin':
        return service.list_projects(offset, limit)
    else:
        return service.list_projects(offset, limit, owner_id=current_user.id)

@router.get("/projects/{project_id}", response_model=FsmProjectRead)
def get_project(
    project_id: int, 
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Access Control
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this project")
        
    return project

@router.put("/projects/{project_id}", response_model=FsmProjectRead)
def update_project(
    project_id: int, 
    project: FsmProjectUpdate, 
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    existing = service.get_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not (current_user.is_superuser or current_user.role == 'Admin' or existing.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this project")

    updated_project = service.update_project(project_id, project)
    return updated_project

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int, 
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    existing = service.get_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not (current_user.is_superuser or current_user.role == 'Admin' or existing.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")

    success = service.delete_project(project_id)
    return {"status": "success"}

@router.post("/projects/import-csv")
async def import_project_csv(
    file: UploadFile = File(...), 
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    content = await file.read()
    try:
        service.import_project_from_csv(content, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    return {"status": "success"}

# ==========================================
# FSM SITES
# ==========================================

@router.post("/sites", response_model=SiteRead)
def create_site(site: SiteCreate, service: ProjectService = Depends(get_project_service)):
    return service.create_site(site)

@router.get("/projects/{project_id}/sites", response_model=List[SiteRead])
def list_project_sites(project_id: int, service: ProjectService = Depends(get_project_service)):
    return service.list_sites(project_id)

# ==========================================
# FSM MONITORS
# ==========================================

@router.post("/monitors", response_model=MonitorRead)
def create_monitor(monitor: MonitorCreate, service: ProjectService = Depends(get_project_service)):
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
def list_monitors(offset: int = 0, limit: int = 100, service: ProjectService = Depends(get_project_service)):
    return service.list_monitors(offset, limit)

@router.get("/sites/{site_id}/monitors", response_model=List[MonitorRead])
def list_site_monitors(site_id: int, service: ProjectService = Depends(get_project_service)):
    return service.list_monitors_by_site(site_id)

@router.get("/projects/{project_id}/monitors", response_model=List[MonitorRead])
def list_project_monitors(project_id: int, service: ProjectService = Depends(get_project_service)):
    try:
        monitors = service.list_monitors_by_project(project_id)
        return monitors if monitors else []
    except Exception as e:
        print(f"Error listing monitors: {e}")
        return []

# ==========================================
# FSM INSTALLS
# ==========================================

@router.post("/installs", response_model=InstallRead)
def create_install(install: InstallCreate, service: ProjectService = Depends(get_project_service)):
    return service.create_install(install)

@router.get("/projects/{project_id}/installs", response_model=List[InstallRead])
def list_project_installs(project_id: int, service: ProjectService = Depends(get_project_service)):
    return service.list_installs(project_id)

@router.get("/sites/{site_id}/installs", response_model=List[InstallRead])
def list_site_installs(site_id: int, service: ProjectService = Depends(get_project_service)):
    all_installs = service.install_repo.list(limit=1000)
    return [i for i in all_installs if i.site_id == site_id]

@router.get("/monitors/{monitor_id}/installs", response_model=List[InstallRead])
def list_monitor_installs(monitor_id: int, service: ProjectService = Depends(get_project_service)):
    all_installs = service.install_repo.list(limit=1000)
    return [i for i in all_installs if i.monitor_id == monitor_id]

@router.get("/installs/{install_id}", response_model=InstallRead)
def get_install(install_id: int, service: ProjectService = Depends(get_project_service)):
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    return install

@router.delete("/installs/{install_id}")
def delete_install(
    install_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this install")
    
    service.delete_install(install_id)
    return {"status": "success"}

@router.put("/installs/{install_id}/uninstall")
def uninstall_install(
    install_id: int,
    data: dict,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this install")
    
    # Parse removal_date from request body
    removal_date_str = data.get("removal_date")
    if not removal_date_str:
        raise HTTPException(status_code=400, detail="removal_date is required")
    
    # Convert string to datetime
    from datetime import datetime as dt
    removal_date = dt.fromisoformat(removal_date_str.replace('Z', '+00:00'))
    
    service.uninstall_install(install_id, removal_date)
    return {"status": "success"}

# ==========================================
# FSM VISITS
# ==========================================

def get_install_service(session: Session = Depends(get_session)) -> InstallService:
    return InstallService(session)

@router.post("/installs/{install_id}/visits", response_model=VisitRead)
def create_visit(install_id: int, visit: VisitCreate, service: InstallService = Depends(get_install_service)):
    visit.install_id = install_id
    return service.create_visit(visit)

@router.get("/installs/{install_id}/visits", response_model=List[VisitRead])
def list_visits(install_id: int, service: InstallService = Depends(get_install_service)):
    return service.list_visits(install_id)

@router.post("/installs/{install_id}/upload")
async def upload_data(install_id: int, file: UploadFile = File(...), service: InstallService = Depends(get_install_service)):
    content = await file.read()
    service.upload_data(install_id, content, file.filename)
    return {"message": "File uploaded successfully", "filename": file.filename}

# ==========================================
# FSM QA - NOTES & ATTACHMENTS
# ==========================================

def get_qa_service(session: Session = Depends(get_session)) -> QAService:
    return QAService(session)

@router.post("/projects/{project_id}/notes", response_model=NoteRead)
def create_note(project_id: int, note: NoteCreate, service: QAService = Depends(get_qa_service)):
    note.project_id = project_id
    return service.create_note(note)

@router.get("/projects/{project_id}/notes", response_model=List[NoteRead])
def list_notes(project_id: int, service: QAService = Depends(get_qa_service)):
    return service.list_notes(project_id)

@router.post("/projects/{project_id}/attachments", response_model=AttachmentRead)
async def create_attachment(
    project_id: int, 
    file: UploadFile = File(...),
    service: QAService = Depends(get_qa_service)
):
    content = await file.read()
    attachment_in = AttachmentCreate(
        filename=file.filename,
        file_path="",  # Will be set by service
        user_id=1,  # TODO: Get from auth context
        project_id=project_id
    )
    return service.create_attachment(attachment_in, content)

@router.get("/projects/{project_id}/attachments", response_model=List[AttachmentRead])
def list_attachments(project_id: int, service: QAService = Depends(get_qa_service)):
    return service.list_attachments(project_id)

# ==========================================
# FSM DASHBOARD
# ==========================================

def get_dashboard_service(session: Session = Depends(get_session)) -> DashboardService:
    return DashboardService(session)

@router.get("/projects/{project_id}/monitor-status")
def get_monitor_status(project_id: int, service: DashboardService = Depends(get_dashboard_service)):
    return service.get_monitor_status(project_id)

@router.get("/monitors/{monitor_id}/history")
def get_monitor_history(monitor_id: int, service: DashboardService = Depends(get_dashboard_service)):
    return service.get_monitor_history(monitor_id)

@router.get("/projects/{project_id}/data-summary")
def get_data_summary(project_id: int, service: DashboardService = Depends(get_dashboard_service)):
    return service.get_data_summary(project_id)

@router.get("/projects/{project_id}/issues")
def get_issues(project_id: int, service: DashboardService = Depends(get_dashboard_service)):
    return service.get_issues(project_id)

# ==========================================
# RAW DATA SETTINGS
# ==========================================

@router.get("/installs/{install_id}/raw-data-settings", response_model=RawDataSettingsRead)
def get_raw_data_settings(
    install_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    settings = service.get_raw_data_settings(install_id)
    if not settings:
        # Return empty settings if none exist
        raise HTTPException(status_code=404, detail="Raw data settings not found")
    
    return settings

@router.put("/installs/{install_id}/raw-data-settings", response_model=RawDataSettingsRead)
def update_raw_data_settings(
    install_id: int,
    settings_update: RawDataSettingsUpdate,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return service.update_raw_data_settings(install_id, settings_update)

@router.post("/installs/{install_id}/validate-file")
def validate_file(
    install_id: int,
    file_path: str,
    file_format: str,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    """Validate if a file exists at the specified path with the given format."""
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    exists = service.validate_file_exists(file_path, file_format, install)
    return {"exists": exists, "resolved_path": service.resolve_file_format(file_format, install, project)}

# ==========================================
# INSTALL TIMESERIES DATA
# ==========================================

@router.get("/installs/{install_id}/timeseries")
def get_install_timeseries(
    install_id: int,
    data_type: str = "Raw",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_points: int = 5000,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get timeseries data for an install with optional filtering and downsampling."""
    import pandas as pd
    from pathlib import Path
    from datetime import datetime as dt
    
    install = service.get_install(install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check project ownership
    project = service.get_project(install.project_id)
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get timeseries records for this install
    from domain.fsm import TimeSeries
    from sqlmodel import select
    

    
    statement = select(TimeSeries).where(
        TimeSeries.install_id == install_id,
        TimeSeries.data_type == data_type
    )
    timeseries_records = service.session.exec(statement).all()

    
    if not timeseries_records:
        return {
            "install_id": install_id,
            "install_type": install.install_type,
            "data_type": data_type,
            "variables": {}
        }
    
    # Load data from parquet files
    all_data = []
    # Files are stored in data/fsm/timeseries/installs/{install_id}/
    data_dir = Path("data/fsm")
    for ts in timeseries_records:
        if ts.filename:
            file_path = data_dir / ts.filename
            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    df['variable'] = ts.variable
                    df['unit'] = ts.unit or ''
                    all_data.append(df)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    
    if not all_data:
        return {
            "install_id": install_id,
            "install_type": install.install_type,
            "data_type": data_type,
            "variables": {}
        }
    
    combined = pd.concat(all_data, ignore_index=True)
    
    # Apply date filtering
    if 'timestamp' in combined.columns:
        time_col = 'timestamp'
    elif 'time' in combined.columns:
        time_col = 'time'
    else:
        time_col = combined.columns[0]
    
    combined[time_col] = pd.to_datetime(combined[time_col])
    
    if start_date:
        combined = combined[combined[time_col] >= pd.to_datetime(start_date)]
    if end_date:
        combined = combined[combined[time_col] <= pd.to_datetime(end_date)]
    
    # Process each variable
    result_variables = {}
    
    for var_name in combined['variable'].unique():
        var_df = combined[combined['variable'] == var_name].copy()
        var_df = var_df.sort_values(time_col)
        
        # Determine value column
        value_col = 'value' if 'value' in var_df.columns else var_df.columns[1]
        unit = var_df['unit'].iloc[0] if 'unit' in var_df.columns else ''
        
        # Downsample if needed
        if len(var_df) > max_points:
            var_df = downsample_with_peaks(var_df, time_col, value_col, max_points)
        
        # Calculate stats
        numeric_values = pd.to_numeric(var_df[value_col], errors='coerce')
        stats = {
            "min": float(numeric_values.min()) if not numeric_values.isna().all() else None,
            "max": float(numeric_values.max()) if not numeric_values.isna().all() else None,
            "mean": float(numeric_values.mean()) if not numeric_values.isna().all() else None,
            "count": len(var_df)
        }
        
        # Format data for frontend
        data_points = []
        for _, row in var_df.iterrows():
            val = row[value_col]
            data_points.append({
                "time": row[time_col].isoformat(),
                "value": float(val) if pd.notna(val) else None
            })
        
        result_variables[var_name] = {
            "data": data_points,
            "stats": stats,
            "unit": unit
        }
    
    return {
        "install_id": install_id,
        "install_type": install.install_type,
        "data_type": data_type,
        "variables": result_variables
    }


def downsample_with_peaks(df, time_col, value_col, max_points):
    """Downsample data while preserving peaks and troughs."""
    if len(df) <= max_points:
        return df
    
    # Calculate segment size
    segment_size = len(df) // (max_points // 3)
    if segment_size < 2:
        return df.iloc[::len(df)//max_points]
    
    indices = []
    for i in range(0, len(df), segment_size):
        segment = df.iloc[i:i+segment_size]
        if len(segment) == 0:
            continue
        
        indices.append(segment.index[0])  # First point
        
        try:
            numeric_vals = pd.to_numeric(segment[value_col], errors='coerce')
            if not numeric_vals.isna().all():
                indices.append(numeric_vals.idxmax())  # Peak
                indices.append(numeric_vals.idxmin())  # Trough
        except:
            pass
    
    indices.append(df.index[-1])  # Last point
    unique_indices = sorted(set(indices))
    
    return df.loc[unique_indices]
