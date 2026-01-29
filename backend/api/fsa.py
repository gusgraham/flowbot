from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body, Form
from sqlmodel import Session, select
import shutil
import os
import json
import threading
import time

from database import get_session, SessionLocal
from domain.fsa import (
    FsaProject, FsaProjectCreate, FsaProjectRead,
    FsaDataset, FsaDatasetCreate, FsaDatasetRead,
    FlowMonitor, FlowMonitorRead,
    FsaTimeSeries, FsaProjectCollaborator
)
from services.importers import import_fdv_file, import_r_file
from services.fsa_services import FsaRainfallService, FsaEventService, FsaFDVService
from pydantic import BaseModel
from domain.auth import User
from api.deps import get_current_active_user

router = APIRouter(prefix="/fsa", tags=["Flow Survey Analysis"])

# ==========================================
# PROJECTS
# ==========================================

@router.post("/projects", response_model=FsaProjectRead)
def create_project(
    project: FsaProjectCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_project = FsaProject(**project.model_dump())
    db_project.owner_id = current_user.id
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/projects", response_model=List[FsaProjectRead])
def read_projects(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    from domain.fsa import FsaProjectCollaborator
    from sqlmodel import or_, col
    
    if current_user.is_superuser or current_user.role == 'Admin':
        projects = session.exec(select(FsaProject).offset(offset).limit(limit)).all()
    else:
        # Include owned projects OR collaborative projects
        collab_subquery = select(FsaProjectCollaborator.project_id).where(
            FsaProjectCollaborator.user_id == current_user.id
        )
        projects = session.exec(
            select(FsaProject).where(
                or_(
                    FsaProject.owner_id == current_user.id,
                    col(FsaProject.id).in_(collab_subquery)
                )
            ).offset(offset).limit(limit)
        ).all()
    return projects

@router.get("/projects/{project_id}", response_model=FsaProjectRead)
def read_project(
    project_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check permissions
    is_collaborator = session.exec(
        select(FsaProjectCollaborator).where(
            FsaProjectCollaborator.project_id == project_id,
            FsaProjectCollaborator.user_id == current_user.id
        )
    ).first()

    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id or is_collaborator):
        raise HTTPException(status_code=403, detail="Not authorized to view this project")
        
    return project

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a project and all associated data (datasets, events, files)"""
    from domain.fsa import SurveyEvent
    
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    # Delete all timeseries data for datasets belonging to this project
    datasets = session.exec(select(FsaDataset).where(FsaDataset.project_id == project_id)).all()
    for dataset in datasets:
        # Delete timeseries records
        timeseries = session.exec(select(FsaTimeSeries).where(FsaTimeSeries.dataset_id == dataset.id)).all()
        for ts in timeseries:
            session.delete(ts)
        
        # Delete dataset file if exists
        if dataset.file_path and os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {dataset.file_path}: {e}")
        
        # Delete dataset record
        session.delete(dataset)
    
    # Delete all survey events
    events = session.exec(select(SurveyEvent).where(SurveyEvent.project_id == project_id)).all()
    for event in events:
        session.delete(event)
    
    # Delete project data directory if exists
    project_dir = f"data/fsa/{project_id}"
    if os.path.exists(project_dir):
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            print(f"Warning: Could not delete directory {project_dir}: {e}")
    
    # Delete the project
    session.delete(project)
    session.commit()
    
    return {"message": "Project deleted successfully", "project_id": project_id}

# ==========================================
# FILE UPLOAD
# ==========================================

@router.post("/projects/{project_id}/upload", response_model=FsaDatasetRead)
def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    dataset_type: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    print(f"\n{'='*60}")
    print(f"📤 UPLOAD START: {file.filename}")
    print(f"   Project ID: {project_id}")
    print(f"   Dataset Type: {dataset_type}")
    print(f"{'='*60}")
    
    # Verify project exists
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Ensure directory exists
    upload_dir = f"data/fsa/{project_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    print(f"💾 Saving file to: {file_path}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"✓ File saved successfully")
    except Exception as e:
        print(f"✗ ERROR saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Detect file type
    filename = file.filename.lower()
    variable_type = "Unknown"
    
    if filename.endswith('.r'):
        variable_type = "Rainfall"
    elif filename.endswith('.fdv'):
        variable_type = "Flow/Depth"
    elif filename.endswith('.std'):
        if dataset_type:
            variable_type = dataset_type
        else:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="For .STD files, please specify dataset_type as 'Rainfall' or 'Flow/Depth'")
    
    # Create dataset record with 'processing' status
    print(f"💾 Creating dataset record (status: processing)")
    retries = 3
    while retries > 0:
        try:
            dataset = FsaDataset(
                project_id=project_id,
                name=file.filename,
                variable=variable_type,
                file_path=file_path,
                status="processing",
                metadata_json=json.dumps({})
            )
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            print(f"✓ Dataset record created (ID: {dataset.id})")
            break
        except Exception as e:
            if "database is locked" in str(e):
                retries -= 1
                print(f"⚠️ Database locked during dataset creation, retrying ({retries} left)...")
                time.sleep(1)
                session.rollback()
            else:
                print(f"✗ ERROR creating dataset record: {e}")
                import traceback
                traceback.print_exc()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(status_code=500, detail=f"Failed to create dataset record: {str(e)}")
    
    if retries == 0:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Database locked - failed to create dataset record after retries")
    
    # Trigger background processing
    print(f"🚀 Triggering background processing for dataset {dataset.id}")
    thread = threading.Thread(target=process_dataset_background, args=(dataset.id,))
    thread.daemon = True
    thread.start()
    
    print(f"✅ UPLOAD COMPLETE: {file.filename} (processing in background)")
    print(f"{'='*60}\n")
    
    return dataset


def process_dataset_background(dataset_id: int):
    """Background task to parse file and populate timeseries data"""
    session = SessionLocal()
    try:
        dataset = session.get(FsaDataset, dataset_id)
        if not dataset:
            print(f"⚠️  Dataset {dataset_id} not found for background processing")
            return
        
        print(f"\n{'='*60}")
        print(f"🔄 BACKGROUND PROCESSING: {dataset.name} (ID: {dataset_id})")
        print(f"{'='*60}")
        
        file_path = dataset.file_path
        variable_type = dataset.variable
        metadata = {}
        parsed_data = None
        
        print(f"🔍 Parsing file (type: {file_path.split('.')[-1]})")
        
        try:
            if file_path.lower().endswith('.r'):
                print(f"   Parsing as .R (Rainfall)")
                data = import_r_file(file_path)
                metadata = {
                    "gauge_name": data["name"],
                    "interval": data["interval_minutes"],
                    "start": data["start_time"].isoformat(),
                    "end": data["end_time"].isoformat()
                }
                parsed_data = data
            elif file_path.lower().endswith('.fdv'):
                print(f"   Parsing as .FDV (Flow/Depth)")
                data = import_fdv_file(file_path)
                metadata = {
                    "monitor_name": data["name"],
                    "interval": data["interval_minutes"],
                    "start": data["start_time"].isoformat(),
                    "end": data["end_time"].isoformat(),
                    "units": data["units"]
                }
                parsed_data = data
            elif file_path.lower().endswith('.std'):
                if variable_type == "Rainfall":
                    print(f"   Parsing as .STD (Rainfall)")
                    data = import_r_file(file_path)
                    metadata = {
                        "gauge_name": data["name"],
                        "interval": data["interval_minutes"],
                        "start": data["start_time"].isoformat(),
                        "end": data["end_time"].isoformat()
                    }
                    parsed_data = data
                elif variable_type == "Flow/Depth":
                    print(f"   Parsing as .STD (Flow/Depth)")
                    data = import_fdv_file(file_path)
                    metadata = {
                        "monitor_name": data["name"],
                        "interval": data["interval_minutes"],
                        "start": data["start_time"].isoformat(),
                        "end": data["end_time"].isoformat(),
                        "units": data["units"]
                    }
                    parsed_data = data
            
            print(f"✓ File parsed successfully")
            print(f"   Name: {metadata.get('gauge_name') or metadata.get('monitor_name')}")
            print(f"   Interval: {metadata.get('interval')} minutes")
            
            # Update metadata
            dataset.metadata_json = json.dumps(metadata)
            
        except Exception as e:
            print(f"✗ ERROR parsing file: {e}")
            import traceback
            traceback.print_exc()
            dataset.status = "error"
            dataset.error_message = f"Failed to parse file: {str(e)}"
            session.commit()
            print(f"❌ PROCESSING FAILED: {dataset.name}")
            print(f"{'='*60}\n")
            return
        
        # Store timeseries data
        if parsed_data and 'data' in parsed_data:
            print(f"💾 Storing timeseries data")
            try:
                timeseries_records = []
                data_dict = parsed_data['data']
                
                if isinstance(data_dict, dict):
                    times = data_dict.get('time', [])
                    
                    if variable_type == "Rainfall":
                        values = data_dict.get('rainfall', [])
                        print(f"   Processing {len(times)} rainfall records...")
                        for timestamp, value in zip(times, values):
                            timeseries_records.append(
                                FsaTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=timestamp,
                                    value=float(value)
                                )
                            )
                    elif variable_type == "Flow/Depth":
                        flows = data_dict.get('flow', [])
                        depths = data_dict.get('depth', [])
                        velocities = data_dict.get('velocity', [])
                        
                        count = len(times)
                        print(f"   Processing {count} flow/depth/velocity records...")
                        
                        for i in range(count):
                            timeseries_records.append(
                                FsaTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=times[i],
                                    flow=float(flows[i]) if i < len(flows) and flows[i] is not None else 0.0,
                                    depth=float(depths[i]) if i < len(depths) and depths[i] is not None else 0.0,
                                    velocity=float(velocities[i]) if i < len(velocities) and velocities[i] is not None else 0.0
                                )
                            )
                
                if timeseries_records:
                    print(f"   Bulk inserting {len(timeseries_records)} records...")
                    
                    # Chunked insert to avoid database locks
                    BATCH_SIZE = 5000
                    total_records = len(timeseries_records)
                    
                    for i in range(0, total_records, BATCH_SIZE):
                        batch = timeseries_records[i:i + BATCH_SIZE]
                        retries = 3
                        while retries > 0:
                            try:
                                session.bulk_save_objects(batch)
                                session.commit()
                                break
                            except Exception as e:
                                if "database is locked" in str(e):
                                    retries -= 1
                                    print(f"   ⚠️ Database locked, retrying batch {i//BATCH_SIZE + 1} ({retries} retries left)...")
                                    time.sleep(1)
                                    session.rollback()
                                else:
                                    raise e
                        
                        if retries == 0:
                            print(f"   ❌ Failed to insert batch {i//BATCH_SIZE + 1} after retries")
                            raise Exception("Database locked - failed to insert batch after retries")
                            
                        print(f"   ✓ Stored batch {i//BATCH_SIZE + 1}/{(total_records + BATCH_SIZE - 1)//BATCH_SIZE}")
                        time.sleep(0.1)
                    
                    print(f"✓ Stored {len(timeseries_records)} timeseries records")
            except Exception as e:
                print(f"✗ Warning: Failed to store timeseries data: {e}")
                import traceback
                traceback.print_exc()
        
        # Mark as ready
        dataset.status = "ready"
        session.commit()
        
        print(f"✅ PROCESSING COMPLETE: {dataset.name}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ FATAL ERROR in background processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

# ==========================================
# DATASETS
# ==========================================

@router.get("/projects/{project_id}/datasets", response_model=List[FsaDatasetRead])
def list_datasets(
    project_id: int,
    session: Session = Depends(get_session)
):
    datasets = session.exec(select(FsaDataset).where(FsaDataset.project_id == project_id)).all()
    return datasets

@router.get("/datasets/{dataset_id}", response_model=FsaDatasetRead)
def read_dataset(dataset_id: int, session: Session = Depends(get_session)):
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.delete("/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    session: Session = Depends(get_session)
):
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Delete the file if it exists
    if dataset.file_path and os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {dataset.file_path}: {e}")
    
    # Delete the database record
    session.delete(dataset)
    session.commit()
    
    return {"message": "Dataset deleted successfully", "dataset_id": dataset_id}

@router.patch("/datasets/{dataset_id}", response_model=FsaDatasetRead)
def update_dataset(
    dataset_id: int,
    updates: Dict[str, Any] = Body(...),
    session: Session = Depends(get_session)
):
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Parse existing metadata
    try:
        metadata = json.loads(dataset.metadata_json) if dataset.metadata_json else {}
    except json.JSONDecodeError:
        metadata = {}

    for key, value in updates.items():
        if hasattr(dataset, key):
            # Handle metadata_json if passed explicitly as dict
            if key == "metadata_json" and isinstance(value, dict):
                metadata.update(value)
            else:
                setattr(dataset, key, value)
        else:
            # If field doesn't exist on model, store in metadata
            metadata[key] = value
    
    # Save updated metadata
    dataset.metadata_json = json.dumps(metadata)
    
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset

# ==========================================
# RAINFALL ANALYSIS
# ==========================================

def get_rainfall_service(session: Session = Depends(get_session)) -> FsaRainfallService:
    return FsaRainfallService(session)

def get_event_service(session: Session = Depends(get_session)) -> FsaEventService:
    return FsaEventService(session)

class AnalysisParams(BaseModel):
    rainfallDepthTolerance: float = 0.1 # Used as threshold_mm for dry days
    precedingDryDays: int = 4
    consecZero: int = 5 # Legacy, maybe unused if interEventGap is set
    interEventGap: int = 360 # Minutes
    requiredDepth: float = 5
    requiredIntensity: float = 6
    requiredIntensityDuration: int = 4 # Minutes
    partialPercent: float = 20
    useConsecutiveIntensities: bool = True

@router.post("/rainfall/events")
def run_rainfall_analysis(
    payload: Dict[str, Any],
    service: FsaEventService = Depends(get_event_service),
    rainfall_service: FsaRainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    # Parse payload manually to handle both legacy single ID and new list
    dataset_id = payload.get("dataset_id")
    dataset_ids = payload.get("dataset_ids", [])
    
    if dataset_id and not dataset_ids:
        dataset_ids = [dataset_id]
        
    params_dict = payload.get("params", {})
    # Default params if not provided
    params = AnalysisParams(**params_dict) if params_dict else AnalysisParams()

    all_events = []
    all_dry_days = []
    
    for ds_id in dataset_ids:
        dataset = service.get_dataset(ds_id)
        if not dataset:
            continue
            
        events = service.detect_storms(
            dataset_id=ds_id, 
            inter_event_minutes=params.interEventGap,
            min_total_mm=params.requiredDepth,
            min_intensity=params.requiredIntensity,
            min_intensity_duration=params.requiredIntensityDuration,
            partial_percent=params.partialPercent,
            use_consecutive_intensities=params.useConsecutiveIntensities
        )
        
        # Detect dry days
        dry_days = service.detect_dry_days(
            dataset_id=ds_id,
            threshold_mm=params.rainfallDepthTolerance,
            preceding_dry_days=params.precedingDryDays
        )
        
        # Add dataset name to events
        for event in events:
            event['dataset_id'] = ds_id
            event['dataset_name'] = dataset.name
            all_events.append(event)
            
        # Add dataset name to dry days
        for dry_day in dry_days:
            dry_day['dataset_id'] = ds_id
            dry_day['dataset_name'] = dataset.name
            all_dry_days.append(dry_day)
    
    return {
        "events": all_events,
        "dry_days": all_dry_days
    }
    period_start = datetime.now().isoformat()
    period_end = datetime.now().isoformat()
    if events:
        period_start = events[0]['start_time'].isoformat()
        period_end = events[-1]['end_time'].isoformat()
    elif timeseries_data:
        period_start = timeseries_data[0]['time']
        period_end = timeseries_data[-1]['time']
        
    # Format events for frontend
    formatted_events = []
    for e in events:
        formatted_events.append({
            "Start": e['start_time'].isoformat(),
            "End": e['end_time'].isoformat(),
            "Depth": e['total_mm'],
            "Intensity_Count": 0,
            "Passed": e['passed'],
            "Status": e['status']
        })
        
    formatted_dry_days = [d['date'].isoformat() for d in dry_days]

    return {
        "events": formatted_events,
        "dry_days": formatted_dry_days,
        "timeseries": timeseries_data,
        "stats": {
            "total_events": len([e for e in events if e['status'] == 'Event']),
            "total_rainfall_depth": total_rainfall,
            "analyzed_period_start": period_start,
            "analyzed_period_end": period_end
        }
    }

@router.get("/rainfall/{dataset_id}/cumulative-depth")
def get_cumulative_depth(
    dataset_id: int, 
    service: FsaRainfallService = Depends(get_rainfall_service)
):
    return service.get_cumulative_depth(dataset_id)

# ==========================================
# FDV ANALYSIS
# ==========================================

def get_fdv_service(session: Session = Depends(get_session)) -> FsaFDVService:
    return FsaFDVService(session)

@router.get("/fdv/{dataset_id}/timeseries")
def get_fdv_timeseries(
    dataset_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get time-series data (flow, depth, velocity) for FDV dataset"""
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    query = select(FsaTimeSeries).where(FsaTimeSeries.dataset_id == dataset_id)
    
    if start_date:
        query = query.where(FsaTimeSeries.timestamp >= start_date)
    if end_date:
        query = query.where(FsaTimeSeries.timestamp <= end_date)
        
    query = query.order_by(FsaTimeSeries.timestamp)
    results = session.exec(query).all()
    
    timeseries = []
    for row in results:
        timeseries.append({
            "time": row.timestamp.isoformat(),
            "rainfall": row.value if row.value is not None else 0.0,
            "flow": row.flow if row.flow is not None else 0.0,
            "depth": row.depth if row.depth is not None else 0.0,
            "velocity": row.velocity if row.velocity is not None else 0.0
        })
        
    return {"dataset_id": dataset_id, "data": timeseries, "count": len(timeseries)}

@router.get("/fdv/{dataset_id}/scatter")
def get_fdv_scatter(
    dataset_id: int,
    plot_mode: str = Query("velocity"),
    iso_min: Optional[float] = Query(None),
    iso_max: Optional[float] = Query(None),
    iso_count: int = Query(2),
    service: FsaFDVService = Depends(get_fdv_service)
) -> Dict[str, Any]:
    """Get scatter graph data including CBW and iso curves"""
    return service.get_scatter_graph_data(dataset_id, plot_mode, iso_min, iso_max, iso_count)

# ==========================================
# SURVEY EVENTS (Captured Events)
# ==========================================

class CaptureEventRequest(BaseModel):
    name: str
    event_type: str  # "Storm Event", "Dry Day", "Dry Period"
    start_time: datetime
    end_time: datetime

@router.post("/projects/{project_id}/events")
def create_survey_event(
    project_id: int,
    event_data: CaptureEventRequest,
    session: Session = Depends(get_session)
):
    """Save a captured event to the SurveyEvent table"""
    from domain.fsa import SurveyEvent
    
    # Verify project exists
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create survey event
    survey_event = SurveyEvent(
        project_id=project_id,
        name=event_data.name,
        event_type=event_data.event_type,
        start_time=event_data.start_time,
        end_time=event_data.end_time
    )
    
    session.add(survey_event)
    session.commit()
    session.refresh(survey_event)
    
    return {
        "id": survey_event.id,
        "project_id": survey_event.project_id,
        "name": survey_event.name,
        "event_type": survey_event.event_type,
        "start_time": survey_event.start_time.isoformat(),
        "end_time": survey_event.end_time.isoformat()
    }

@router.get("/projects/{project_id}/events")
def read_project_events(
    project_id: int,
    session: Session = Depends(get_session)
):
    """Get all captured events for a project"""
    from domain.fsa import SurveyEvent
    
    events = session.exec(
        select(SurveyEvent)
        .where(SurveyEvent.project_id == project_id)
        .order_by(SurveyEvent.start_time)
    ).all()
    
    return events

@router.put("/events/{event_id}")
def update_survey_event(
    event_id: int,
    event_data: CaptureEventRequest,
    session: Session = Depends(get_session)
):
    """Update an existing captured event"""
    from domain.fsa import SurveyEvent
    
    event = session.get(SurveyEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields
    event.name = event_data.name
    event.event_type = event_data.event_type
    event.start_time = event_data.start_time
    event.end_time = event_data.end_time
    
    session.add(event)
    session.commit()
    session.refresh(event)
    
    return {
        "id": event.id,
        "project_id": event.project_id,
        "name": event.name,
        "event_type": event.event_type,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat()
    }

@router.delete("/events/{event_id}")
def delete_survey_event(
    event_id: int,
    session: Session = Depends(get_session)
):
    """Delete a captured event"""
    from domain.fsa import SurveyEvent
    
    event = session.get(SurveyEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    session.delete(event)
    session.commit()
    
    return {"message": "Event deleted successfully"}

# ==========================================
# COLLABORATORS
# ==========================================

@router.get("/projects/{project_id}/collaborators")
def list_collaborators(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all collaborators for a project."""
    from domain.fsa import FsaProject, FsaProjectCollaborator
    from domain.auth import User as UserModel
    
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    statement = select(UserModel).join(FsaProjectCollaborator).where(
        FsaProjectCollaborator.project_id == project_id
    )
    return session.exec(statement).all()

@router.post("/projects/{project_id}/collaborators")
def add_collaborator(
    project_id: int,
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a collaborator to a project. Only owner or admin can add."""
    from domain.fsa import FsaProject, FsaProjectCollaborator
    from domain.auth import User as UserModel
    
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only owner or admin can add collaborators
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can add collaborators")
    
    # Find user by username
    user_to_add = session.exec(select(UserModel).where(UserModel.username == username)).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a collaborator
    existing = session.exec(select(FsaProjectCollaborator).where(
        FsaProjectCollaborator.project_id == project_id,
        FsaProjectCollaborator.user_id == user_to_add.id
    )).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    # Add collaborator
    link = FsaProjectCollaborator(project_id=project_id, user_id=user_to_add.id)
    session.add(link)
    session.commit()
    
    return user_to_add

@router.delete("/projects/{project_id}/collaborators/{user_id}")
def remove_collaborator(
    project_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a collaborator from a project. Only owner or admin can remove."""
    from domain.fsa import FsaProject, FsaProjectCollaborator
    
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only owner or admin can remove collaborators
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")
    
    link = session.exec(select(FsaProjectCollaborator).where(
        FsaProjectCollaborator.project_id == project_id,
        FsaProjectCollaborator.user_id == user_id
    )).first()
    
    if link:
        session.delete(link)
        session.commit()
    
    return {"message": "Collaborator removed"}
