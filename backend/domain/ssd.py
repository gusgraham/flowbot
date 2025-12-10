from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship, JSON

# Base Project Model
class SSDProject(SQLModel, table=True):
    __tablename__ = "ssdproject"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client: str
    job_number: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    # Date format for CSV parsing (e.g., '%d/%m/%Y %H:%M:%S')
    # None means auto-detect
    date_format: Optional[str] = None
    
    # Relationships
    datasets: List["SSDDataset"] = Relationship(back_populates="project")
    results: List["SSDResult"] = Relationship(back_populates="project")

class SSDProjectCreate(SQLModel):
    name: str
    client: str
    job_number: str
    description: Optional[str] = None

class SSDProjectRead(SQLModel):
    id: int
    name: str
    client: str
    job_number: str
    description: Optional[str] = None
    created_at: datetime
    date_format: Optional[str] = None

class SSDProjectUpdate(SQLModel):
    name: Optional[str] = None
    client: Optional[str] = None
    job_number: Optional[str] = None
    description: Optional[str] = None

# Dataset Model (stores file paths)
class SSDDataset(SQLModel, table=True):
    __tablename__ = "ssddataset"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="ssdproject.id")
    file_type: str = "csv" # csv, etc
    flow_file_path: Optional[str] = None
    depth_file_path: Optional[str] = None
    imported_metadata: Optional[dict] = Field(default=None, sa_type=JSON) 
    uploaded_at: datetime = Field(default_factory=datetime.now)

    project: Optional[SSDProject] = Relationship(back_populates="datasets")

# Result Model - stores analysis results per scenario
class SSDResult(SQLModel, table=True):
    __tablename__ = "ssdresult"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="ssdproject.id", index=True)
    scenario_id: int = Field(foreign_key="analysisscenario.id", index=True)
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    # Scenario identifiers (snapshot at time of analysis)
    scenario_name: str
    cso_name: str
    config_name: str
    
    # Analysis parameters (snapshot)
    start_date: datetime
    end_date: datetime
    pff_increase: float
    spill_target: int
    tank_volume: float = 0.0  # Tank volume used in analysis
    
    # Key Metrics
    converged: bool
    iterations: int
    final_storage_m3: float
    spill_count: int
    bathing_spill_count: int
    total_spill_volume_m3: float
    bathing_spill_volume_m3: float
    total_spill_duration_hours: float
    
    # Spill events as JSON array
    spill_events: List[dict] = Field(default=[], sa_type=JSON)
    
    # Path to Parquet file with time-series data
    timeseries_path: Optional[str] = None
    
    project: Optional[SSDProject] = Relationship(back_populates="results")


class SSDResultCreate(SQLModel):
    scenario_id: int
    scenario_name: str
    cso_name: str
    config_name: str
    start_date: datetime
    end_date: datetime
    pff_increase: float
    spill_target: int
    tank_volume: float = 0.0
    converged: bool
    iterations: int
    final_storage_m3: float
    spill_count: int
    bathing_spill_count: int
    total_spill_volume_m3: float
    bathing_spill_volume_m3: float
    total_spill_duration_hours: float
    spill_events: List[dict] = []
    timeseries_path: Optional[str] = None


class SSDResultRead(SQLModel):
    id: int
    project_id: int
    scenario_id: int
    analysis_date: datetime
    scenario_name: str
    cso_name: str
    config_name: str
    start_date: datetime
    end_date: datetime
    pff_increase: float
    spill_target: int
    tank_volume: float
    converged: bool
    iterations: int
    final_storage_m3: float
    spill_count: int
    bathing_spill_count: int
    total_spill_volume_m3: float
    bathing_spill_volume_m3: float
    total_spill_duration_hours: float
    spill_events: List[dict]
    timeseries_path: Optional[str]




# CSO Asset Model - defines which links represent a CSO
class CSOAsset(SQLModel, table=True):
    __tablename__ = "csoasset"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="ssdproject.id", index=True)
    name: str = Field(index=True)  # Unique CSO identifier
    overflow_links: List[str] = Field(default=[], sa_type=JSON)  # Link names for overflow
    continuation_link: str  # Downstream continuation link
    is_effective_link: bool = False  # Whether overflow combines multiple links
    effective_link_components: Optional[List[str]] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.now)


class CSOAssetCreate(SQLModel):
    name: str
    overflow_links: List[str]
    continuation_link: str
    is_effective_link: bool = False
    effective_link_components: Optional[List[str]] = None


class CSOAssetRead(SQLModel):
    id: int
    project_id: int
    name: str
    overflow_links: List[str]
    continuation_link: str
    is_effective_link: bool
    effective_link_components: Optional[List[str]]
    created_at: datetime


class CSOAssetUpdate(SQLModel):
    name: Optional[str] = None
    overflow_links: Optional[List[str]] = None
    continuation_link: Optional[str] = None
    is_effective_link: Optional[bool] = None
    effective_link_components: Optional[List[str]] = None


# Analysis Configuration Model - reusable analysis settings
class AnalysisConfig(SQLModel, table=True):
    __tablename__ = "analysisconfig"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="ssdproject.id", index=True)
    name: str = Field(index=True)  # Configuration name
    mode: str  # "Default Mode", "Catchment Based Mode", "WWTW Mode"
    model: int  # 1=Spill Target, 2=Storage Volume, 3=Yorkshire Water, 4=Bathing Season
    start_date: datetime
    end_date: datetime
    spill_target: int  # Target spills for entire period
    spill_target_bathing: Optional[int] = None  # Target spills for bathing season (Model 4)
    bathing_season_start: Optional[str] = None  # "dd/mm" format
    bathing_season_end: Optional[str] = None  # "dd/mm" format
    spill_flow_threshold: float = 0.001  # m³/s
    spill_volume_threshold: float = 0.0  # m³
    created_at: datetime = Field(default_factory=datetime.now)


class AnalysisConfigCreate(SQLModel):
    name: str
    mode: str
    model: int
    start_date: datetime
    end_date: datetime
    spill_target: int
    spill_target_bathing: Optional[int] = None
    bathing_season_start: Optional[str] = None
    bathing_season_end: Optional[str] = None
    spill_flow_threshold: float = 0.001
    spill_volume_threshold: float = 0.0


class AnalysisConfigRead(SQLModel):
    id: int
    project_id: int
    name: str
    mode: str
    model: int
    start_date: datetime
    end_date: datetime
    spill_target: int
    spill_target_bathing: Optional[int]
    bathing_season_start: Optional[str]
    bathing_season_end: Optional[str]
    spill_flow_threshold: float
    spill_volume_threshold: float
    created_at: datetime


class AnalysisConfigUpdate(SQLModel):
    name: Optional[str] = None
    mode: Optional[str] = None
    model: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    spill_target: Optional[int] = None
    spill_target_bathing: Optional[int] = None
    bathing_season_start: Optional[str] = None
    bathing_season_end: Optional[str] = None
    spill_flow_threshold: Optional[float] = None
    spill_volume_threshold: Optional[float] = None


# Analysis Scenario Model - specific what-if cases to run
class AnalysisScenario(SQLModel, table=True):
    __tablename__ = "analysisscenario"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="ssdproject.id", index=True)
    scenario_name: str = Field(index=True)  # Unique identifier
    cso_asset_id: int = Field(foreign_key="csoasset.id", index=True)  # Links to CSOAsset
    config_id: int = Field(foreign_key="analysisconfig.id", index=True)  # Links to AnalysisConfig
    
    # Intervention parameters
    pff_increase: float = 0.0  # Pass forward flow increase (m³/s)
    pumping_mode: str = "Fixed"  # "Fixed" or "Variable"
    pump_rate: float = 0.0  # m³/s
    time_delay: int = 0  # hours
    flow_return_threshold: float = 0.0  # m³/s
    depth_return_threshold: float = 0.0  # m
    tank_volume: Optional[float] = None  # m³ (for Model 2 - Fixed Tank)
    
    created_at: datetime = Field(default_factory=datetime.now)


class AnalysisScenarioCreate(SQLModel):
    scenario_name: str
    cso_asset_id: int
    config_id: int
    pff_increase: float = 0.0
    pumping_mode: str = "Fixed"
    pump_rate: float = 0.0
    time_delay: int = 0
    flow_return_threshold: float = 0.0
    depth_return_threshold: float = 0.0
    tank_volume: Optional[float] = None


class AnalysisScenarioRead(SQLModel):
    id: int
    project_id: int
    scenario_name: str
    cso_asset_id: int
    config_id: int
    pff_increase: float
    pumping_mode: str
    pump_rate: float
    time_delay: int
    flow_return_threshold: float
    depth_return_threshold: float
    tank_volume: Optional[float]
    created_at: datetime


class AnalysisScenarioUpdate(SQLModel):
    scenario_name: Optional[str] = None
    cso_asset_id: Optional[int] = None
    config_id: Optional[int] = None
    pff_increase: Optional[float] = None
    pumping_mode: Optional[str] = None
    pump_rate: Optional[float] = None
    time_delay: Optional[int] = None
    flow_return_threshold: Optional[float] = None
    depth_return_threshold: Optional[float] = None
    tank_volume: Optional[float] = None



