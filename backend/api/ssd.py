from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlmodel import Session, select, Field
from pydantic import BaseModel
import shutil
import os
from pathlib import Path
import pandas as pd

# Import domain models
from domain.ssd import (
    SSDProject, SSDProjectCreate, SSDProjectRead, SSDDataset, SSDResult,
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
    """List all SSD projects."""
    projects = session.exec(
        select(SSDProject).offset(offset).limit(limit)
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
    
    for csv_file in project_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            # Find time column
            time_col = None
            for col in df.columns:
                if col.lower() in ['time', 'datetime', 'date', 'timestamp']:
                    time_col = col
                    break
            
            if time_col:
                # Parse dates
                df[time_col] = pd.to_datetime(df[time_col], dayfirst=True)
                file_min = df[time_col].min()
                file_max = df[time_col].max()
                
                if min_date is None or file_min < min_date:
                    min_date = file_min
                if max_date is None or file_max > max_date:
                    max_date = file_max
        except Exception:
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
                    pass  # Use default timestep
            
            data_source = DataSourceInfo(
                data_folder=project_dir,
                file_type="csv",
                timestep_seconds=timestep_seconds
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
            
            results.append({
                "scenario_id": scenario.id,
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
        
        # Setup data source
        data_source = DataSourceInfo(
            data_folder=project_dir,
            file_type="csv"
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
