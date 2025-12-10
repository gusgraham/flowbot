from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, Field
from pydantic import BaseModel
import shutil
import os
import json
import queue
import threading
from pathlib import Path
import pandas as pd

# Import domain models
from domain.ssd import (
    SSDProject, SSDProjectCreate, SSDProjectRead, SSDProjectUpdate, SSDDataset, SSDResult, SSDResultRead,
    CSOAsset, CSOAssetCreate, CSOAssetRead, CSOAssetUpdate,
    AnalysisConfig, AnalysisConfigCreate, AnalysisConfigRead, AnalysisConfigUpdate,
    AnalysisScenario, AnalysisScenarioCreate, AnalysisScenarioRead, AnalysisScenarioUpdate
)
from domain.auth import User
from database import get_session
from api.deps import get_current_active_user

# Import core PLATO engine
from engines.plato.refactored.engine import StorageAnalyzer
from engines.plato.refactored.config import DataSourceInfo, ScenarioSettings
from engines.plato.refactored.models import CSOConfiguration, CSOAnalysisResult

router = APIRouter(prefix="/ssd", tags=["Spill Storage Design"])

DATA_DIR = Path("data/ssd")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def lttb_downsample(df: pd.DataFrame, target_points: int) -> pd.DataFrame:
    """
    LTTB (Largest Triangle Three Buckets) downsampling algorithm.
    
    Preserves visual shape of the data by selecting points that create the largest triangles,
    effectively keeping peaks and troughs while reducing point count.
    
    Args:
        df: DataFrame with time-series data
        target_points: Approximate number of points to keep
        
    Returns:
        Downsampled DataFrame
    """
    import numpy as np
    
    n_points = len(df)
    if target_points >= n_points or target_points < 3:
        return df
    
    # Use the first numeric column as the value column for LTTB
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        # Fall back to simple downsampling if no numeric columns
        return df.iloc[::max(1, n_points // target_points)]
    
    # Use Spill_Flow or first numeric column as the primary value for point selection
    value_col = 'Spill_Flow' if 'Spill_Flow' in numeric_cols else numeric_cols[0]
    
    # LTTB algorithm
    selected_indices = [0]  # Always keep first point
    bucket_size = (n_points - 2) / (target_points - 2)
    
    values = df[value_col].values
    x_values = np.arange(n_points)  # Use index as x-axis
    
    a = 0  # Point a (selected in previous bucket)
    
    for i in range(target_points - 2):
        # Calculate bucket boundaries
        bucket_start = int((i + 1) * bucket_size) + 1
        bucket_end = int((i + 2) * bucket_size) + 1
        bucket_end = min(bucket_end, n_points)
        
        next_bucket_start = int((i + 2) * bucket_size) + 1
        next_bucket_end = int((i + 3) * bucket_size) + 1
        next_bucket_end = min(next_bucket_end, n_points)
        
        # Calculate average point for next bucket
        if next_bucket_end <= n_points and next_bucket_end > next_bucket_start:
            avg_x = np.mean(x_values[next_bucket_start:next_bucket_end])
            avg_y = np.mean(values[next_bucket_start:next_bucket_end])
        else:
            avg_x = x_values[-1]
            avg_y = values[-1]
        
        # Find the point in current bucket that creates largest triangle
        max_area = -1
        max_area_idx = bucket_start
        
        for j in range(bucket_start, bucket_end):
            # Calculate triangle area using cross product
            area = abs(
                (x_values[a] - avg_x) * (values[j] - values[a]) -
                (x_values[a] - x_values[j]) * (avg_y - values[a])
            )
            if area > max_area:
                max_area = area
                max_area_idx = j
        
        selected_indices.append(max_area_idx)
        a = max_area_idx
    
    selected_indices.append(n_points - 1)  # Always keep last point
    
    return df.iloc[selected_indices].reset_index(drop=True)


def detect_csv_date_format(csv_file: str | Path, sample_size: int = 10) -> str | None:
    """
    Auto-detect the date format in a CSV file's Time column.
    
    Samples the Time column and tries common ICM export formats to find
    the fastest explicit format for parsing (avoids slow dateutil fallback).
    
    Args:
        csv_file: Path to CSV file to sample
        sample_size: Number of rows to sample
        
    Returns:
        Date format string (e.g., '%d/%m/%Y %H:%M:%S') or None if auto-detection works
    """
    import warnings
    
    try:
        # Read sample rows without parsing dates
        df_sample = pd.read_csv(csv_file, nrows=sample_size)
        
        if 'Time' not in df_sample.columns:
            return None
        
        # Try to parse with pandas auto-detection (dayfirst=True)
        # Check if pandas can infer a consistent format (fast path)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                pd.to_datetime(df_sample['Time'], dayfirst=True, errors='raise')
                
                # Check if we got the "could not infer format" warning
                # This means pandas is using slow dateutil fallback
                has_infer_warning = any(
                    "Could not infer format" in str(warning.message)
                    for warning in w
                )
                
                if not has_infer_warning:
                    # Success - pandas can efficiently auto-parse, no explicit format needed
                    return None
            except Exception:
                pass
        
        # Try common ICM export formats
        common_formats = [
            '%d/%m/%Y %H:%M:%S',  # 01/12/2023 14:30:00
            '%d-%m-%y %H:%M',      # 01-12-23 14:30
            '%d/%m/%Y %H:%M',      # 01/12/2023 14:30
            '%Y-%m-%d %H:%M:%S',   # 2023-12-01 14:30:00
            '%d/%m/%y %H:%M:%S',   # 01/12/23 14:30:00
            '%d-%m-%Y %H:%M:%S',   # 01-12-2023 14:30:00
            '%Y-%m-%dT%H:%M:%S',   # 2023-12-01T14:30:00 (ISO)
        ]
        
        for fmt in common_formats:
            try:
                pd.to_datetime(df_sample['Time'], format=fmt, errors='raise')
                # Success - found matching format
                return fmt
            except Exception:
                continue
        
        # Could not find an explicit format, return None to use slow fallback
        return None
        
    except Exception:
        return None


# ==========================================
# PYDANTIC MODELS FOR API
# ==========================================

class SSDAnalysisConfig(BaseModel):
    """Configuration for CSO storage analysis."""
    cso_name: str
    overflow_link: str
    continuation_link: str
    run_suffix: str = "001"
    start_date: str  # ISO format YYYY-MM-DDTHH:MM:SS
    end_date: str
    spill_target_entire: int = 10
    spill_target_bathing: int = -1  # -1 means ignore bathing
    bathing_season_start: str = "15/05"  # DD/MM
    bathing_season_end: str = "30/09"
    pff_increase: float = 0.0
    tank_volume: Optional[float] = None
    pump_rate: float = 0.0
    pumping_mode: str = "Fixed"  # Fixed or Variable
    flow_return_threshold: float = 0.0
    depth_return_threshold: float = 0.0
    time_delay: float = 0.0
    spill_flow_threshold: float = 0.001
    spill_volume_threshold: float = 0.0


class ScenarioAnalysisRequest(BaseModel):
    """Request to run analysis for selected scenarios."""
    scenario_ids: List[int]


class SpillEventResponse(BaseModel):
    """Single spill event in results."""
    start_time: str
    end_time: str
    duration_hours: float
    volume_m3: float
    peak_flow_m3s: float
    is_bathing_season: bool = False


class SSDAnalysisResponse(BaseModel):
    """Response from analysis run."""
    success: bool
    cso_name: str
    converged: bool
    iterations: int
    final_storage_m3: float
    spill_count: int
    bathing_spill_count: int
    total_spill_volume_m3: float
    bathing_spill_volume_m3: float
    total_spill_duration_hours: float
    spill_events: List[SpillEventResponse]
    error: Optional[str] = None


class UploadedFileInfo(BaseModel):
    """Info about an uploaded file."""
    filename: str
    size_bytes: int
    uploaded_at: str


# ==========================================
# PROJECTS
# ==========================================

@router.get("/projects", response_model=List[SSDProjectRead])
def list_projects(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all SSD projects (owned or collaborative)."""
    from domain.ssd import SSDProjectCollaborator
    from sqlmodel import or_, col
    
    if current_user.is_superuser or current_user.role == 'Admin':
        projects = session.exec(
            select(SSDProject).offset(offset).limit(limit)
        ).all()
    else:
        # Include owned projects OR collaborative projects
        collab_subquery = select(SSDProjectCollaborator.project_id).where(
            SSDProjectCollaborator.user_id == current_user.id
        )
        projects = session.exec(
            select(SSDProject).where(
                or_(
                    SSDProject.owner_id == current_user.id,
                    col(SSDProject.id).in_(collab_subquery)
                )
            ).offset(offset).limit(limit)
        ).all()
    return projects


@router.post("/projects", response_model=SSDProjectRead)
def create_project(
    project: SSDProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new SSD project."""
    db_project = SSDProject.model_validate(project)
    db_project.owner_id = current_user.id
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


@router.get("/projects/{project_id}", response_model=SSDProjectRead)
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a single SSD project by ID."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


class DateFormatDetectionResponse(BaseModel):
    """Response from date format detection endpoint."""
    can_auto_parse: bool
    detected_format: Optional[str] = None
    sample_dates: List[str] = []
    current_format: Optional[str] = None
    

@router.get("/projects/{project_id}/detect-date-format", response_model=DateFormatDetectionResponse)
def detect_date_format_endpoint(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Detect date format from project's CSV files."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    csv_files = list(project_dir.glob("*.csv"))
    
    if not csv_files:
        return DateFormatDetectionResponse(
            can_auto_parse=True,
            detected_format=None,
            sample_dates=[],
            current_format=project.date_format
        )
    
    # Sample dates from first file
    sample_dates = []
    try:
        df_sample = pd.read_csv(csv_files[0], nrows=5)
        if 'Time' in df_sample.columns:
            sample_dates = df_sample['Time'].astype(str).tolist()
    except Exception:
        pass
    
    # Detect format
    detected_format = detect_csv_date_format(csv_files[0])
    
    return DateFormatDetectionResponse(
        can_auto_parse=(detected_format is None),
        detected_format=detected_format,
        sample_dates=sample_dates,
        current_format=project.date_format
    )


class DateFormatUpdateRequest(BaseModel):
    """Request to update project's date format."""
    date_format: Optional[str] = None  # None means auto-detect


@router.patch("/projects/{project_id}/date-format")
def update_date_format(
    project_id: int,
    request: DateFormatUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update project's date format setting."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.date_format = request.date_format
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return {
        "message": f"Date format updated to: {request.date_format or 'auto-detect'}",
        "date_format": project.date_format
    }


@router.put("/projects/{project_id}", response_model=SSDProjectRead)
def update_project(
    project_id: int,
    project_update: SSDProjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update an SSD project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = project_update.dict(exclude_unset=True)
    for key, value in project_data.items():
        setattr(project, key, value)
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an SSD project and all associated data."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 1. Delete associated database records
    
    # Datasets
    datasets = session.exec(select(SSDDataset).where(SSDDataset.project_id == project_id)).all()
    for dataset in datasets:
        session.delete(dataset)
        
    # Results
    results = session.exec(select(SSDResult).where(SSDResult.project_id == project_id)).all()
    for result in results:
        session.delete(result)

    # Analysis Scenarios
    scenarios = session.exec(select(AnalysisScenario).where(AnalysisScenario.project_id == project_id)).all()
    for scenario in scenarios:
        session.delete(scenario)

    # CSO Assets
    assets = session.exec(select(CSOAsset).where(CSOAsset.project_id == project_id)).all()
    for asset in assets:
        session.delete(asset)
        
    # Analysis Configs
    configs = session.exec(select(AnalysisConfig).where(AnalysisConfig.project_id == project_id)).all()
    for config in configs:
        session.delete(config)
        
    # 2. Delete Project record
    session.delete(project)
    session.commit()
    
    # 3. Clean up files
    project_dir = DATA_DIR / str(project_id)
    if project_dir.exists() and project_dir.is_dir():
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            print(f"Error deleting project directory: {e}")
            
    return {"ok": True}


# ==========================================
# FILE UPLOAD & MANAGEMENT
# ==========================================

@router.post("/projects/{project_id}/upload")
def upload_data(
    project_id: int,
    flow_files: List[UploadFile] = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Upload flow data files for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for file in flow_files:
        file_path = project_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append({
            "filename": file.filename,
            "path": str(file_path)
        })
        
    return {"message": f"Uploaded {len(saved_files)} files", "files": saved_files}


@router.get("/projects/{project_id}/files", response_model=List[UploadedFileInfo])
def list_files(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all uploaded files for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists():
        return []
    
    files = []
    for file_path in project_dir.glob("*.csv"):
        stat = file_path.stat()
        files.append(UploadedFileInfo(
            filename=file_path.name,
            size_bytes=stat.st_size,
            uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
        ))
    
    return files


@router.delete("/projects/{project_id}/files/{filename}")
def delete_file(
    project_id: int,
    filename: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an uploaded file."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_path = DATA_DIR / str(project_id) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    os.remove(file_path)
    return {"message": f"Deleted {filename}"}


@router.get("/projects/{project_id}/links", response_model=List[str])
def get_available_links(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Extract available link names from uploaded CSV files."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists():
        return []
    
    all_links = set()
    
    for csv_file in project_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, nrows=0)
            for col in df.columns:
                col_lower = col.lower()
                if col_lower not in ['time', 'datetime', 'date', 'timestamp']:
                    all_links.add(col)
        except Exception:
            continue
    
    return sorted(list(all_links))


class DateRangeResponse(BaseModel):
    """Date range from uploaded data files."""
    min_date: Optional[str] = None
    max_date: Optional[str] = None


@router.get("/projects/{project_id}/date-range", response_model=DateRangeResponse)
def get_date_range(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Extract available date range from uploaded CSV files.
    
    Parses all CSV files and finds the min/max timestamps from the Time column.
    """
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists():
        return DateRangeResponse()
    
    min_date = None
    max_date = None
    
    import warnings
    
    for csv_file in project_dir.glob("*.csv"):
        try:
            # Only read first and last few rows for efficiency
            # First, peek at header to find time column
            df_head = pd.read_csv(csv_file, nrows=5)
            
            time_col = None
            for col in df_head.columns:
                if col.lower() in ['time', 'datetime', 'date', 'timestamp']:
                    time_col = col
                    break
            
            if not time_col:
                continue
            
            # Read just first and last rows for min/max dates
            # Read first rows
            df_first = pd.read_csv(csv_file, nrows=10, usecols=[time_col])
            
            # Read last rows using tail - need to count lines first
            with open(csv_file, 'r') as f:
                total_lines = sum(1 for _ in f)
            
            skip_rows = max(1, total_lines - 10)  # Skip all but last 10 rows (keep header)
            df_last = pd.read_csv(csv_file, skiprows=range(1, skip_rows), usecols=[time_col])
            
            # Combine and parse dates
            df_combined = pd.concat([df_first, df_last], ignore_index=True)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                if project.date_format:
                    df_combined[time_col] = pd.to_datetime(df_combined[time_col], format=project.date_format)
                else:
                    df_combined[time_col] = pd.to_datetime(df_combined[time_col], dayfirst=True)
            
            file_min = df_combined[time_col].min()
            file_max = df_combined[time_col].max()
            
            if min_date is None or file_min < min_date:
                min_date = file_min
            if max_date is None or file_max > max_date:
                max_date = file_max
        except Exception as e:
            print(f"Error parsing {csv_file.name}: {e}")
            continue
    
    return DateRangeResponse(
        min_date=min_date.isoformat() if min_date else None,
        max_date=max_date.isoformat() if max_date else None
    )


# ==========================================
# CSO ASSETS
# ==========================================

@router.get("/projects/{project_id}/cso-assets", response_model=List[CSOAssetRead])
def list_cso_assets(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all CSO assets for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    assets = session.exec(
        select(CSOAsset).where(CSOAsset.project_id == project_id)
    ).all()
    return assets


@router.post("/projects/{project_id}/cso-assets", response_model=CSOAssetRead)
def create_cso_asset(
    project_id: int,
    asset: CSOAssetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new CSO asset."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    existing = session.exec(
        select(CSOAsset).where(
            CSOAsset.project_id == project_id,
            CSOAsset.name == asset.name
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"CSO asset '{asset.name}' already exists")
    
    db_asset = CSOAsset(
        project_id=project_id,
        name=asset.name,
        overflow_links=asset.overflow_links,
        continuation_link=asset.continuation_link,
        is_effective_link=asset.is_effective_link,
        effective_link_components=asset.effective_link_components
    )
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


@router.put("/projects/{project_id}/cso-assets/{asset_id}", response_model=CSOAssetRead)
def update_cso_asset(
    project_id: int,
    asset_id: int,
    asset_update: CSOAssetUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update a CSO asset."""
    db_asset = session.exec(
        select(CSOAsset).where(
            CSOAsset.id == asset_id,
            CSOAsset.project_id == project_id
        )
    ).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="CSO asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_asset, key, value)
    
    session.add(db_asset)
    session.commit()
    session.refresh(db_asset)
    return db_asset


@router.delete("/projects/{project_id}/cso-assets/{asset_id}")
def delete_cso_asset(
    project_id: int,
    asset_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a CSO asset."""
    db_asset = session.exec(
        select(CSOAsset).where(
            CSOAsset.id == asset_id,
            CSOAsset.project_id == project_id
        )
    ).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="CSO asset not found")
    
    session.delete(db_asset)
    session.commit()
    return {"message": f"Deleted CSO asset '{db_asset.name}'"}


# ==========================================
# ANALYSIS CONFIGURATIONS
# ==========================================

@router.get("/projects/{project_id}/analysis-configs", response_model=List[AnalysisConfigRead])
def list_analysis_configs(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all analysis configurations for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    configs = session.exec(
        select(AnalysisConfig).where(AnalysisConfig.project_id == project_id)
    ).all()
    return configs


@router.post("/projects/{project_id}/analysis-configs", response_model=AnalysisConfigRead)
def create_analysis_config(
    project_id: int,
    config: AnalysisConfigCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new analysis configuration."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    existing = session.exec(
        select(AnalysisConfig).where(
            AnalysisConfig.project_id == project_id,
            AnalysisConfig.name == config.name
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Configuration '{config.name}' already exists")
    
    db_config = AnalysisConfig(
        project_id=project_id,
        name=config.name,
        mode=config.mode,
        model=config.model,
        start_date=config.start_date,
        end_date=config.end_date,
        spill_target=config.spill_target,
        spill_target_bathing=config.spill_target_bathing,
        bathing_season_start=config.bathing_season_start,
        bathing_season_end=config.bathing_season_end,
        spill_flow_threshold=config.spill_flow_threshold,
        spill_volume_threshold=config.spill_volume_threshold
    )
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


@router.put("/projects/{project_id}/analysis-configs/{config_id}", response_model=AnalysisConfigRead)
def update_analysis_config(
    project_id: int,
    config_id: int,
    config_update: AnalysisConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update an analysis configuration."""
    db_config = session.exec(
        select(AnalysisConfig).where(
            AnalysisConfig.id == config_id,
            AnalysisConfig.project_id == project_id
        )
    ).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Analysis configuration not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


@router.delete("/projects/{project_id}/analysis-configs/{config_id}")
def delete_analysis_config(
    project_id: int,
    config_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an analysis configuration."""
    db_config = session.exec(
        select(AnalysisConfig).where(
            AnalysisConfig.id == config_id,
            AnalysisConfig.project_id == project_id
        )
    ).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Analysis configuration not found")
    
    session.delete(db_config)
    session.commit()
    return {"message": f"Deleted configuration '{db_config.name}'"}


# ==========================================
# ANALYSIS SCENARIOS
# ==========================================

@router.get("/projects/{project_id}/scenarios", response_model=List[AnalysisScenarioRead])
def list_scenarios(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all analysis scenarios for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenarios = session.exec(
        select(AnalysisScenario).where(AnalysisScenario.project_id == project_id)
    ).all()
    return scenarios


@router.post("/projects/{project_id}/scenarios", response_model=AnalysisScenarioRead)
def create_scenario(
    project_id: int,
    scenario: AnalysisScenarioCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new analysis scenario."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate CSO asset exists
    cso_asset = session.get(CSOAsset, scenario.cso_asset_id)
    if not cso_asset or cso_asset.project_id != project_id:
        raise HTTPException(status_code=400, detail="CSO asset not found in this project")
    
    # Validate config exists
    config = session.get(AnalysisConfig, scenario.config_id)
    if not config or config.project_id != project_id:
        raise HTTPException(status_code=400, detail="Configuration not found in this project")
    
    # Check for duplicate scenario name
    existing = session.exec(
        select(AnalysisScenario).where(
            AnalysisScenario.project_id == project_id,
            AnalysisScenario.scenario_name == scenario.scenario_name
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Scenario '{scenario.scenario_name}' already exists")
    
    db_scenario = AnalysisScenario(
        project_id=project_id,
        scenario_name=scenario.scenario_name,
        cso_asset_id=scenario.cso_asset_id,
        config_id=scenario.config_id,
        pff_increase=scenario.pff_increase,
        pumping_mode=scenario.pumping_mode,
        pump_rate=scenario.pump_rate,
        time_delay=scenario.time_delay,
        flow_return_threshold=scenario.flow_return_threshold,
        depth_return_threshold=scenario.depth_return_threshold,
        tank_volume=scenario.tank_volume
    )
    session.add(db_scenario)
    session.commit()
    session.refresh(db_scenario)
    return db_scenario


@router.put("/projects/{project_id}/scenarios/{scenario_id}", response_model=AnalysisScenarioRead)
def update_scenario(
    project_id: int,
    scenario_id: int,
    scenario_update: AnalysisScenarioUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update an analysis scenario."""
    db_scenario = session.exec(
        select(AnalysisScenario).where(
            AnalysisScenario.id == scenario_id,
            AnalysisScenario.project_id == project_id
        )
    ).first()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    update_data = scenario_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scenario, key, value)
    
    session.add(db_scenario)
    session.commit()
    session.refresh(db_scenario)
    return db_scenario


@router.delete("/projects/{project_id}/scenarios/{scenario_id}")
def delete_scenario(
    project_id: int,
    scenario_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an analysis scenario."""
    db_scenario = session.exec(
        select(AnalysisScenario).where(
            AnalysisScenario.id == scenario_id,
            AnalysisScenario.project_id == project_id
        )
    ).first()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    session.delete(db_scenario)
    session.commit()
    return {"message": f"Deleted scenario '{db_scenario.scenario_name}'"}


# ==========================================
# ANALYSIS
# ==========================================

@router.post("/projects/{project_id}/analyze-scenarios")
def run_scenario_analysis(
    project_id: int,
    request: ScenarioAnalysisRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Run storage analysis for selected scenarios using the PLATO engine.
    
    This endpoint builds CSOConfiguration from database entities and runs
    the StorageAnalyzer for each selected scenario.
    """
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists() or not list(project_dir.glob("*.csv")):
        raise HTTPException(status_code=400, detail="No data files uploaded. Please upload CSV files first.")
    
    if not request.scenario_ids:
        raise HTTPException(status_code=400, detail="No scenarios selected")
    
    # Run analysis for each scenario
    results = []
    for scenario_id in request.scenario_ids:
        scenario = session.get(AnalysisScenario, scenario_id)
        if not scenario or scenario.project_id != project_id:
            results.append({
                "scenario_id": scenario_id,
                "scenario_name": f"Unknown",
                "status": "error",
                "message": f"Scenario {scenario_id} not found or doesn't belong to this project"
            })
            continue
        
        # Get the CSO asset and config
        cso_asset = session.get(CSOAsset, scenario.cso_asset_id)
        config = session.get(AnalysisConfig, scenario.config_id)
        
        if not cso_asset:
            results.append({
                "scenario_id": scenario.id,
                "scenario_name": scenario.scenario_name,
                "status": "error",
                "message": f"CSO asset not found"
            })
            continue
            
        if not config:
            results.append({
                "scenario_id": scenario.id,
                "scenario_name": scenario.scenario_name,
                "status": "error",
                "message": f"Analysis configuration not found"
            })
            continue
        
        try:
            # Build CSOConfiguration from database entities
            # Combine CSO asset links with config time settings and scenario interventions
            legacy_config = {
                'CSO Name': cso_asset.name,
                'Overflow Links': cso_asset.overflow_links,
                'Continuation Link': cso_asset.continuation_link,
                'Run Suffix': scenario.scenario_name[:3].upper(),  # Use scenario name as run suffix
                'Start Date (dd/mm/yy hh:mm:ss)': config.start_date.strftime('%d/%m/%Y %H:%M:%S'),
                'End Date (dd/mm/yy hh:mm:ss)': config.end_date.strftime('%d/%m/%Y %H:%M:%S'),
                'Spill Target (Entire Period)': config.spill_target,
                'Spill Target (Bathing Seasons)': config.spill_target_bathing or 0,
                'Bathing Season Start (dd/mm)': config.bathing_season_start or '15/05',
                'Bathing Season End (dd/mm)': config.bathing_season_end or '30/09',
                # Intervention parameters from scenario
                'PFF Increase (m3/s)': scenario.pff_increase,
                'Tank Volume (m3)': scenario.tank_volume,
                'Pump Rate (m3/s)': scenario.pump_rate,
                'Pumping Mode': scenario.pumping_mode,
                'Flow Return Threshold (m3/s)': scenario.flow_return_threshold,
                'Depth Return Threshold (m)': scenario.depth_return_threshold,
                'Time Delay (hours)': scenario.time_delay,
                # Thresholds from config
                'Spill Flow Threshold (m3/s)': config.spill_flow_threshold,
                'Spill Volume Threshold (m3)': config.spill_volume_threshold,
            }
            
            cso_config = CSOConfiguration.from_dict(legacy_config)
            
            # Validate config
            errors = cso_config.validate()
            if errors:
                results.append({
                    "scenario_id": scenario.id,
                    "scenario_name": scenario.scenario_name,
                    "cso_name": cso_asset.name,
                    "config_name": config.name,
                    "status": "error",
                    "message": f"Configuration error: {', '.join(errors)}"
                })
                continue
            
            # Setup data source - detect timestep from first CSV
            csv_files = list(project_dir.glob("*.csv"))
            timestep_seconds = 120  # Default: 2 minutes
            date_format = None
            if csv_files:
                # Detect date format for fast parsing
                date_format = detect_csv_date_format(csv_files[0])
                
                try:
                    df_sample = pd.read_csv(csv_files[0], nrows=10)
                    if 'Time' in df_sample.columns:
                        df_sample['Time'] = pd.to_datetime(df_sample['Time'], dayfirst=True)
                        if len(df_sample) >= 2:
                            delta = (df_sample['Time'].iloc[1] - df_sample['Time'].iloc[0]).total_seconds()
                            if delta > 0:
                                timestep_seconds = int(delta)
                except Exception:
                    pass  # Use default timestep
            
            data_source = DataSourceInfo(
                data_folder=project_dir,
                file_type="csv",
                timestep_seconds=timestep_seconds,
                date_format=date_format
            )
            
            # Setup scenario settings
            scenario_settings = ScenarioSettings(
                name=scenario.scenario_name,
                spill_target=config.spill_target,
                bathing_spill_target=config.spill_target_bathing or 0,
                spill_flow_threshold=config.spill_flow_threshold,
                spill_volume_threshold=config.spill_volume_threshold,
            )
            
            # Collect log messages from the engine
            log_messages = []
            def progress_callback(message: str):
                log_messages.append(message)
            
            # Run the PLATO analysis engine with progress callback
            analyzer = StorageAnalyzer(cso_config, data_source, scenario_settings, progress_callback=progress_callback)
            result: CSOAnalysisResult = analyzer.run()
            
            # Convert spill events to serializable format
            spill_events = []
            for event in result.spill_events:
                is_bathing = event.is_in_bathing_season(
                    cso_config.bathing_season_start.month,
                    cso_config.bathing_season_start.day,
                    cso_config.bathing_season_end.month,
                    cso_config.bathing_season_end.day
                ) if (config.spill_target_bathing or 0) > 0 else False
                
                spill_events.append({
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "duration_hours": round(event.spill_duration_hours, 2),
                    "volume_m3": round(event.volume_m3, 1),
                    "peak_flow_m3s": round(event.peak_flow_m3s, 4),
                    "is_bathing_season": is_bathing
                })
            
            # Save time-series to Parquet file
            results_dir = project_dir / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            ts_filename = f"ts_{scenario.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            ts_path = results_dir / ts_filename
            result.time_series.to_parquet(ts_path, index=False)
            
            # Delete existing result(s) for this scenario (overwrite behavior)
            existing_results = session.exec(
                select(SSDResult).where(SSDResult.scenario_id == scenario.id)
            ).all()
            for old_result in existing_results:
                # Delete old timeseries file if exists
                if old_result.timeseries_path:
                    old_ts = Path(old_result.timeseries_path)
                    if old_ts.exists():
                        try:
                            old_ts.unlink()
                        except Exception:
                            pass  # Ignore file deletion errors
                session.delete(old_result)
            
            # Save new result to database
            db_result = SSDResult(
                project_id=project_id,
                scenario_id=scenario.id,
                scenario_name=scenario.scenario_name,
                cso_name=cso_asset.name,
                config_name=config.name,
                start_date=config.start_date,
                end_date=config.end_date,
                pff_increase=scenario.pff_increase,
                tank_volume=scenario.tank_volume or 0.0,
                spill_target=config.spill_target,
                spill_target_bathing=config.spill_target_bathing,
                converged=result.converged,
                iterations=result.iterations_count,
                final_storage_m3=round(result.final_storage_m3, 1),
                spill_count=result.spill_count,
                bathing_spill_count=result.bathing_spills_count,
                total_spill_volume_m3=round(result.total_spill_volume_m3, 1),
                bathing_spill_volume_m3=round(result.bathing_spill_volume_m3, 1),
                total_spill_duration_hours=round(result.total_spill_duration_hours, 2),
                spill_events=spill_events,
                timeseries_path=str(ts_path)
            )
            session.add(db_result)
            session.commit()
            session.refresh(db_result)
            
            results.append({
                "scenario_id": scenario.id,
                "result_id": db_result.id,  # Include saved result ID
                "scenario_name": scenario.scenario_name,
                "cso_name": cso_asset.name,
                "config_name": config.name,
                "status": "success",
                "converged": result.converged,
                "iterations": result.iterations_count,
                "final_storage_m3": round(result.final_storage_m3, 1),
                "spill_count": result.spill_count,
                "bathing_spill_count": result.bathing_spills_count,
                "total_spill_volume_m3": round(result.total_spill_volume_m3, 1),
                "bathing_spill_volume_m3": round(result.bathing_spill_volume_m3, 1),
                "total_spill_duration_hours": round(result.total_spill_duration_hours, 2),
                "spill_events": spill_events,
                "log": log_messages  # Detailed engine output
            })
            
        except Exception as e:
            import traceback
            results.append({
                "scenario_id": scenario.id,
                "scenario_name": scenario.scenario_name,
                "cso_name": cso_asset.name if cso_asset else "Unknown",
                "config_name": config.name if config else "Unknown",
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
    
    # Summarize results
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    
    return {
        "success": successful > 0,
        "message": f"Completed {successful} of {len(results)} scenario(s)" + (f" ({failed} failed)" if failed > 0 else ""),
        "scenarios": results
    }


@router.post("/projects/{project_id}/analyze-stream")
def run_scenario_analysis_stream(
    project_id: int,
    request: ScenarioAnalysisRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Run storage analysis with real-time log streaming via SSE.
    
    This endpoint streams log messages as Server-Sent Events (SSE) so the
    frontend can display progress in real-time during long-running analyses.
    """
    # Validate project and data
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists() or not list(project_dir.glob("*.csv")):
        raise HTTPException(status_code=400, detail="No data files uploaded")
    
    if not request.scenario_ids:
        raise HTTPException(status_code=400, detail="No scenarios selected")
    
    # Pre-fetch all scenario data (must be done before async generator starts)
    scenarios_data = []
    for scenario_id in request.scenario_ids:
        scenario = session.get(AnalysisScenario, scenario_id)
        if not scenario or scenario.project_id != project_id:
            continue
        cso_asset = session.get(CSOAsset, scenario.cso_asset_id)
        config = session.get(AnalysisConfig, scenario.config_id)
        if cso_asset and config:
            scenarios_data.append({
                'scenario': scenario,
                'cso_asset': cso_asset,
                'config': config,
                'scenario_dict': {
                    'id': scenario.id,
                    'scenario_name': scenario.scenario_name,
                    'pff_increase': scenario.pff_increase,
                    'pump_rate': scenario.pump_rate,
                    'pumping_mode': scenario.pumping_mode,
                    'flow_return_threshold': scenario.flow_return_threshold,
                    'depth_return_threshold': scenario.depth_return_threshold,
                    'time_delay': scenario.time_delay,
                    'tank_volume': scenario.tank_volume,
                },
                'cso_dict': {
                    'name': cso_asset.name,
                    'overflow_links': cso_asset.overflow_links,
                    'continuation_link': cso_asset.continuation_link,
                },
                'config_dict': {
                    'name': config.name,
                    'start_date': config.start_date,
                    'end_date': config.end_date,
                    'spill_target': config.spill_target,
                    'spill_target_bathing': config.spill_target_bathing,
                    'bathing_season_start': config.bathing_season_start,
                    'bathing_season_end': config.bathing_season_end,
                    'spill_flow_threshold': config.spill_flow_threshold,
                    'spill_volume_threshold': config.spill_volume_threshold,
                }
            })
    
    # Get date format from project
    project_date_format = project.date_format
    
    def event_generator():
        """Generator that yields SSE events during analysis."""
        results = []
        
        for data in scenarios_data:
            scenario_dict = data['scenario_dict']
            cso_dict = data['cso_dict']
            config_dict = data['config_dict']
            
            # Send scenario start event
            yield f"data: {json.dumps({'type': 'scenario_start', 'scenario_name': scenario_dict['scenario_name'], 'cso_name': cso_dict['name']})}\n\n"
            
            try:
                # Build CSOConfiguration
                legacy_config = {
                    'CSO Name': cso_dict['name'],
                    'Overflow Links': cso_dict['overflow_links'],
                    'Continuation Link': cso_dict['continuation_link'],
                    'Run Suffix': scenario_dict['scenario_name'][:3].upper(),
                    'Start Date (dd/mm/yy hh:mm:ss)': config_dict['start_date'].strftime('%d/%m/%Y %H:%M:%S'),
                    'End Date (dd/mm/yy hh:mm:ss)': config_dict['end_date'].strftime('%d/%m/%Y %H:%M:%S'),
                    'Spill Target (Entire Period)': config_dict['spill_target'],
                    'Spill Target (Bathing Seasons)': config_dict['spill_target_bathing'] or 0,
                    'Bathing Season Start (dd/mm)': config_dict['bathing_season_start'] or '15/05',
                    'Bathing Season End (dd/mm)': config_dict['bathing_season_end'] or '30/09',
                    'PFF Increase (m3/s)': scenario_dict['pff_increase'],
                    'Tank Volume (m3)': scenario_dict['tank_volume'],
                    'Pump Rate (m3/s)': scenario_dict['pump_rate'],
                    'Pumping Mode': scenario_dict['pumping_mode'],
                    'Flow Return Threshold (m3/s)': scenario_dict['flow_return_threshold'],
                    'Depth Return Threshold (m)': scenario_dict['depth_return_threshold'],
                    'Time Delay (hours)': scenario_dict['time_delay'],
                    'Spill Flow Threshold (m3/s)': config_dict['spill_flow_threshold'],
                    'Spill Volume Threshold (m3)': config_dict['spill_volume_threshold'],
                }
                
                cso_config = CSOConfiguration.from_dict(legacy_config)
                errors = cso_config.validate()
                if errors:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Configuration error: {errors}', 'level': 'error'})}\n\n"
                    results.append({'scenario_id': scenario_dict['id'], 'status': 'error', 'message': str(errors)})
                    continue
                
                # Setup data source
                csv_files = list(project_dir.glob("*.csv"))
                timestep_seconds = 120
                date_format = project_date_format
                if not date_format and csv_files:
                    date_format = detect_csv_date_format(csv_files[0])
                
                if csv_files:
                    try:
                        df_sample = pd.read_csv(csv_files[0], nrows=10)
                        if 'Time' in df_sample.columns:
                            df_sample['Time'] = pd.to_datetime(df_sample['Time'], dayfirst=True)
                            if len(df_sample) >= 2:
                                delta = (df_sample['Time'].iloc[1] - df_sample['Time'].iloc[0]).total_seconds()
                                if delta > 0:
                                    timestep_seconds = int(delta)
                    except Exception:
                        pass
                
                data_source = DataSourceInfo(
                    data_folder=project_dir,
                    file_type="csv",
                    timestep_seconds=timestep_seconds,
                    date_format=date_format
                )
                
                scenario_settings = ScenarioSettings(
                    name=scenario_dict['scenario_name'],
                    spill_target=config_dict['spill_target'],
                    bathing_spill_target=config_dict['spill_target_bathing'] or 0,
                    spill_flow_threshold=config_dict['spill_flow_threshold'],
                    spill_volume_threshold=config_dict['spill_volume_threshold'],
                )
                
                # Progress callback that yields SSE events
                def progress_callback(message: str):
                    # Can't yield from nested function, so we use a different approach
                    pass
                
                # For SSE, we use threading with a queue for true real-time streaming
                log_queue = queue.Queue()
                analysis_done = threading.Event()
                analysis_result = [None]  # Use list to store result from thread
                analysis_error = [None]
                
                def run_analysis_thread():
                    """Run analysis in separate thread, pushing logs to queue."""
                    try:
                        def progress_callback(message: str):
                            log_queue.put(('log', message))
                        
                        analyzer = StorageAnalyzer(cso_config, data_source, scenario_settings, progress_callback=progress_callback)
                        analysis_result[0] = analyzer.run()
                    except Exception as e:
                        analysis_error[0] = e
                    finally:
                        analysis_done.set()
                
                # Start analysis thread
                thread = threading.Thread(target=run_analysis_thread)
                thread.start()
                
                # Yield log messages as they arrive (real-time!)
                while not analysis_done.is_set() or not log_queue.empty():
                    try:
                        msg_type, message = log_queue.get(timeout=0.1)
                        if msg_type == 'log':
                            yield f"data: {json.dumps({'type': 'log', 'message': message})}\n\n"
                    except queue.Empty:
                        continue
                
                thread.join()
                
                # Check for errors
                if analysis_error[0]:
                    raise analysis_error[0]
                
                result = analysis_result[0]
                
                # Process spill events
                spill_events = []
                for event in result.spill_events:
                    is_bathing = event.is_in_bathing_season(
                        cso_config.bathing_season_start.month,
                        cso_config.bathing_season_start.day,
                        cso_config.bathing_season_end.month,
                        cso_config.bathing_season_end.day
                    ) if (config_dict['spill_target_bathing'] or 0) > 0 else False
                    
                    spill_events.append({
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat(),
                        "duration_hours": round(event.spill_duration_hours, 2),
                        "volume_m3": round(event.volume_m3, 1),
                        "peak_flow_m3s": round(event.peak_flow_m3s, 4),
                        "is_bathing_season": is_bathing
                    })
                
                # Save timeseries
                results_dir = project_dir / "results"
                results_dir.mkdir(parents=True, exist_ok=True)
                ts_filename = f"ts_{scenario_dict['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                ts_path = results_dir / ts_filename
                result.time_series.to_parquet(ts_path, index=False)
                
                # Save to database - DELETE existing result first (overwrite behavior)
                from database import engine
                from sqlmodel import Session as SQLModelSession
                with SQLModelSession(engine) as db_session:
                    # Delete existing result(s) for this scenario
                    existing_results = db_session.exec(
                        select(SSDResult).where(SSDResult.scenario_id == scenario_dict['id'])
                    ).all()
                    for old_result in existing_results:
                        # Delete old timeseries file if exists
                        if old_result.timeseries_path:
                            old_ts = Path(old_result.timeseries_path)
                            if old_ts.exists():
                                try:
                                    old_ts.unlink()
                                except Exception:
                                    pass  # Ignore file deletion errors
                        db_session.delete(old_result)
                    
                    # Now add new result
                    db_result = SSDResult(
                        project_id=project_id,
                        scenario_id=scenario_dict['id'],
                        scenario_name=scenario_dict['scenario_name'],
                        cso_name=cso_dict['name'],
                        config_name=config_dict['name'],
                        start_date=config_dict['start_date'],
                        end_date=config_dict['end_date'],
                        pff_increase=scenario_dict['pff_increase'],
                        tank_volume=scenario_dict['tank_volume'] or 0.0,
                        spill_target=config_dict['spill_target'],
                        spill_target_bathing=config_dict['spill_target_bathing'],
                        converged=result.converged,
                        iterations=result.iterations_count,
                        final_storage_m3=round(result.final_storage_m3, 1),
                        spill_count=result.spill_count,
                        bathing_spill_count=result.bathing_spills_count,
                        total_spill_volume_m3=round(result.total_spill_volume_m3, 1),
                        bathing_spill_volume_m3=round(result.bathing_spill_volume_m3, 1),
                        total_spill_duration_hours=round(result.total_spill_duration_hours, 2),
                        spill_events=spill_events,
                        timeseries_path=str(ts_path)
                    )
                    db_session.add(db_result)
                    db_session.commit()
                    db_session.refresh(db_result)
                    result_id = db_result.id
                
                scenario_result = {
                    "scenario_id": scenario_dict['id'],
                    "result_id": result_id,
                    "scenario_name": scenario_dict['scenario_name'],
                    "cso_name": cso_dict['name'],
                    "config_name": config_dict['name'],
                    "status": "success",
                    "converged": result.converged,
                    "iterations": result.iterations_count,
                    "final_storage_m3": round(result.final_storage_m3, 1),
                    "spill_count": result.spill_count,
                    "bathing_spill_count": result.bathing_spills_count,
                }
                results.append(scenario_result)
                
                # Send scenario complete event
                yield f"data: {json.dumps({'type': 'scenario_complete', 'result': scenario_result})}\n\n"
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                yield f"data: {json.dumps({'type': 'log', 'message': f'Error: {error_msg}', 'level': 'error'})}\n\n"
                results.append({
                    "scenario_id": scenario_dict['id'],
                    "scenario_name": scenario_dict['scenario_name'],
                    "status": "error",
                    "message": error_msg
                })
        
        # Send final complete event
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = len(results) - successful
        yield f"data: {json.dumps({'type': 'complete', 'success': successful > 0, 'message': f'Completed {successful} of {len(results)} scenario(s)', 'scenarios': results})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/projects/{project_id}/analyze", response_model=SSDAnalysisResponse)
def run_analysis(
    project_id: int,
    config: SSDAnalysisConfig,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Run storage analysis for a project (legacy single-config endpoint)."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = DATA_DIR / str(project_id)
    if not project_dir.exists() or not list(project_dir.glob("*.csv")):
        raise HTTPException(status_code=400, detail="No data files uploaded. Please upload CSV files first.")
    
    try:
        # Convert API config to legacy dict format for CSOConfiguration
        legacy_config = {
            'CSO Name': config.cso_name,
            'Overflow Links': [config.overflow_link],
            'Continuation Link': config.continuation_link,
            'Run Suffix': config.run_suffix,
            'Start Date (dd/mm/yy hh:mm:ss)': datetime.fromisoformat(config.start_date).strftime('%d/%m/%Y %H:%M:%S'),
            'End Date (dd/mm/yy hh:mm:ss)': datetime.fromisoformat(config.end_date).strftime('%d/%m/%Y %H:%M:%S'),
            'Spill Target (Entire Period)': config.spill_target_entire,
            'Spill Target (Bathing Seasons)': config.spill_target_bathing,
            'Bathing Season Start (dd/mm)': config.bathing_season_start,
            'Bathing Season End (dd/mm)': config.bathing_season_end,
            'PFF Increase (m3/s)': config.pff_increase,
            'Tank Volume (m3)': config.tank_volume,
            'Pump Rate (m3/s)': config.pump_rate,
            'Pumping Mode': config.pumping_mode,
            'Flow Return Threshold (m3/s)': config.flow_return_threshold,
            'Depth Return Threshold (m)': config.depth_return_threshold,
            'Time Delay (hours)': config.time_delay,
            'Spill Flow Threshold (m3/s)': config.spill_flow_threshold,
            'Spill Volume Threshold (m3)': config.spill_volume_threshold,
        }
        
        cso_config = CSOConfiguration.from_dict(legacy_config)
        
        # Validate config
        errors = cso_config.validate()
        if errors:
            raise HTTPException(status_code=400, detail=f"Configuration error: {', '.join(errors)}")
        
        # Setup data source with date format detection for fast parsing
        csv_files = list(project_dir.glob("*.csv"))
        date_format = detect_csv_date_format(csv_files[0]) if csv_files else None
        
        data_source = DataSourceInfo(
            data_folder=project_dir,
            file_type="csv",
            date_format=date_format
        )
        
        # Setup scenario
        scenario = ScenarioSettings(
            spill_target=config.spill_target_entire,
            bathing_spill_target=config.spill_target_bathing,
            spill_flow_threshold=config.spill_flow_threshold,
            spill_volume_threshold=config.spill_volume_threshold,
        )
        
        # Run analysis
        analyzer = StorageAnalyzer(cso_config, data_source, scenario)
        result: CSOAnalysisResult = analyzer.run()
        
        # Convert spill events
        spill_events = []
        for event in result.spill_events:
            spill_events.append(SpillEventResponse(
                start_time=event.start_time.isoformat(),
                end_time=event.end_time.isoformat(),
                duration_hours=event.spill_duration_hours,
                volume_m3=event.volume_m3,
                peak_flow_m3s=event.peak_flow_m3s,
                is_bathing_season=event.is_in_bathing_season(
                    cso_config.bathing_season_start.month,
                    cso_config.bathing_season_start.day,
                    cso_config.bathing_season_end.month,
                    cso_config.bathing_season_end.day
                ) if config.spill_target_bathing > 0 else False
            ))
        
        return SSDAnalysisResponse(
            success=True,
            cso_name=result.cso_name,
            converged=result.converged,
            iterations=result.iterations_count,
            final_storage_m3=round(result.final_storage_m3, 1),
            spill_count=result.spill_count,
            bathing_spill_count=result.bathing_spills_count,
            total_spill_volume_m3=round(result.total_spill_volume_m3, 1),
            bathing_spill_volume_m3=round(result.bathing_spill_volume_m3, 1),
            total_spill_duration_hours=round(result.total_spill_duration_hours, 2),
            spill_events=spill_events
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return SSDAnalysisResponse(
            success=False,
            cso_name=config.cso_name,
            converged=False,
            iterations=0,
            final_storage_m3=0,
            spill_count=0,
            bathing_spill_count=0,
            total_spill_volume_m3=0,
            bathing_spill_volume_m3=0,
            total_spill_duration_hours=0,
            spill_events=[],
            error=str(e)
        )


# ==========================================
# RESULTS ENDPOINTS
# ==========================================

@router.get("/projects/{project_id}/results", response_model=List[SSDResultRead])
def list_results(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all saved analysis results for a project."""
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    statement = select(SSDResult).where(SSDResult.project_id == project_id).order_by(SSDResult.analysis_date.desc())
    results = session.exec(statement).all()
    return results


@router.get("/projects/{project_id}/results/{result_id}", response_model=SSDResultRead)
def get_result(
    project_id: int,
    result_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific analysis result."""
    result = session.get(SSDResult, result_id)
    if not result or result.project_id != project_id:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/projects/{project_id}/results/{result_id}/timeseries")
def get_result_timeseries(
    project_id: int,
    result_id: int,
    downsample: int = Query(default=1, ge=1, description="Target number of points (1 = all points, otherwise approx N points)"),
    start_date: str = Query(default=None, description="Start date for zoom (ISO format)"),
    end_date: str = Query(default=None, description="End date for zoom (ISO format)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get time-series data for a result (for charting) with smart downsampling and optional date range zoom."""
    result = session.get(SSDResult, result_id)
    if not result or result.project_id != project_id:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if not result.timeseries_path:
        raise HTTPException(status_code=404, detail="Time-series data not available")
    
    # Handle path resolution - stored path may be relative
    ts_path = Path(result.timeseries_path)
    if not ts_path.is_absolute():
        # Resolve relative to the backend directory (api/ssd.py -> api -> backend)
        ts_path = Path(__file__).parent.parent / result.timeseries_path
    
    if not ts_path.exists():
        raise HTTPException(status_code=404, detail=f"Time-series file not found: {ts_path}")
    
    try:
        df = pd.read_parquet(ts_path)
        full_data_count = len(df)
        
        # Parse and filter by date range if provided (for zoom feature)
        if start_date or end_date:
            # Ensure Time column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['Time']):
                df['Time'] = pd.to_datetime(df['Time'])
            
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['Time'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df['Time'] <= end_dt]
        
        # Select columns for charting
        chart_columns = ['Time', 'CSO_Flow_Original', 'Cont_Flow_Original', 'Spill_Flow', 'Tank_Volume']
        available_cols = [c for c in chart_columns if c in df.columns]
        
        # Also include any columns matching the continuation link pattern
        for col in df.columns:
            if col not in available_cols and not col.endswith('_Depth') and col != 'Spill_in_Time_Delay':
                available_cols.append(col)
        
        df_chart = df[available_cols].copy()
        original_count = len(df_chart)
        
        # Apply LTTB (Largest Triangle Three Buckets) downsampling if requested
        # This algorithm preserves the visual shape by keeping peaks and troughs
        if downsample > 1 and len(df_chart) > downsample:
            df_chart = lttb_downsample(df_chart, downsample)
        
        df_chart['Time'] = df_chart['Time'].astype(str)  # Convert datetime for JSON
        
        # Replace NaN and Inf values with None for JSON serialization
        import numpy as np
        df_chart = df_chart.replace([np.inf, -np.inf], np.nan)
        
        # Convert to dict and replace NaN with None (null in JSON)
        data_records = df_chart.to_dict(orient='records')
        for record in data_records:
            for key, value in record.items():
                if isinstance(value, float) and (pd.isna(value) or np.isinf(value)):
                    record[key] = None
        
        return {
            "columns": list(df_chart.columns),
            "data": data_records,
            "total_points": len(df_chart),
            "original_points": original_count,
            "downsampled": len(df_chart) < original_count
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error reading time-series: {str(e)}\n{traceback.format_exc()}")


@router.delete("/projects/{project_id}/results/{result_id}")
def delete_result(
    project_id: int,
    result_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an analysis result and its time-series file."""
    result = session.get(SSDResult, result_id)
    if not result or result.project_id != project_id:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Delete Parquet file if it exists
    if result.timeseries_path:
        ts_path = Path(result.timeseries_path)
        if ts_path.exists():
            ts_path.unlink()
    
    # Delete from database
    session.delete(result)
    session.commit()
    
    return {"success": True, "message": "Result deleted successfully"}


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
    from domain.ssd import SSDProjectCollaborator
    
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    statement = select(User).join(SSDProjectCollaborator).where(
        SSDProjectCollaborator.project_id == project_id
    )
    return session.exec(statement).all()

@router.post("/projects/{project_id}/collaborators")
def add_collaborator(
    project_id: int,
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a collaborator to a project."""
    from domain.ssd import SSDProjectCollaborator
    
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can add collaborators")
    
    user_to_add = session.exec(select(User).where(User.username == username)).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = session.exec(select(SSDProjectCollaborator).where(
        SSDProjectCollaborator.project_id == project_id,
        SSDProjectCollaborator.user_id == user_to_add.id
    )).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    link = SSDProjectCollaborator(project_id=project_id, user_id=user_to_add.id)
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
    """Remove a collaborator from a project."""
    from domain.ssd import SSDProjectCollaborator
    
    project = session.get(SSDProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")
    
    link = session.exec(select(SSDProjectCollaborator).where(
        SSDProjectCollaborator.project_id == project_id,
        SSDProjectCollaborator.user_id == user_id
    )).first()
    
    if link:
        session.delete(link)
        session.commit()
    
    return {"message": "Collaborator removed"}
