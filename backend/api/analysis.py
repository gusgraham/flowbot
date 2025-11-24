from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from database import get_session
from services.analysis import RainfallService
from domain.analysis import AnalysisProject, AnalysisProjectCreate, AnalysisProjectRead

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
async def upload_analysis_dataset(
    project_id: int,
    file: UploadFile = File(...),
    dataset_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    # Ensure directory exists
    upload_dir = f"data/analysis/{project_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Detect type and parse
    filename = file.filename.lower()
    variable_type = "Unknown"
    metadata = {}
    
    try:
        if filename.endswith('.r'):
            # .R files are always rainfall
            data = import_r_file(file_path)
            variable_type = "Rainfall"
            metadata = {
                "gauge_name": data["name"],
                "interval": data["interval_minutes"],
                "start": data["start_time"].isoformat(),
                "end": data["end_time"].isoformat()
            }
        elif filename.endswith('.fdv'):
            # .FDV files are always flow/depth
            data = import_fdv_file(file_path)
            variable_type = "Flow/Depth"
            metadata = {
                "monitor_name": data["name"],
                "interval": data["interval_minutes"],
                "start": data["start_time"].isoformat(),
                "end": data["end_time"].isoformat(),
                "units": data["units"]
            }
        elif filename.endswith('.std'):
            # .STD files require user to specify type
            if dataset_type == "Rainfall":
                data = import_r_file(file_path)
                variable_type = "Rainfall"
                metadata = {
                    "gauge_name": data["name"],
                    "interval": data["interval_minutes"],
                    "start": data["start_time"].isoformat(),
                    "end": data["end_time"].isoformat()
                }
            elif dataset_type == "Flow/Depth":
                data = import_fdv_file(file_path)
                variable_type = "Flow/Depth"
                metadata = {
                    "monitor_name": data["name"],
                    "interval": data["interval_minutes"],
                    "start": data["start_time"].isoformat(),
                    "end": data["end_time"].isoformat(),
                    "units": data["units"]
                }
            else:
                os.remove(file_path)
                raise HTTPException(status_code=400, detail="For .STD files, please specify dataset_type as 'Rainfall' or 'Flow/Depth'")

    except Exception as e:
        # If parsing fails, remove file and error
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    dataset = AnalysisDataset(
        project_id=project_id,
        name=file.filename,
        variable=variable_type,
        file_path=file_path,
        metadata_json=json.dumps(metadata)
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset

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
    try:
        existing_metadata = json.loads(dataset.metadata_json)
    except:
        existing_metadata = {}
    
    existing_metadata.update(updates)
    dataset.metadata_json = json.dumps(existing_metadata)
    
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    
    return dataset


def get_rainfall_service(session: Session = Depends(get_session)) -> RainfallService:
    return RainfallService(session)

@router.get("/analysis/rainfall/{dataset_id}/cumulative")
def get_cumulative_rainfall(
    dataset_id: int, 
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None),
    service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    # Not implemented in service yet, but keeping endpoint structure
    return {}

@router.get("/analysis/rainfall/{dataset_id}/completeness")
def check_data_completeness(
    dataset_id: int, 
    service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    return service.check_data_completeness(dataset_id)

def get_event_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import EventService
    return EventService(session)

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
    service: Any = Depends(get_fdv_service)
) -> Dict[str, Any]:
    """Get time-series data (flow, depth, velocity) for FDV dataset"""
    data = service.get_scatter_data(dataset_id, start_date, end_date)
    # Convert to time-series format
    timeseries = []
    for point in data:
        timeseries.append({
            "time": point['time'].isoformat() if hasattr(point['time'], 'isoformat') else str(point['time']),
            "depth": point.get('depth', 0),
            "flow": point.get('flow', 0),
            "velocity": point.get('velocity', 0)
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
