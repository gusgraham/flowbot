"""
Data models for separating CSO assets from analysis scenarios.

This module implements a three-level architecture:
- CSOAsset: Physical CSO definition (defined once)
- AnalysisConfiguration: Reusable analysis settings (can be applied to multiple CSOs)
- AnalysisScenario: Specific what-if analysis (CSO + Config + Interventions)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path


@dataclass
class CSOAsset:
    """
    Physical CSO definition - defines which links represent a CSO.

    This represents the logical grouping of overflow and continuation links.
    The actual data comes from the Data Import tab.
    One CSO asset can have many analysis scenarios.

    Attributes:
        name: Unique CSO identifier
        overflow_links: List of link names that spill (can be single link or effective link)
        continuation_link: Downstream continuation link name
        is_effective_link: Whether overflow is an effective (combined) link
        effective_link_components: If effective, the component link names
    """
    name: str
    overflow_links: list[str]  # Link name(s) from data import
    continuation_link: str  # Link name from data import
    is_effective_link: bool = False
    effective_link_components: Optional[list[str]] = None

    def __post_init__(self):
        """Validate asset data."""
        if not self.name or not self.name.strip():
            raise ValueError("CSO name cannot be empty")

        if not self.overflow_links:
            raise ValueError("At least one overflow link must be specified")

        if not self.continuation_link or not self.continuation_link.strip():
            raise ValueError("Continuation link must be specified")

        if self.is_effective_link and not self.effective_link_components:
            raise ValueError(
                "Effective link must have component links specified")

        if self.is_effective_link and len(self.effective_link_components) < 2:
            raise ValueError("Effective link must combine at least 2 links")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        result = {
            'CSO Name': self.name,
            'Overflow Links': '|'.join(self.overflow_links),  # Pipe-separated
            'Continuation Link': self.continuation_link,
            'Is Effective Link': self.is_effective_link,
        }

        if self.effective_link_components:
            result['Effective Link Components'] = '|'.join(
                self.effective_link_components)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CSOAsset':
        """Create from dictionary (CSV import)."""
        overflow_links = data['Overflow Links'].split('|') if isinstance(
            data['Overflow Links'], str) else data['Overflow Links']

        effective_components = None
        if data.get('Effective Link Components'):
            effective_components = data['Effective Link Components'].split('|')

        return cls(
            name=data['CSO Name'],
            overflow_links=overflow_links,
            continuation_link=data['Continuation Link'],
            is_effective_link=bool(data.get('Is Effective Link', False)),
            effective_link_components=effective_components,
        )


@dataclass
class WWTWAsset:
    """
    Wastewater Treatment Works (WwTW) asset definition.

    Unlike CSOs (which model overflow/continuation splits), WwTWs model
    the inlet works with pump control and FFT (Final Effluent Tank) augmentation.

    Attributes:
        name: Unique WwTW identifier
        spill_links: List of inlet spill/overflow link names
        fft_link: Final effluent tank (continuation/pass-forward) link name
        pump_links: Optional list of pump link names (can be empty)
    """
    name: str
    spill_links: List[str]  # Inlet overflow links
    fft_link: str  # Continuation/pass-forward link
    pump_links: List[str] = field(default_factory=list)  # Optional pump links

    def __post_init__(self):
        """Validate WwTW data."""
        if not self.name or not self.name.strip():
            raise ValueError("WwTW name cannot be empty")

        if not self.spill_links:
            raise ValueError("At least one spill link must be specified")

        if not self.fft_link or not self.fft_link.strip():
            raise ValueError("FFT link must be specified")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            'WwTW Name': self.name,
            'Spill Links': '|'.join(self.spill_links),
            'FFT Link': self.fft_link,
            'Pump Links': '|'.join(self.pump_links) if self.pump_links else '',
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WWTWAsset':
        """Create from dictionary (CSV import)."""
        spill_links = data['Spill Links'].split('|') if isinstance(
            data['Spill Links'], str) else data['Spill Links']

        pump_links_str = data.get('Pump Links', '')
        pump_links = pump_links_str.split(
            '|') if pump_links_str and pump_links_str.strip() else []

        return cls(
            name=data['WwTW Name'],
            spill_links=spill_links,
            fft_link=data['FFT Link'],
            pump_links=pump_links,
        )


@dataclass
class AnalysisConfiguration:
    """
    Reusable analysis configuration - defines how to analyze CSOs.

    This represents a standard analysis approach that can be applied to multiple CSOs.
    For example: "10 Spills Per Annum", "Bathing Season Compliance", etc.

    Attributes:
        name: Configuration name (e.g., "CSO 10SPA", "Bathing Compliance")
        mode: Analysis mode ("Default Mode", "Catchment Based Mode", "WWTW Mode")
        model: Model/method (1: Classical, 2: Fixed Tank, 3: Yorkshire Water, 4: Bathing Season Assessment)
        start_date: Analysis period start
        end_date: Analysis period end
        spill_target: Target spills for entire period
        spill_target_bathing: Target spills during bathing season (required for Model 4)
        bathing_season_start: Bathing season start date "dd/mm" (required for Model 4)
        bathing_season_end: Bathing season end date "dd/mm" (required for Model 4)
        spill_flow_threshold: Minimum flow to count as spill (m³/s)
        spill_volume_threshold: Minimum volume to count as spill (m³)
    """
    name: str
    mode: str  # "Default Mode", "Catchment Based Mode", "WWTW Mode", "Bathing Season Assessment"
    model: int  # 1=Classical, 2=Fixed Tank, 3=Yorkshire Water, 4=Bathing Season
    start_date: datetime
    end_date: datetime
    spill_target: int  # Target spills for entire period

    # Optional bathing season parameters (required for Model 4)
    spill_target_bathing: Optional[int] = None
    bathing_season_start: Optional[str] = None  # "dd/mm" format
    bathing_season_end: Optional[str] = None    # "dd/mm" format

    # Spill definition thresholds
    spill_flow_threshold: float = 0.001  # m³/s
    spill_volume_threshold: float = 0.0  # m³

    def __post_init__(self):
        """Validate configuration."""
        if not self.name or not self.name.strip():
            raise ValueError("Analysis configuration name cannot be empty")

        valid_modes = ["Default Mode", "Catchment Based Mode", "WWTW Mode"]
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {valid_modes}")

        if self.model not in [1, 2, 3, 4]:
            raise ValueError(
                f"Invalid model: {self.model}. Must be 1, 2, 3, or 4")

        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

        # Validate model-specific requirements
        if self.model == 4:
            if self.spill_target_bathing is None:
                raise ValueError(
                    "Model 4 (Bathing Season) requires spill_target_bathing")
            if not self.bathing_season_start or not self.bathing_season_end:
                raise ValueError(
                    "Model 4 (Bathing Season) requires bathing season dates")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        result = {
            'Configuration Name': self.name,
            'Mode': self.mode,
            'Model': self.model,
            'Start Date': self.start_date.strftime('%d/%m/%Y %H:%M:%S'),
            'End Date': self.end_date.strftime('%d/%m/%Y %H:%M:%S'),
            'Spill Target': self.spill_target,
            'Spill Target (Bathing)': self.spill_target_bathing if self.spill_target_bathing is not None else '',
            'Bathing Season Start': self.bathing_season_start or '',
            'Bathing Season End': self.bathing_season_end or '',
            'Spill Flow Threshold (m3/s)': self.spill_flow_threshold,
            'Spill Volume Threshold (m3)': self.spill_volume_threshold,
        }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisConfiguration':
        """Create from dictionary (CSV import or JSON load)."""
        bathing_target = data.get('Spill Target (Bathing)')
        if bathing_target == '' or bathing_target is None:
            bathing_target = None
        else:
            bathing_target = int(bathing_target)

        # Parse dates - handle both CSV format and ISO format (from JSON)
        start_date_str = data['Start Date']
        end_date_str = data['End Date']

        # Try ISO format first (from JSON), then CSV format
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except (ValueError, AttributeError):
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y %H:%M:%S')

        try:
            end_date = datetime.fromisoformat(end_date_str)
        except (ValueError, AttributeError):
            end_date = datetime.strptime(end_date_str, '%d/%m/%Y %H:%M:%S')

        return cls(
            name=data['Configuration Name'],
            mode=data['Mode'],
            model=int(data['Model']),
            start_date=start_date,
            end_date=end_date,
            spill_target=int(data['Spill Target']),
            spill_target_bathing=bathing_target,
            bathing_season_start=data.get('Bathing Season Start') or None,
            bathing_season_end=data.get('Bathing Season End') or None,
            spill_flow_threshold=float(
                data.get('Spill Flow Threshold (m3/s)', 0.001)),
            spill_volume_threshold=float(
                data.get('Spill Volume Threshold (m3)', 0.0)),
        )


@dataclass
class AnalysisScenario:
    """
    Specific analysis scenario - combines CSO/Catchment/WwTW + Configuration + Interventions.

    This represents a specific "what-if" case to run.
    Multiple scenarios can use the same asset and Configuration with different interventions.

    Attributes:
        cso_name: Reference to CSOAsset.name (for single CSO scenarios)
        catchment_name: Reference to Catchment.name (for catchment scenarios)
        wwtw_name: Reference to WWTWAsset.name (for WwTW scenarios)
        config_name: Reference to AnalysisConfiguration.name
        scenario_name: Unique scenario identifier
        pff_increase: Pass forward flow increase (m³/s) - CSO/Catchment only
        pumping_mode: "Fixed" or "Variable" - CSO/Catchment only
        pump_rate: Pump rate (m³/s) - CSO/Catchment only
        time_delay: Pump activation delay (hours) - CSO/Catchment only
        flow_return_threshold: Flow threshold for tank draindown (m³/s) - CSO/Catchment only
        depth_return_threshold: Depth threshold for tank draindown (m) - CSO/Catchment only
        tank_volume: Storage tank volume (m³) - required for Model 2 (Fixed Tank Method)
        fft_augmentation: FFT capacity increase (m³/s) - WwTW only

    Note: Exactly ONE of cso_name, catchment_name, or wwtw_name must be set.
    """
    config_name: str  # Reference to AnalysisConfiguration.name
    scenario_name: str  # Unique identifier for this scenario

    # Asset reference - EXACTLY ONE of these must be set
    cso_name: Optional[str] = None  # Reference to CSOAsset.name
    catchment_name: Optional[str] = None  # Reference to Catchment.name
    wwtw_name: Optional[str] = None  # Reference to WWTWAsset.name

    # For catchment scenarios: per-CSO intervention parameters
    # Dict mapping CSO name -> intervention parameters
    # Example: {"CSO1": {"pff_increase": 0.1, "pump_rate": 0.5, ...}, "CSO2": {...}}
    cso_interventions: Optional[Dict[str, Dict[str, Any]]] = None

    # Intervention parameters (for single CSO scenarios, or defaults for catchment)
    pff_increase: float = 0.0  # m³/s

    # Pumping configuration
    pumping_mode: str = "Fixed"  # "Fixed" or "Variable"
    pump_rate: float = 0.0  # m³/s
    time_delay: int = 0  # hours

    # Tank draindown thresholds (CSO/Catchment only)
    flow_return_threshold: float = 0.0  # m³/s
    depth_return_threshold: float = 0.0  # m

    # Storage tank volume (required for Model 2 - Fixed Tank Method)
    tank_volume: Optional[float] = None  # m³

    # WwTW-specific interventions
    fft_augmentation: float = 0.0  # m³/s - increase to FFT capacity
    wwtw_pump_rate: Optional[float] = None  # m³/s - Pump discharge rate
    # m³/s - Flow threshold to start pumping
    wwtw_pump_on_threshold: Optional[float] = None
    # m³/s - Flow threshold to stop pumping
    wwtw_pump_off_threshold: Optional[float] = None
    # hours - Time delay for pump control
    wwtw_time_delay_hours: Optional[int] = None

    def __post_init__(self):
        """Validate scenario configuration."""
        # Validate that exactly one asset type is specified
        asset_count = sum([
            self.cso_name is not None,
            self.catchment_name is not None,
            self.wwtw_name is not None
        ])
        if asset_count != 1:
            raise ValueError(
                "Must specify exactly one of: cso_name, catchment_name, wwtw_name")

        # Validate that if specified, names are not empty
        if self.cso_name is not None and not self.cso_name.strip():
            raise ValueError("CSO name cannot be empty")

        if self.catchment_name is not None and not self.catchment_name.strip():
            raise ValueError("Catchment name cannot be empty")

        if self.wwtw_name is not None and not self.wwtw_name.strip():
            raise ValueError("WwTW name cannot be empty")

        if not self.config_name or not self.config_name.strip():
            raise ValueError("Configuration name cannot be empty")

        if not self.scenario_name or not self.scenario_name.strip():
            raise ValueError("Scenario name cannot be empty")

        if self.pumping_mode not in ["Fixed", "Variable"]:
            raise ValueError(f"Invalid pumping mode: {self.pumping_mode}")

    def is_catchment_scenario(self) -> bool:
        """Check if this is a catchment-based scenario."""
        return self.catchment_name is not None

    def is_wwtw_scenario(self) -> bool:
        """Check if this is a WwTW scenario."""
        return self.wwtw_name is not None

    def get_asset_name(self) -> str:
        """Get the asset name (CSO, Catchment, or WwTW)."""
        if self.is_catchment_scenario():
            return self.catchment_name
        elif self.is_wwtw_scenario():
            return self.wwtw_name
        else:
            return self.cso_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        result = {
            'config_name': self.config_name,
            'scenario_name': self.scenario_name,
            'cso_name': self.cso_name,
            'catchment_name': self.catchment_name,
            'wwtw_name': self.wwtw_name,
            'pff_increase': self.pff_increase,
            'pumping_mode': self.pumping_mode,
            'pump_rate': self.pump_rate,
            'time_delay': self.time_delay,
            'flow_return_threshold': self.flow_return_threshold,
            'depth_return_threshold': self.depth_return_threshold,
            'tank_volume': self.tank_volume,
            'fft_augmentation': self.fft_augmentation,
            'wwtw_pump_rate': self.wwtw_pump_rate,
            'wwtw_pump_on_threshold': self.wwtw_pump_on_threshold,
            'wwtw_pump_off_threshold': self.wwtw_pump_off_threshold,
            'wwtw_time_delay_hours': self.wwtw_time_delay_hours,
            'cso_interventions': self.cso_interventions,
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisScenario':
        """Create from dictionary (CSV import or JSON load)."""
        return cls(
            cso_name=data.get('cso_name'),
            catchment_name=data.get('catchment_name'),
            wwtw_name=data.get('wwtw_name'),
            config_name=data['config_name'],
            scenario_name=data['scenario_name'],
            pff_increase=data.get('pff_increase', 0.0),
            pumping_mode=data.get('pumping_mode', 'Fixed'),
            pump_rate=data.get('pump_rate', 0.0),
            time_delay=data.get('time_delay', 0),
            flow_return_threshold=data.get('flow_return_threshold', 0.0),
            depth_return_threshold=data.get('depth_return_threshold', 0.0),
            tank_volume=data.get('tank_volume'),
            fft_augmentation=data.get('fft_augmentation', 0.0),
            wwtw_pump_rate=data.get('wwtw_pump_rate'),
            wwtw_pump_on_threshold=data.get('wwtw_pump_on_threshold'),
            wwtw_pump_off_threshold=data.get('wwtw_pump_off_threshold'),
            wwtw_time_delay_hours=data.get('wwtw_time_delay_hours'),
            cso_interventions=data.get('cso_interventions'),
        )

    def to_legacy_format(self, asset: CSOAsset, config: AnalysisConfiguration) -> Dict[str, Any]:
        """
        Convert scenario + asset + config to legacy Storage_Modeller format.

        Note: Legacy engine expects 'CSO Name' to be the overflow link name (data column),
        not a user-friendly name. For display, use asset.name separately.
        """
        # Legacy uses overflow link as identifier (data column name)
        cso_identifier = asset.overflow_links[0] if asset.overflow_links else asset.name

        return {
            'CSO Name': cso_identifier,
            'CSO Display Name': asset.name,  # User-friendly name for display/logging
            # Include scenario name for results display
            'Scenario Name': self.scenario_name,
            'Overflow Links': asset.overflow_links,
            'Continuation Link': asset.continuation_link,
            'Is Effective Link': asset.is_effective_link,
            'Effective Link Components': asset.effective_link_components,
            'Analysis Mode': config.mode,
            'Model Identifier': config.model,
            'Start Date (dd/mm/yy hh:mm:ss)': config.start_date,
            'End Date (dd/mm/yy hh:mm:ss)': config.end_date,
            'Spill Target (Entire Period)': config.spill_target,
            'Spill Target (Bathing Seasons)': config.spill_target_bathing,
            'Bathing Season Start (dd/mm)': config.bathing_season_start,
            'Bathing Season End (dd/mm)': config.bathing_season_end,
            'Spill Flow Threshold (m3/s)': config.spill_flow_threshold,
            'Spill Volume Threshold (m3)': config.spill_volume_threshold,
            'Tank Volume (m3)': self.tank_volume,
            'PFF Increase (m3/s)': self.pff_increase,
            'Pumping Mode': self.pumping_mode,
            'Pump Rate (m3/s)': self.pump_rate,
            'Time Delay (hours)': self.time_delay,
            'Flow Return Threshold (m3/s)': self.flow_return_threshold,
            'Depth Return Threshold (m)': self.depth_return_threshold,
            # Generate unique run suffix
            'Run Suffix': f"{self.scenario_name}_{asset.name}",
        }


# Helper function to create legacy config from new three-level structure
def create_legacy_config(
    asset: CSOAsset,
    config: AnalysisConfiguration,
    scenario: AnalysisScenario
) -> Dict[str, Any]:
    """Create legacy config from new three-level structure."""
    return scenario.to_legacy_format(asset, config)


def get_available_models_for_mode(mode: str) -> list[int]:
    """
    Get the list of valid models for a given analysis mode.

    Args:
        mode: Analysis mode ("Default Mode", "Catchment Based Mode", "WWTW Mode")

    Returns:
        List of valid model identifiers
    """
    # Default Mode: All models available
    if mode == "Default Mode":
        return [1, 2, 3, 4]

    # Catchment Based Mode: Local and DS Draindown
    elif mode == "Catchment Based Mode":
        return [1, 2]

    # WWTW Mode: Same as Default but excluding Model 3 (Yorkshire Water Method)
    elif mode == "WWTW Mode":
        return [1, 2, 4]

    return [1, 2, 3, 4]  # Default to all


def get_model_name(model: int, mode: str = "Default Mode") -> str:
    """
    Get human-readable name for model identifier.

    Args:
        model: Model identifier (1-4)
        mode: Analysis mode (affects model 1 and 2 names for Catchment mode)

    Returns:
        Human-readable model name
    """
    # Catchment mode has different names for models 1 and 2
    if mode == "Catchment Based Mode":
        catchment_names = {
            1: "Local Draindown",
            2: "DS Draindown First",
        }
        return catchment_names.get(model, f"Model {model}")

    # Default and WwTW modes use standard names
    names = {
        1: "Spill Target Assessment",
        2: "Storage Volume Assessment",
        3: "Yorkshire Water Method",
        4: "Bathing Season Assessment"
    }
    return names.get(model, f"Model {model}")


def get_model_description(model: int, mode: str = "Default Mode") -> str:
    """
    Get description of model behavior.

    Args:
        model: Model identifier (1-4)
        mode: Analysis mode (affects descriptions for Catchment mode)

    Returns:
        Description of model behavior
    """
    # Catchment mode has different descriptions for models 1 and 2
    if mode == "Catchment Based Mode":
        catchment_descriptions = {
            1: "Local draindown condition: Tank empties locally at each CSO between spill events.",
            2: "Downstream draindown first: Downstream CSO tanks drain before upstream flow contribution.",
        }
        return catchment_descriptions.get(model, "")

    # Default and WwTW modes use standard descriptions
    descriptions = {
        1: "Iterative bisection with tank draindown. Searches for exact target spill count.",
        2: "Single iteration with user-specified tank volume. No optimization.",
        3: "Yorkshire Water heuristic: mean nth-largest spill volume per year. Instant tank emptying, single iteration.",
        4: "Iterative bisection with dual constraints (entire period + bathing season). Searches for exact targets."
    }
    return descriptions.get(model, "")


@dataclass
class CatchmentRelationship:
    """
    Defines hydraulic connection between two CSOs within a catchment.

    This represents a single CSO and its connections to upstream/downstream CSOs.
    Used within a Catchment to define the network topology.

    Attributes:
        cso_name: Reference to CSOAsset.name
        upstream_csos: List of CSO names that feed into this CSO (empty if independent)
        downstream_cso: CSO name that receives flow from this CSO (None if terminal)
        max_pff: Maximum pass forward flow capacity (m³/s) - limits how much upstream
                 delta can be added to continuation flow before spilling
        distance_to_downstream: Distance to downstream CSO in meters (for time-shift calculation)
        average_velocity: Average flow velocity in m/s (for time-shift calculation)
    """
    cso_name: str
    upstream_csos: List[str] = field(default_factory=list)
    downstream_cso: Optional[str] = None
    max_pff: Optional[float] = None  # m³/s
    distance_to_downstream: Optional[float] = None  # meters
    average_velocity: Optional[float] = None  # m/s

    def __post_init__(self):
        """Validate catchment relationship."""
        if not self.cso_name or not self.cso_name.strip():
            raise ValueError("CSO name cannot be empty")

        # If downstream CSO specified, must have distance and velocity
        if self.downstream_cso:
            if self.distance_to_downstream is None or self.distance_to_downstream <= 0:
                raise ValueError(
                    f"Distance to downstream CSO must be positive (CSO: {self.cso_name})")
            if self.average_velocity is None or self.average_velocity <= 0:
                raise ValueError(
                    f"Average velocity must be positive (CSO: {self.cso_name})")

        # If upstream CSOs specified, should have max PFF defined
        if self.upstream_csos and not self.max_pff:
            # Warning but not error - max_pff can be 'Unknown' which becomes None
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            'CSO Name': self.cso_name,
            'Upstream CSOs': ','.join(self.upstream_csos) if self.upstream_csos else '',
            'Downstream CSO': self.downstream_cso or '',
            'Maximum Pass Forward Flow (m3/s)': self.max_pff if self.max_pff is not None else '',
            'Distance (m)': self.distance_to_downstream if self.distance_to_downstream is not None else '',
            'Average Velocity (m/s)': self.average_velocity if self.average_velocity is not None else '',
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CatchmentRelationship':
        """Create from dictionary (CSV import)."""
        # Parse upstream CSOs
        upstream_str = data.get('Upstream CSOs', '')
        upstream_csos = [x.strip() for x in upstream_str.split(
            ',') if x.strip()] if upstream_str else []

        # Parse downstream CSO
        downstream = data.get('Downstream CSO', '')
        downstream_cso = downstream if downstream else None

        # Parse numeric fields
        max_pff_str = data.get('Maximum Pass Forward Flow (m3/s)', '')
        max_pff = float(
            max_pff_str) if max_pff_str and max_pff_str != '' else None

        distance_str = data.get('Distance (m)', '')
        distance = float(
            distance_str) if distance_str and distance_str != '' else None

        velocity_str = data.get('Average Velocity (m/s)', '')
        velocity = float(
            velocity_str) if velocity_str and velocity_str != '' else None

        return cls(
            cso_name=data['CSO Name'],
            upstream_csos=upstream_csos,
            downstream_cso=downstream_cso,
            max_pff=max_pff,
            distance_to_downstream=distance,
            average_velocity=velocity,
        )

    def calculate_position_level(self, all_relationships: List['CatchmentRelationship']) -> int:
        """
        Calculate position level via topological sort.

        Level 0 = no upstream CSOs (headwaters)
        Level N = max(upstream levels) + 1
        """
        if not self.upstream_csos:
            return 0

        # Find upstream relationships
        upstream_levels = []
        for upstream_name in self.upstream_csos:
            upstream_rel = next(
                (r for r in all_relationships if r.cso_name == upstream_name), None)
            if upstream_rel:
                upstream_levels.append(
                    upstream_rel.calculate_position_level(all_relationships))

        return max(upstream_levels, default=-1) + 1


@dataclass
class Catchment:
    """
    Named catchment group containing multiple CSOs with defined relationships.

    A catchment represents a hydraulic network of CSOs that must be analyzed
    together in Catchment Based Mode. Each catchment has a name and contains
    2 or more CSO assets with their upstream/downstream relationships defined.

    Attributes:
        name: Unique catchment identifier (e.g., "North_Catchment", "River_System_A")
        cso_relationships: List of CatchmentRelationship objects defining the network
        _node_positions: Optional dict storing graphical positions of CSO nodes for editor
                        Format: {'cso_name': {'x': float, 'y': float}}
    """
    name: str
    cso_relationships: List[CatchmentRelationship] = field(
        default_factory=list)
    _node_positions: Optional[Dict[str, Dict[str, float]]] = field(
        default=None, repr=False)

    def __post_init__(self):
        """Basic validation of catchment name."""
        if not self.name or not self.name.strip():
            raise ValueError("Catchment name cannot be empty")

    def validate(self) -> List[str]:
        """
        Validate catchment configuration.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if len(self.cso_relationships) < 2:
            errors.append(
                f"Catchment '{self.name}' must contain at least 2 CSOs (currently has {len(self.cso_relationships)})")

        # Check for duplicate CSO names
        cso_names = [rel.cso_name for rel in self.cso_relationships]
        duplicates = [name for name in cso_names if cso_names.count(name) > 1]
        if duplicates:
            errors.append(
                f"Catchment '{self.name}' has duplicate CSOs: {', '.join(set(duplicates))}")

        return errors

    def get_cso_names(self) -> List[str]:
        """Get list of all CSO names in this catchment."""
        return [rel.cso_name for rel in self.cso_relationships]

    def get_relationship(self, cso_name: str) -> Optional[CatchmentRelationship]:
        """Get the relationship definition for a specific CSO."""
        return next((rel for rel in self.cso_relationships if rel.cso_name == cso_name), None)

    def validate_network(self) -> List[str]:
        """
        Validate the catchment network for common issues.

        Returns:
            List of error/warning messages (empty if valid)
        """
        errors = []
        cso_names = self.get_cso_names()

        # Check for circular dependencies
        for rel in self.cso_relationships:
            if self._has_circular_dependency(rel):
                errors.append(
                    f"Circular dependency detected involving '{rel.cso_name}'")

        # Check for references to CSOs not in this catchment
        for rel in self.cso_relationships:
            for upstream in rel.upstream_csos:
                if upstream not in cso_names:
                    errors.append(
                        f"'{rel.cso_name}' references upstream CSO '{upstream}' which is not in this catchment")

            if rel.downstream_cso and rel.downstream_cso not in cso_names:
                errors.append(
                    f"'{rel.cso_name}' references downstream CSO '{rel.downstream_cso}' which is not in this catchment")

        return errors

    def _has_circular_dependency(self, rel: CatchmentRelationship, visited: Optional[set] = None) -> bool:
        """Check if a relationship has circular dependencies."""
        if visited is None:
            visited = set()

        if rel.cso_name in visited:
            return True

        visited.add(rel.cso_name)

        for upstream_name in rel.upstream_csos:
            upstream_rel = self.get_relationship(upstream_name)
            if upstream_rel and self._has_circular_dependency(upstream_rel, visited.copy()):
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            'Catchment Name': self.name,
            'CSO Count': len(self.cso_relationships),
            'CSOs': ','.join(self.get_cso_names()),
            'Relationships': [rel.to_dict() for rel in self.cso_relationships]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Catchment':
        """Create from dictionary (project load)."""
        relationships = [
            CatchmentRelationship.from_dict(rel_dict)
            for rel_dict in data.get('Relationships', [])
        ]
        return cls(
            name=data['Catchment Name'],
            cso_relationships=relationships
        )
