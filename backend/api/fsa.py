from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
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
    FsaTimeSeries
)
from services.importers import import_fdv_file, import_r_file
from services.fsa_services import FsaRainfallService, FsaEventService, FsaFDVService
from pydantic import BaseModel

router = APIRouter(prefix="/fsa", tags=["Flow Survey Analysis"])

# ==========================================
# PROJECTS
# ==========================================

@router.post("/projects/", response_model=FsaProjectRead)
def create_project(project: FsaProjectCreate, session: Session = Depends(get_session)):
    db_project = FsaProject(**project.model_dump())
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=List[FsaProjectRead])
def read_projects(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session)
):
    projects = session.exec(select(FsaProject).offset(offset).limit(limit)).all()
    return projects

@router.get("/projects/{project_id}", response_model=FsaProjectRead)
def read_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(FsaProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# ==========================================
# FILE UPLOAD
# ==========================================

@router.post("/projects/{project_id}/upload", response_model=FsaDatasetRead)
def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    dataset_type: Optional[str] = None,
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
    rainfallDepthTolerance: float = 0
    precedingDryDays: int = 4
    consecZero: int = 5
    requiredDepth: float = 5
    requiredIntensity: float = 6
    requiredIntensityDuration: int = 4
    partialPercent: float = 20
    useConsecutiveIntensities: bool = True

@router.post("/rainfall/events")
def run_rainfall_analysis(
    dataset_id: int,
    params: AnalysisParams,
    service: FsaEventService = Depends(get_event_service),
    rainfall_service: FsaRainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    events = service.detect_storms(
        dataset_id=dataset_id, 
        inter_event_hours=12,
        min_total_mm=params.requiredDepth,
        min_intensity=params.requiredIntensity,
        min_intensity_duration=params.requiredIntensityDuration,
        partial_percent=params.partialPercent
    )
    
    dry_days = service.detect_dry_days(
        dataset_id=dataset_id,
        threshold_mm=0.1
    )
    
    # Get full timeseries for the graph
    timeseries_data = rainfall_service.get_rainfall_timeseries(dataset_id)

    # Calculate stats
    total_rainfall = sum(e['total_mm'] for e in events if e['status'] == 'Event')
    
    # Get period from events or dataset
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
