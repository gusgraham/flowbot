"""Core data models for the refactored storage modeller."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(slots=True)
class EffectiveCSODefinition:
    """User-defined mapping of real-world CSO links to an effective model."""

    name: str
    continuation_links: List[str]
    overflow_links: List[str]
    run_suffix: str = "1"
    notes: Optional[str] = None

    def all_links(self) -> List[str]:
        return sorted(set(self.continuation_links + self.overflow_links))


@dataclass(slots=True)
class ScenarioSettings:
    """High-level analysis knobs applied across all CSOs in a run."""

    name: str = "Default Scenario"
    analysis_mode: str = "default"  # default, bathing_season, catchment, wwtw
    spill_target: int = 10
    bathing_spill_target: int = 0
    spill_flow_threshold: float = 0.001
    spill_volume_threshold: float = 0.0
    bathing_season_start: date | None = None
    bathing_season_end: date | None = None
    time_delay_hours: int = 0
    timestep_seconds: Optional[int] = None
    pump_mode: str = "Fixed"
    pump_rate_m3s: float = 0.0
    flow_return_threshold_m3s: float = 0.0
    depth_return_threshold_m: float = 0.0
    pff_increase_m3s: float = 0.0

    def copy_with_overrides(self, **overrides: object) -> "ScenarioSettings":
        return replace(self, **overrides)


@dataclass(slots=True)
class DataSourceInfo:
    """Metadata about imported InfoWorks time-series files."""

    data_folder: Path
    file_type: str
    timestep_seconds: Optional[int] = None
    available_links: List[str] = field(default_factory=list)
    has_depth_data: bool = True
    raw_metadata: Dict[str, Dict[str, object]] = field(default_factory=dict)
    # Explicit date format for fast CSV parsing
    date_format: Optional[str] = None


@dataclass(slots=True)
class AnalysisJob:
    """Container for everything needed to execute a modelling run."""

    csos: List[EffectiveCSODefinition]
    scenario: ScenarioSettings
    data_source: DataSourceInfo
    output_directory: Optional[Path] = None
    extras: Dict[str, object] = field(default_factory=dict)
