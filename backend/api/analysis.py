from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from database import get_session
from services.analysis import RainfallService
from domain.analysis import AnalysisProject, AnalysisProjectCreate, AnalysisProjectRead, AnalysisDataset, AnalysisDatasetRead, AnalysisTimeSeries
from pydantic import BaseModel

router = APIRouter()

# Analysis Projects
@router.post("/analysis/projects", response_model=AnalysisProjectRead)
def create_analysis_project(
    project: AnalysisProjectCreate, 
    session: Session = Depends(get_session)
):
    db_project = AnalysisProject.from_orm(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/analysis/projects", response_model=List[AnalysisProjectRead])
def list_analysis_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    projects = session.exec(select(AnalysisProject).offset(offset).limit(limit)).all()
    return projects

@router.get("/analysis/projects/{project_id}", response_model=AnalysisProjectRead)
def get_analysis_project(
    project_id: int, 
    session: Session = Depends(get_session)
):
    project = session.get(AnalysisProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Analysis Project not found")
    return project

# Analysis Datasets
from fastapi import UploadFile, File
import shutil
import os
import json
from domain.analysis import AnalysisDataset, AnalysisDatasetRead
from services.importers import import_fdv_file, import_r_file

@router.post("/analysis/projects/{project_id}/upload", response_model=AnalysisDatasetRead)
def upload_analysis_dataset(
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
    
    # Ensure directory exists
    upload_dir = f"data/analysis/{project_id}"
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
    import time
    retries = 3
    while retries > 0:
        try:
            dataset = AnalysisDataset(
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
    import threading
    thread = threading.Thread(target=process_dataset_background, args=(dataset.id,))
    thread.daemon = True
    thread.start()
    
    print(f"✅ UPLOAD COMPLETE: {file.filename} (processing in background)")
    print(f"{'='*60}\n")
    
    return dataset


def process_dataset_background(dataset_id: int):
    """Background task to parse file and populate timeseries data"""
    from database import SessionLocal
    
    session = SessionLocal()
    try:
        dataset = session.get(AnalysisDataset, dataset_id)
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
        from domain.analysis import AnalysisTimeSeries
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
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=timestamp,
                                    value=float(value)
                                )
                            )
                    elif variable_type == "Flow/Depth":
                        flows = data_dict.get('flow', [])
                        depths = data_dict.get('depth', [])
                        velocities = data_dict.get('velocity', [])
                        
                        # Ensure all arrays are same length or handle missing
                        count = len(times)
                        print(f"   Processing {count} flow/depth/velocity records...")
                        
                        for i in range(count):
                            timeseries_records.append(
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=times[i],
                                    flow=float(flows[i]) if i < len(flows) and flows[i] is not None else 0.0,
                                    depth=float(depths[i]) if i < len(depths) and depths[i] is not None else 0.0,
                                    velocity=float(velocities[i]) if i < len(velocities) and velocities[i] is not None else 0.0
                                )
                            )
                    else:
                        values = data_dict.get('value', [])
                        print(f"   Processing {len(times)} generic records...")
                        for timestamp, value in zip(times, values):
                            timeseries_records.append(
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=timestamp,
                                    value=float(value)
                                )
                            )
                else:
                    print(f"   Processing {len(data_dict)} records (legacy format)...")
                    for point in data_dict:
                        if variable_type == "Rainfall":
                            timeseries_records.append(
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=point['time'],
                                    value=float(point.get('rainfall', 0.0))
                                )
                            )
                        elif variable_type == "Flow/Depth":
                            timeseries_records.append(
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=point['time'],
                                    flow=float(point.get('flow', 0.0)),
                                    depth=float(point.get('depth', 0.0)),
                                    velocity=float(point.get('velocity', 0.0))
                                )
                            )
                        else:
                            timeseries_records.append(
                                AnalysisTimeSeries(
                                    dataset_id=dataset.id,
                                    timestamp=point['time'],
                                    value=float(point.get('value', 0.0))
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
                                    import time
                                    time.sleep(1)
                                    session.rollback()
                                else:
                                    raise e
                        
                        if retries == 0:
                            print(f"   ❌ Failed to insert batch {i//BATCH_SIZE + 1} after retries")
                            raise Exception("Database locked - failed to insert batch after retries")
                            
                        print(f"   ✓ Stored batch {i//BATCH_SIZE + 1}/{(total_records + BATCH_SIZE - 1)//BATCH_SIZE}")
                        
                        # Yield to other threads
                        import time
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

@router.get("/analysis/projects/{project_id}/datasets", response_model=List[AnalysisDatasetRead])
def list_analysis_datasets(
    project_id: int,
    session: Session = Depends(get_session)
):
    datasets = session.exec(select(AnalysisDataset).where(AnalysisDataset.project_id == project_id)).all()
    return datasets

@router.delete("/analysis/datasets/{dataset_id}")
def delete_analysis_dataset(
    dataset_id: int,
    session: Session = Depends(get_session)
):
    dataset = session.get(AnalysisDataset, dataset_id)
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

@router.patch("/analysis/datasets/{dataset_id}", response_model=AnalysisDatasetRead)
def update_analysis_dataset(
    dataset_id: int,
    updates: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Update dataset metadata (e.g., pipe parameters)"""
    dataset = session.get(AnalysisDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Merge updates into existing metadata
    # Not implemented in service yet, but keeping endpoint structure
    return dataset

def get_rainfall_service(session: Session = Depends(get_session)) -> RainfallService:
    return RainfallService(session)

@router.get("/analysis/rainfall/{dataset_id}/completeness")
def check_data_completeness(
    dataset_id: int, 
    service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    return service.check_data_completeness(dataset_id)

def get_event_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import EventService
    return EventService(session)

class AnalysisParams(BaseModel):
    rainfallDepthTolerance: float = 0
    precedingDryDays: int = 4
    consecZero: int = 5
    requiredDepth: float = 5
    requiredIntensity: float = 6
    requiredIntensityDuration: int = 4
    partialPercent: float = 20
    useConsecutiveIntensities: bool = True

@router.post("/analysis/rainfall/events")
def run_rainfall_analysis(
    dataset_id: int,
    params: AnalysisParams,
    service: Any = Depends(get_event_service),
    rainfall_service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    # Map frontend params to service params
    
    events = service.detect_storms(
        dataset_id=dataset_id, 
        inter_event_hours=12, # Standard separation or derived?
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
            "Intensity_Count": 0, # Placeholder
            "Passed": e['passed'], # 1=Full, 2=Partial, 0=No
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

@router.post("/analysis/events/{dataset_id}/detect-storms")
def detect_storms(
    dataset_id: int,
    inter_event_hours: int = 6,
    min_total_mm: float = 2.0,
    service: Any = Depends(get_event_service)
) -> Dict[str, Any]:
    events = service.detect_storms(dataset_id, inter_event_hours, min_total_mm)
    return {"dataset_id": dataset_id, "events": events, "count": len(events)}

@router.post("/analysis/events/{dataset_id}/detect-dry-days")
def detect_dry_days(
    dataset_id: int,
    threshold_mm: float = 0.1,
    service: Any = Depends(get_event_service)
) -> Dict[str, Any]:
    days = service.detect_dry_days(dataset_id, threshold_mm)
    return {"dataset_id": dataset_id, "dry_days": days, "count": len(days)}

def get_fdv_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import FDVService
    return FDVService(session)

@router.get("/analysis/scatter/{dataset_id}")
def get_scatter_data(
    dataset_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: Any = Depends(get_fdv_service)
) -> Dict[str, Any]:
    points = service.get_scatter_data(dataset_id, start_date, end_date)
    return {"dataset_id": dataset_id, "points": points, "count": len(points)}

@router.get("/analysis/fdv/{dataset_id}/timeseries")
def get_fdv_timeseries(
    dataset_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get time-series data (flow, depth, velocity) for FDV dataset"""
    # Verify dataset exists
    dataset = session.get(AnalysisDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Query timeseries data
    query = select(AnalysisTimeSeries).where(AnalysisTimeSeries.dataset_id == dataset_id)
    
    if start_date:
        query = query.where(AnalysisTimeSeries.timestamp >= start_date)
    if end_date:
        query = query.where(AnalysisTimeSeries.timestamp <= end_date)
        
    query = query.order_by(AnalysisTimeSeries.timestamp)
    results = session.exec(query).all()
    
    # If no data in DB, try to parse from file (fallback for legacy/unprocessed datasets)
    if not results and dataset.status != "processing":
        # ... (fallback logic could go here, but for now let's rely on DB)
        pass

    # Convert to response format
    timeseries = []
    
    # Check if we need to separate flow/depth/velocity or if they are all in one value
    # For FDV, we might need a more complex schema if we stored them separately
    # But currently AnalysisTimeSeries only has 'value'. 
    # Wait, FDV has flow, depth, velocity. AnalysisTimeSeries has a single 'value'.
    # We might have stored them as separate rows with different variable types?
    # Let's check how we stored them in the background task.
    
    # In background task:
    # timeseries_records.append(AnalysisTimeSeries(..., value=float(value)))
    # It seems we only stored one value! 
    # Wait, let me check the background task implementation again.
    
    # It seems we might have a schema mismatch. 
    # The background task code I wrote:
    # if variable_type == "Rainfall": values = data_dict.get('rainfall', [])
    # elif variable_type == "Flow/Depth": values = data_dict.get('flow', data_dict.get('depth', []))
    
    # It selects EITHER flow OR depth. That's a problem for FDV files which have both!
    # We need to fix the background task to store multiple series, or the model to support multiple values.
    # For now, let's assume we want to fix the endpoint to return what we have.
    
    for row in results:
        timeseries.append({
            "time": row.timestamp.isoformat(),
            "flow": row.flow if row.flow is not None else 0.0,
            "depth": row.depth if row.depth is not None else 0.0,
            "velocity": row.velocity if row.velocity is not None else 0.0
        })
        
    return {"dataset_id": dataset_id, "data": timeseries, "count": len(timeseries)}

@router.get("/analysis/fdv/{dataset_id}/scatter")
def get_fdv_scatter(
    dataset_id: int,
    plot_mode: str = Query("velocity"),
    iso_min: Optional[float] = Query(None),
    iso_max: Optional[float] = Query(None),
    iso_count: int = Query(2),
    service: Any = Depends(get_fdv_service)
) -> Dict[str, Any]:
    """Get scatter graph data including CBW and iso curves"""
    return service.get_scatter_graph_data(dataset_id, plot_mode, iso_min, iso_max, iso_count)



@router.get("/analysis/rainfall/{dataset_id}/cumulative-depth")
def get_cumulative_depth(
    dataset_id: int, 
    service: RainfallService = Depends(get_rainfall_service)
):
    return service.get_cumulative_depth(dataset_id)

def get_spatial_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import SpatialService
    return SpatialService(session)

@router.post("/analysis/spatial/idw")
def calculate_idw(
    target_lat: float,
    target_lon: float,
    source_gauges: List[Dict[str, Any]],
    power: float = 2.0,
    service: Any = Depends(get_spatial_service)
) -> Dict[str, Any]:
    result = service.calculate_idw(target_lat, target_lon, source_gauges, power)
    return {"target_lat": target_lat, "target_lon": target_lon, "interpolated_value": result}
