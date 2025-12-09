"""Convert between legacy single-table and new asset/scenario formats."""

from typing import List, Tuple, Dict, Any
from datetime import datetime
from collections import defaultdict

from .asset_models import CSOAsset, AnalysisScenario


def split_legacy_to_assets_scenarios(
    legacy_rows: List[Dict[str, Any]]
) -> Tuple[List[CSOAsset], List[AnalysisScenario]]:
    """
    Convert legacy single-table format to asset/scenario format.

    Extracts unique CSO definitions and creates scenarios for each row.
    Eliminates duplication where same CSO appears multiple times.

    Args:
        legacy_rows: List of dicts with legacy column names like:
            'CSO Name', 'Continuation Link', 'Start Date', etc.

    Returns:
        Tuple of (assets, scenarios)
    """
    # Group rows by CSO Name to detect duplicates
    cso_groups = defaultdict(list)
    for row in legacy_rows:
        cso_name = row.get('CSO Name', '').strip()
        if cso_name:
            cso_groups[cso_name].append(row)

    assets = []
    scenarios = []

    for cso_name, rows in cso_groups.items():
        # Use first row to define asset (assuming consistent data)
        first_row = rows[0]

        # Extract asset properties (should be same across all rows for this CSO)
        try:
            asset = CSOAsset(
                name=cso_name,
                continuation_link=first_row.get('Continuation Link', ''),
                # You may need to add this column
                data_folder=first_row.get('Data Folder', ''),
                # You may need to add this column
                file_type=first_row.get('File Type', 'csv'),
                timestep_length=int(first_row.get(
                    'Timestep Length', 15)),  # Add if needed
                spill_flow_threshold=float(first_row.get(
                    'Spill Flow Threshold (m3/s)', 0.001)),
                spill_volume_threshold=float(first_row.get(
                    'Spill Volume Threshold (m3)', 0.0)),
            )
            assets.append(asset)
        except Exception as e:
            print(f"Warning: Could not create asset for {cso_name}: {e}")
            continue

        # Create scenario for each row
        for idx, row in enumerate(rows):
            try:
                # Parse dates
                start_date = parse_date(
                    row.get('Start Date (dd/mm/yy hh:mm:ss)', ''))
                end_date = parse_date(
                    row.get('End Date (dd/mm/yy hh:mm:ss)', ''))

                # Get bathing season target (empty string = None)
                bathing_target_str = row.get(
                    'Spill Target (Bathing Seasons)', '').strip()
                bathing_target = int(
                    bathing_target_str) if bathing_target_str else None

                # Determine model based on parameters
                model = determine_model_from_legacy(row)

                scenario = AnalysisScenario(
                    cso_name=cso_name,
                    scenario_name=f"Scenario_{idx+1}" if len(
                        rows) > 1 else "Base",
                    mode="Default",  # Legacy didn't specify, default to this
                    model=model,
                    start_date=start_date,
                    end_date=end_date,
                    spill_target=int(
                        row.get('Spill Target (Entire Period)', 10)),
                    spill_target_bathing=bathing_target,
                    bathing_season_start=row.get(
                        'Bathing Season Start (dd/mm)') or None,
                    bathing_season_end=row.get(
                        'Bathing Season End (dd/mm)') or None,
                    pff_increase=float(row.get('PFF Increase (m3/s)', 0.0)),
                    tank_volume=float(row.get('Tank Volume (m3)', 0)) or None,
                    pumping_mode=row.get('Pumping Mode', 'Fixed'),
                    pump_rate=float(row.get('Pump Rate (m3/s)', 0.0)),
                    flow_return_threshold=float(
                        row.get('Flow Return Threshold (m3/s)', 0.0)),
                    depth_return_threshold=float(
                        row.get('Depth Return Threshold (m)', 0.0)),
                    time_delay=int(row.get('Time Delay (hours)', 0)),
                    run_suffix=row.get('Run Suffix', '001'),
                )
                scenarios.append(scenario)
            except Exception as e:
                print(
                    f"Warning: Could not create scenario for {cso_name} row {idx}: {e}")
                continue

    return assets, scenarios


def determine_model_from_legacy(row: Dict[str, Any]) -> int:
    """
    Infer which model to use based on legacy parameters.

    Legacy didn't explicitly specify model, but we can guess:
    - If bathing season target specified -> Model 4
    - If tank volume > 0 and no iteration -> Model 2
    - Otherwise -> Model 1 (Classical)
    """
    bathing_target = row.get('Spill Target (Bathing Seasons)', '').strip()
    tank_volume = float(row.get('Tank Volume (m3)', 0))

    if bathing_target:
        return 4  # Bathing Season Assessment
    elif tank_volume > 0:
        # Fixed Tank (user may need to adjust if they want Model 1 with tank)
        return 2
    else:
        return 1  # Classical Approach


def merge_assets_scenarios_to_legacy(
    assets: List[CSOAsset],
    scenarios: List[AnalysisScenario]
) -> List[Dict[str, Any]]:
    """
    Convert asset/scenario format back to legacy single-table format.

    Each scenario creates one row with asset data duplicated.
    Compatible with existing CSO Configuration tab.

    Args:
        assets: List of CSOAsset objects
        scenarios: List of AnalysisScenario objects

    Returns:
        List of dicts with legacy column names
    """
    # Create lookup for assets by name
    asset_map = {asset.name: asset for asset in assets}

    legacy_rows = []

    for scenario in scenarios:
        asset = asset_map.get(scenario.cso_name)
        if not asset:
            print(
                f"Warning: No asset found for scenario {scenario.scenario_name} (CSO: {scenario.cso_name})")
            continue

        # Build legacy row dict
        row = {
            'CSO Name': asset.name,
            'Continuation Link': asset.continuation_link,
            'Run Suffix': scenario.run_suffix,
            'Start Date (dd/mm/yy hh:mm:ss)': scenario.start_date.strftime('%d/%m/%Y %H:%M:%S'),
            'End Date (dd/mm/yy hh:mm:ss)': scenario.end_date.strftime('%d/%m/%Y %H:%M:%S'),
            'Spill Target (Entire Period)': str(scenario.spill_target),
            'Spill Target (Bathing Seasons)': str(scenario.spill_target_bathing) if scenario.spill_target_bathing else '',
            'Bathing Season Start (dd/mm)': scenario.bathing_season_start or '15/05',
            'Bathing Season End (dd/mm)': scenario.bathing_season_end or '30/09',
            'PFF Increase (m3/s)': str(scenario.pff_increase),
            'Tank Volume (m3)': str(scenario.tank_volume) if scenario.tank_volume else '0',
            'Pumping Mode': scenario.pumping_mode,
            'Pump Rate (m3/s)': str(scenario.pump_rate),
            'Flow Return Threshold (m3/s)': str(scenario.flow_return_threshold),
            'Depth Return Threshold (m)': str(scenario.depth_return_threshold),
            'Time Delay (hours)': str(scenario.time_delay),
            'Spill Flow Threshold (m3/s)': str(asset.spill_flow_threshold),
            'Spill Volume Threshold (m3)': str(asset.spill_volume_threshold),
            # Optional: Add these if your tab supports them
            # 'Data Folder': asset.data_folder,
            # 'File Type': asset.file_type,
            # 'Timestep Length': str(asset.timestep_length),
        }

        legacy_rows.append(row)

    return legacy_rows


def parse_date(date_str: str) -> datetime:
    """Parse date from various legacy formats."""
    if not date_str:
        return datetime.now()

    formats = [
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%y %H:%M:%S',
        '%d/%m/%y %H:%M',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    # Last resort
    return datetime.now()


# Example usage:
"""
# From legacy configuration tab
legacy_rows = cso_config_tab.get_all_rows_as_dicts()

# Split into assets and scenarios
assets, scenarios = split_legacy_to_assets_scenarios(legacy_rows)

# Load into new tabs
assets_tab.load_assets(assets)
scenarios_tab.load_scenarios(scenarios)

# ===== OR GO THE OTHER WAY =====

# From new tabs
assets = assets_tab.get_assets()
scenarios = scenarios_tab.get_scenarios()

# Merge back to legacy format
legacy_rows = merge_assets_scenarios_to_legacy(assets, scenarios)

# Run through both engines
for row in legacy_rows:
    legacy_result = legacy_engine.run(row)
    
    # Also run refactored
    scenario = [s for s in scenarios if s.cso_name == row['CSO Name']][0]
    asset = [a for a in assets if a.name == row['CSO Name']][0]
    refactored_result = refactored_engine.run(asset, scenario)
    
    # Compare
    compare(legacy_result, refactored_result)
"""
