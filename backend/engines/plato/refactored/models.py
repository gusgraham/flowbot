"""
Data models for refactored PLATO engine.
Provides typed, validated alternatives to legacy dict-based configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from pathlib import Path
import pandas as pd


@dataclass
class SpillEvent:
    """Single spill event with all relevant data."""
    start_time: datetime
    end_time: datetime
    window_duration_hours: float
    spill_duration_hours: float
    volume_m3: float
    peak_flow_m3s: float

    def is_in_bathing_season(self, start_month: int, start_day: int,
                             end_month: int, end_day: int) -> bool:
        """Check if this spill overlaps with bathing season."""
        event_month = self.start_time.month
        event_day = self.start_time.day

        # Simple case: season doesn't cross year boundary
        if start_month <= end_month:
            if start_month < event_month < end_month:
                return True
            if event_month == start_month and event_day >= start_day:
                return True
            if event_month == end_month and event_day <= end_day:
                return True
        else:  # Season crosses year boundary (e.g., Nov-Mar)
            if event_month >= start_month or event_month <= end_month:
                if event_month == start_month and event_day < start_day:
                    return False
                if event_month == end_month and event_day > end_day:
                    return False
                return True

        return False


@dataclass
class CSOAnalysisResult:
    """Structured result from CSO analysis (used by all analysis modes)."""
    cso_name: str
    run_suffix: str
    converged: bool
    iterations_count: int
    final_storage_m3: float

    # Spill statistics
    spill_count: int
    bathing_spills_count: int
    total_spill_volume_m3: float
    bathing_spill_volume_m3: float
    total_spill_duration_hours: float
    bathing_spill_duration_hours: float

    # Detailed data
    spill_events: list[SpillEvent]
    time_series: pd.DataFrame

    # Metadata
    analysis_date: datetime
    output_directory: Optional[Path] = None

    def to_summary_dict(self) -> dict:
        """Export summary for display."""
        return {
            'CSO Name': self.cso_name,
            'Run Suffix': self.run_suffix,
            'Converged': 'Yes' if self.converged else 'No',
            'Iterations': self.iterations_count,
            'Storage (m³)': round(self.final_storage_m3, 1),
            'Spills': self.spill_count,
            'Bathing Spills': self.bathing_spills_count,
            'Total Volume (m³)': round(self.total_spill_volume_m3, 1),
            'Bathing Volume (m³)': round(self.bathing_spill_volume_m3, 1),
        }


@dataclass
class CSOConfiguration:
    """
    Single CSO configuration with type safety and validation.
    Replaces legacy dict-based approach.
    """

    # Identity
    cso_name: str  # User-friendly name (e.g., "Beech Ave CSO")
    # Actual column name in data files (e.g., "BS4334543.1")
    overflow_link: str
    # Actual column name in data files (e.g., "BS4334543")
    continuation_link: str
    run_suffix: str

    # Time range
    start_date: datetime
    end_date: datetime

    # Spill targets
    spill_target_entire: int
    spill_target_bathing: int
    bathing_season_start: date  # MM-DD format
    bathing_season_end: date

    # Storage parameters
    pff_increase: float  # m3/s
    tank_volume: Optional[float] = None  # m3
    pump_rate: float = 0.0  # m3/s
    pumping_mode: str = 'Fixed'  # 'Fixed' or 'Variable'

    # Return thresholds
    flow_return_threshold: float = 0.0  # m3/s
    depth_return_threshold: float = 0.0  # m
    time_delay: float = 0.0  # hours (for draindown check)

    # Spill event thresholds
    spill_flow_threshold: float = 0.0  # m3/s
    spill_volume_threshold: float = 0.0  # m3

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of error messages.
        Empty list means valid.
        """
        errors = []

        if not self.cso_name:
            errors.append("CSO Name is required")

        if not self.overflow_link:
            errors.append("Overflow Link is required")

        if not self.continuation_link:
            errors.append("Continuation Link is required")

        if self.start_date >= self.end_date:
            errors.append("Start Date must be before End Date")

        if self.spill_target_entire < 0:
            errors.append("Spill Target (Entire Period) must be non-negative")

        if self.spill_target_bathing < -1:
            errors.append("Spill Target (Bathing Season) must be -1 (ignore) or non-negative")

        if self.pff_increase < 0:
            errors.append("PFF Increase must be non-negative")

        if self.tank_volume is not None and self.tank_volume < 0:
            errors.append("Tank Volume must be non-negative")

        if self.pump_rate < 0:
            errors.append("Pump Rate must be non-negative")

        return errors

    def is_valid(self) -> bool:
        """Quick validity check."""
        return len(self.validate()) == 0

    @classmethod
    def from_dict(cls, data: dict) -> "CSOConfiguration":
        """
        Create from legacy dict format (from GUI table).
        Handles type conversion and default values.
        """
        # Parse dates
        start_date = cls._parse_datetime(
            data.get('Start Date (dd/mm/yy hh:mm:ss)'))
        end_date = cls._parse_datetime(
            data.get('End Date (dd/mm/yy hh:mm:ss)'))

        # Parse bathing season dates (dd/mm format)
        bathing_start = cls._parse_day_month(
            data.get('Bathing Season Start (dd/mm)', '15/05'))
        bathing_end = cls._parse_day_month(
            data.get('Bathing Season End (dd/mm)', '30/09'))

        # Parse bathing target - treat 0 or negative as "ignore bathing season" (-1)
        bathing_target_raw = data.get('Spill Target (Bathing Seasons)', 0)
        try:
            bathing_target = int(
                bathing_target_raw) if bathing_target_raw else 0
        except (ValueError, TypeError):
            bathing_target = 0

        # If 0 or negative, convert to -1 to clearly indicate "not using bathing mode"
        if bathing_target <= 0:
            bathing_target = -1

        # Extract overflow link (first one if multiple)
        overflow_links = data.get('Overflow Links', [])
        if isinstance(overflow_links, list) and overflow_links:
            overflow_link = overflow_links[0]
        elif isinstance(overflow_links, str):
            overflow_link = overflow_links
        else:
            # Fallback: use CSO name as overflow link (for backwards compatibility with old configs)
            overflow_link = str(data.get('CSO Name', ''))

        return cls(
            cso_name=str(data.get('CSO Name', '')),
            overflow_link=overflow_link,
            continuation_link=str(data.get('Continuation Link', '')),
            run_suffix=str(data.get('Run Suffix', '001')),
            start_date=start_date,
            end_date=end_date,
            spill_target_entire=int(
                data.get('Spill Target (Entire Period)', 0)),
            spill_target_bathing=bathing_target,
            bathing_season_start=bathing_start,
            bathing_season_end=bathing_end,
            pff_increase=float(data.get('PFF Increase (m3/s)', 0.0)),
            tank_volume=float(data['Tank Volume (m3)']) if data.get(
                'Tank Volume (m3)') else None,
            pump_rate=float(data.get('Pump Rate (m3/s)', 0.0)),
            pumping_mode=str(data.get('Pumping Mode', 'Fixed')),
            flow_return_threshold=float(
                data.get('Flow Return Threshold (m3/s)', 0.0)),
            depth_return_threshold=float(
                data.get('Depth Return Threshold (m)', 0.0)),
            time_delay=float(data.get('Time Delay (hours)', 0.0)),
            spill_flow_threshold=float(
                data.get('Spill Flow Threshold (m3/s)', 0.0)),
            spill_volume_threshold=float(
                data.get('Spill Volume Threshold (m3)', 0.0)),
        )

    def to_legacy_dict(self) -> dict:
        """Convert back to legacy dict format for backwards compatibility."""
        return {
            'CSO Name': self.cso_name,
            'Overflow Link': self.overflow_link,
            'Continuation Link': self.continuation_link,
            'Run Suffix': self.run_suffix,
            'Start Date (dd/mm/yy hh:mm:ss)': self.start_date.strftime('%d/%m/%Y %H:%M:%S'),
            'End Date (dd/mm/yy hh:mm:ss)': self.end_date.strftime('%d/%m/%Y %H:%M:%S'),
            'Spill Target (Entire Period)': self.spill_target_entire,
            'Spill Target (Bathing Seasons)': self.spill_target_bathing,
            'Bathing Season Start (dd/mm)': self.bathing_season_start.strftime('%d/%m'),
            'Bathing Season End (dd/mm)': self.bathing_season_end.strftime('%d/%m'),
            'PFF Increase (m3/s)': self.pff_increase,
            'Tank Volume (m3)': self.tank_volume,
            'Pump Rate (m3/s)': self.pump_rate,
            'Pumping Mode': self.pumping_mode,
            'Flow Return Threshold (m3/s)': self.flow_return_threshold,
            'Depth Return Threshold (m)': self.depth_return_threshold,
            'Time Delay (hours)': self.time_delay,
            'Spill Flow Threshold (m3/s)': self.spill_flow_threshold,
            'Spill Volume Threshold (m3)': self.spill_volume_threshold,
        }

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """Parse datetime from various formats."""
        if isinstance(value, datetime):
            return value

        formats = [
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%y %H:%M:%S',
            '%d/%m/%y %H:%M',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except (ValueError, TypeError):
                continue

        raise ValueError(f"Could not parse datetime: {value}")

    @staticmethod
    def _parse_day_month(value: str) -> date:
        """Parse day/month (dd/mm) into a date object (year 2000)."""
        if isinstance(value, date):
            return value

        try:
            day, month = map(int, value.split('/'))
            return date(2000, month, day)
        except (ValueError, AttributeError):
            return date(2000, 5, 15)  # Default
