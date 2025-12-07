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
from domain.interim import (
    Interim, InterimCreate, InterimUpdate, InterimRead,
    InterimReview, InterimReviewCreate, InterimReviewRead,
    ReviewAnnotation, ReviewAnnotationCreate, ReviewAnnotationRead,
    StageSignoff
)
from domain.auth import User
from api.deps import get_current_active_user, get_storage_service
from services.project import ProjectService
from services.install import InstallService
from services.qa import QAService
from services.dashboard import DashboardService
from infra.storage import StorageService

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
    installs = service.list_installs(project_id)
    
    # Enrich with status info
    from domain.fsm import TimeSeries
    from sqlmodel import select, func
    
    result_installs = []
    for install in installs:
        # Get last ingested (Raw)
        last_ingested = service.session.exec(
            select(func.max(TimeSeries.end_time))
            .where(TimeSeries.install_id == install.id)
            .where(TimeSeries.data_type == 'Raw')
        ).first()
        
        # Get last processed (Processed)
        last_processed = service.session.exec(
            select(func.max(TimeSeries.end_time))
            .where(TimeSeries.install_id == install.id)
            .where(TimeSeries.data_type == 'Processed')
        ).first()
        
        # Convert to InstallRead and set fields
        # Note: distinct from database model Install, utilizing InstallRead schema
        install_read = InstallRead.model_validate(install)
        install_read.last_data_ingested = last_ingested
        install_read.last_data_processed = last_processed
        result_installs.append(install_read)
        
    return result_installs

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
from services.processing import ProcessingService

@router.post("/installs/{install_id}/process")
def process_install_data(
    install_id: int,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Run data processing for a specific install.
    Applies calibrations and calculates derived variables (Flow).
    """
    service = ProcessingService(session, storage)
    try:
        service.process_install(install_id)
        return {"status": "success", "message": "Processing complete"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/projects/{project_id}/process")
def process_project_data(
    project_id: int,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Run data processing for all installs in a project.
    """
    service = ProcessingService(session, storage)
    try:
        results = service.process_project(project_id)
        return results
    except Exception as e:
        print(f"Project processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Project processing failed: {str(e)}")

# ==========================================
# INTERIMS
# ==========================================

@router.post("/projects/{project_id}/interims", response_model=InterimRead)
def create_interim(
    project_id: int,
    interim: InterimCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new interim for a project."""
    from domain.fsm import FsmProject, Install
    
    # Verify project exists
    project = session.get(FsmProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create interim
    db_interim = Interim(
        project_id=project_id,
        start_date=interim.start_date,
        end_date=interim.end_date
    )
    session.add(db_interim)
    session.commit()
    session.refresh(db_interim)
    
    # Auto-create InterimReview for each active install
    installs = session.query(Install).filter(
        Install.project_id == project_id,
        Install.removal_date == None
    ).all()
    
    for install in installs:
        review = InterimReview(
            interim_id=db_interim.id,
            install_id=install.id,
            monitor_id=install.monitor_id,
            install_type=install.install_type
        )
        session.add(review)
    
    session.commit()
    session.refresh(db_interim)
    
    return db_interim


@router.get("/projects/{project_id}/interims", response_model=List[InterimRead])
def list_project_interims(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all interims for a project."""
    interims = session.query(Interim).filter(Interim.project_id == project_id).all()
    
    # Add review counts
    result = []
    for interim in interims:
        interim_dict = InterimRead(
            id=interim.id,
            project_id=interim.project_id,
            start_date=interim.start_date,
            end_date=interim.end_date,
            status=interim.status,
            revision_of=interim.revision_of,
            created_at=interim.created_at,
            locked_at=interim.locked_at,
            review_count=len(interim.reviews),
            reviews_complete=sum(1 for r in interim.reviews if r.review_complete)
        )
        result.append(interim_dict)
    
    return result


@router.get("/interims/{interim_id}", response_model=InterimRead)
def get_interim(
    interim_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get an interim by ID."""
    interim = session.get(Interim, interim_id)
    if not interim:
        raise HTTPException(status_code=404, detail="Interim not found")
    
    return InterimRead(
        id=interim.id,
        project_id=interim.project_id,
        start_date=interim.start_date,
        end_date=interim.end_date,
        status=interim.status,
        revision_of=interim.revision_of,
        created_at=interim.created_at,
        locked_at=interim.locked_at,
        review_count=len(interim.reviews),
        reviews_complete=sum(1 for r in interim.reviews if r.review_complete)
    )


@router.put("/interims/{interim_id}", response_model=InterimRead)
def update_interim(
    interim_id: int,
    update: InterimUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update an interim."""
    interim = session.get(Interim, interim_id)
    if not interim:
        raise HTTPException(status_code=404, detail="Interim not found")
    
    if interim.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot modify a locked interim")
    
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interim, key, value)
    
    session.add(interim)
    session.commit()
    session.refresh(interim)
    
    return interim


@router.delete("/interims/{interim_id}")
def delete_interim(
    interim_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an interim."""
    interim = session.get(Interim, interim_id)
    if not interim:
        raise HTTPException(status_code=404, detail="Interim not found")
    
    if interim.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot delete a locked interim")
    
    session.delete(interim)
    session.commit()
    
    return {"status": "success", "message": "Interim deleted"}


# ==========================================
# INTERIM REVIEWS
# ==========================================

@router.get("/interims/{interim_id}/reviews", response_model=List[InterimReviewRead])
def list_interim_reviews(
    interim_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all reviews for an interim."""
    reviews = session.query(InterimReview).filter(
        InterimReview.interim_id == interim_id
    ).all()
    
    result = []
    for review in reviews:
        review_dict = InterimReviewRead(
            id=review.id,
            interim_id=review.interim_id,
            install_id=review.install_id,
            monitor_id=review.monitor_id,
            install_type=review.install_type,
            data_coverage_pct=review.data_coverage_pct,
            gaps_json=review.gaps_json,
            data_import_acknowledged=review.data_import_acknowledged,
            data_import_notes=review.data_import_notes,
            data_import_reviewer=review.data_import_reviewer,
            data_import_reviewed_at=review.data_import_reviewed_at,
            classification_complete=review.classification_complete,
            classification_comment=review.classification_comment,
            classification_reviewer=review.classification_reviewer,
            classification_reviewed_at=review.classification_reviewed_at,
            events_complete=review.events_complete,
            events_comment=review.events_comment,
            events_reviewer=review.events_reviewer,
            events_reviewed_at=review.events_reviewed_at,
            review_complete=review.review_complete,
            review_comment=review.review_comment,
            review_reviewer=review.review_reviewer,
            review_reviewed_at=review.review_reviewed_at,
            annotation_count=len(review.annotations)
        )
        result.append(review_dict)
    
    return result


@router.get("/reviews/{review_id}", response_model=InterimReviewRead)
def get_interim_review(
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get an interim review by ID."""
    review = session.get(InterimReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return InterimReviewRead(
        id=review.id,
        interim_id=review.interim_id,
        install_id=review.install_id,
        monitor_id=review.monitor_id,
        install_type=review.install_type,
        data_coverage_pct=review.data_coverage_pct,
        gaps_json=review.gaps_json,
        data_import_acknowledged=review.data_import_acknowledged,
        data_import_notes=review.data_import_notes,
        data_import_reviewer=review.data_import_reviewer,
        data_import_reviewed_at=review.data_import_reviewed_at,
        classification_complete=review.classification_complete,
        classification_comment=review.classification_comment,
        classification_reviewer=review.classification_reviewer,
        classification_reviewed_at=review.classification_reviewed_at,
        events_complete=review.events_complete,
        events_comment=review.events_comment,
        events_reviewer=review.events_reviewer,
        events_reviewed_at=review.events_reviewed_at,
        review_complete=review.review_complete,
        review_comment=review.review_comment,
        review_reviewer=review.review_reviewer,
        review_reviewed_at=review.review_reviewed_at,
        annotation_count=len(review.annotations)
    )


@router.put("/reviews/{review_id}/signoff/{stage}")
def signoff_review_stage(
    review_id: int,
    stage: str,
    signoff: StageSignoff,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Sign off a review stage (data_import, classification, events, review)."""
    from datetime import datetime
    
    review = session.get(InterimReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check interim is not locked
    interim = session.get(Interim, review.interim_id)
    if interim and interim.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot modify a locked interim")
    
    valid_stages = ["data_import", "classification", "events", "review"]
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")
    
    now = datetime.now()
    
    if stage == "data_import":
        review.data_import_acknowledged = True
        review.data_import_notes = signoff.comment
        review.data_import_reviewer = signoff.reviewer
        review.data_import_reviewed_at = now
    elif stage == "classification":
        review.classification_complete = True
        review.classification_comment = signoff.comment
        review.classification_reviewer = signoff.reviewer
        review.classification_reviewed_at = now
    elif stage == "events":
        review.events_complete = True
        review.events_comment = signoff.comment
        review.events_reviewer = signoff.reviewer
        review.events_reviewed_at = now
    elif stage == "review":
        review.review_complete = True
        review.review_comment = signoff.comment
        review.review_reviewer = signoff.reviewer
        review.review_reviewed_at = now
    
    session.add(review)
    session.commit()
    
    return {"status": "success", "message": f"Stage '{stage}' signed off"}


@router.post("/reviews/{review_id}/calculate-coverage")
def calculate_review_coverage(
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate and update data coverage for a review."""
    from services.data_coverage import update_review_coverage
    from infra.storage import StorageService
    
    storage = StorageService()
    result = update_review_coverage(session, review_id, storage)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/interims/{interim_id}/calculate-all-coverage")
def calculate_interim_coverage(
    interim_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate data coverage for all reviews in an interim."""
    from services.data_coverage import update_review_coverage
    from infra.storage import StorageService
    
    interim = session.get(Interim, interim_id)
    if not interim:
        raise HTTPException(status_code=404, detail="Interim not found")
    
    storage = StorageService()
    results = []
    
    for review in interim.reviews:
        result = update_review_coverage(session, review.id, storage)
        results.append({
            "review_id": review.id,
            "install_id": review.install_id,
            **result
        })
    
    return {"message": f"Calculated coverage for {len(results)} reviews", "results": results}


# ==========================================
# REVIEW ANNOTATIONS
# ==========================================

@router.get("/reviews/{review_id}/annotations", response_model=List[ReviewAnnotationRead])
def list_review_annotations(
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all annotations for a review."""
    annotations = session.query(ReviewAnnotation).filter(
        ReviewAnnotation.interim_review_id == review_id
    ).all()
    return annotations


@router.post("/reviews/{review_id}/annotations", response_model=ReviewAnnotationRead)
def create_review_annotation(
    review_id: int,
    annotation: ReviewAnnotationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create an annotation for a review."""
    review = session.get(InterimReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db_annotation = ReviewAnnotation(
        interim_review_id=review_id,
        variable=annotation.variable,
        start_time=annotation.start_time,
        end_time=annotation.end_time,
        issue_type=annotation.issue_type,
        description=annotation.description,
        created_by=current_user.username if current_user else None
    )
    session.add(db_annotation)
    session.commit()
    session.refresh(db_annotation)
    
    return db_annotation


@router.delete("/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an annotation."""
    annotation = session.get(ReviewAnnotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    session.delete(annotation)
    session.commit()
    
    return {"status": "success", "message": "Annotation deleted"}


# ==========================================
# CLASSIFICATION
# ==========================================

@router.get("/reviews/{review_id}/classifications")
def get_review_classifications(
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily classifications for a review."""
    from domain.interim import DailyClassification
    
    review = session.get(InterimReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    classifications = session.query(DailyClassification).filter(
        DailyClassification.interim_review_id == review_id
    ).order_by(DailyClassification.date).all()
    
    return [
        {
            "id": c.id,
            "date": c.date.isoformat() if c.date else None,
            "ml_classification": c.ml_classification,
            "ml_confidence": c.ml_confidence,
            "manual_classification": c.manual_classification,
            "override_reason": c.override_reason,
            "override_by": c.override_by,
            "override_at": c.override_at.isoformat() if c.override_at else None,
        }
        for c in classifications
    ]


@router.post("/reviews/{review_id}/classify")
def run_classification_for_review(
    review_id: int,
    session: Session = Depends(get_session),
    storage: StorageService = Depends(get_storage_service),
    current_user: User = Depends(get_current_active_user)
):
    """Run ML classification for a review."""
    from domain.interim import DailyClassification, Interim
    from domain.fsm import Install, TimeSeries
    from services.classification import run_classification, check_models_available
    import pandas as pd
    
    review = session.get(InterimReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    interim = session.get(Interim, review.interim_id)
    if not interim:
        raise HTTPException(status_code=404, detail="Interim not found")
    
    install = session.get(Install, review.install_id)
    if not install:
        raise HTTPException(status_code=404, detail="Install not found")
    
    # Check models are available
    models_available = check_models_available()
    model_type = 'FM' if install.install_type == 'Flow Monitor' else 'RG' if install.install_type == 'Rain Gauge' else 'DM'
    
    if not models_available.get(model_type, False):
        raise HTTPException(
            status_code=400, 
            detail=f"ML model for {install.install_type} not found. Please add {model_type}_model to backend/resources/classifier/models/"
        )
    
    # Load timeseries data for the interim period
    timeseries = session.query(TimeSeries).filter(
        TimeSeries.install_id == review.install_id
    ).all()
    
    if not timeseries:
        raise HTTPException(status_code=400, detail="No timeseries data found for this install")
    
    # Load and combine data
    all_data = []
    for ts in timeseries:
        try:
            if not ts.filename:
                continue
            ts_data = storage.read_parquet(ts.filename)
            if ts_data is not None and not ts_data.empty:
                # Find time column and standardize
                time_col = None
                for col in ['time', 'timestamp', 'Date']:
                    if col in ts_data.columns:
                        time_col = col
                        break
                if time_col and time_col != 'timestamp':
                    ts_data = ts_data.rename(columns={time_col: 'timestamp'})
                
                # Rename value column to expected name
                if 'value' in ts_data.columns:
                    col_name = f"{ts.variable}Data"
                    ts_data = ts_data.rename(columns={'value': col_name})
                all_data.append(ts_data)
        except Exception as e:
            print(f"Error loading timeseries {ts.variable}: {e}")
    
    if not all_data:
        raise HTTPException(status_code=400, detail="Could not load timeseries data")
    
    # Merge all data on timestamp
    try:
        combined = all_data[0]
        for df in all_data[1:]:
            combined = pd.merge(combined, df, on='timestamp', how='outer')
        
        combined = combined.rename(columns={'timestamp': 'Date'})
        print(f"Combined data shape: {combined.shape}, columns: {list(combined.columns)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to merge timeseries data: {str(e)}")
    
    # Prepare install data for feature extraction
    install_data = {
        'fm_pipe_height_mm': install.fm_pipe_height_mm,
        'fm_pipe_width_mm': install.fm_pipe_width_mm,
        'fm_pipe_depth_to_invert_mm': install.fm_pipe_depth_to_invert_mm,
        'fm_pipe_letter': install.fm_pipe_letter,
        'fm_pipe_shape': install.fm_pipe_shape,
    }
    
    # Run classification
    try:
        results = run_classification(
            install_type=install.install_type,
            data=combined,
            start_date=interim.start_date,
            end_date=interim.end_date,
            install_data=install_data
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
    
    # Delete existing classifications for this review
    session.query(DailyClassification).filter(
        DailyClassification.interim_review_id == review_id
    ).delete()
    
    # Save new classifications
    for result in results:
        # Parse date string back to datetime
        date_val = result['date']
        if isinstance(date_val, str):
            from datetime import datetime
            date_val = datetime.fromisoformat(date_val)
        
        classification = DailyClassification(
            interim_review_id=review_id,
            date=date_val,
            ml_classification=result['classification'],
            ml_confidence=result['confidence']
        )
        session.add(classification)
    
    session.commit()
    
    return {
        "status": "success",
        "message": f"Classified {len(results)} days",
        "results_count": len(results)
    }


@router.put("/classifications/{classification_id}/override")
def override_classification(
    classification_id: int,
    override_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Override a classification manually."""
    from domain.interim import DailyClassification
    from datetime import datetime
    
    classification = session.get(DailyClassification, classification_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    
    classification.manual_classification = override_data.get('manual_classification')
    classification.override_reason = override_data.get('override_reason')
    classification.override_by = current_user.username if current_user else 'Unknown'
    classification.override_at = datetime.now()
    
    session.add(classification)
    session.commit()
    
    return {"status": "success", "message": "Classification overridden"}


@router.get("/classification/models-status")
def get_models_status(
    current_user: User = Depends(get_current_active_user)
):
    """Check which ML models are available."""
    from services.classification import check_models_available
    
    return check_models_available()
