"""Utilities for building effective CSO time series from raw data exports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from .config import DataSourceInfo, EffectiveCSODefinition


@dataclass(slots=True)
class EffectiveCSOTimeSeries:
    """Aggregated time-series data for a user-defined effective CSO."""

    name: str
    data: pd.DataFrame
    components: Dict[str, Sequence[str]] = field(default_factory=dict)

    @property
    def flow_column(self) -> str:
        return f"{self.name}_overflow_flow"

    @property
    def continuation_column(self) -> str:
        return f"{self.name}_continuation_flow"

    @property
    def depth_column(self) -> str:
        return f"{self.name}_overflow_depth"

    @property
    def continuation_depth_column(self) -> str:
        return f"{self.name}_continuation_depth"


class EffectiveSeriesBuilderError(RuntimeError):
    """Raised when the builder fails to construct an effective series."""


def build_effective_series(
    definition: EffectiveCSODefinition,
    data_source: DataSourceInfo,
) -> EffectiveCSOTimeSeries:
    """Create aggregated continuation/overflow series for a single CSO.

    Parameters
    ----------
    definition:
        CSO definition that lists constituent continuation and overflow links.
    data_source:
        Metadata describing where the raw InfoWorks exports live.
    """

    if data_source.file_type.lower() != "csv":
        raise EffectiveSeriesBuilderError(
            "Effective CSO builder currently supports CSV exports only."
        )

    data_folder = Path(data_source.data_folder)
    if not data_folder.exists():
        raise EffectiveSeriesBuilderError(
            f"Data folder does not exist: {data_folder}"
        )

    flow_df = _load_link_dataframe(
        data_folder,
        definition.continuation_links + definition.overflow_links,
        suffixes=("_Q.csv", "_us_flow.csv"),
    )

    required_flow_columns = set(
        definition.continuation_links + definition.overflow_links)
    missing_flow = required_flow_columns - set(flow_df.columns)
    if missing_flow:
        raise EffectiveSeriesBuilderError(
            "Flow data missing for links: " + ", ".join(sorted(missing_flow))
        )

    try:
        depth_df = _load_link_dataframe(
            data_folder,
            definition.continuation_links + definition.overflow_links,
            suffixes=("_D.csv", "_us_depth.csv"),
        )
    except EffectiveSeriesBuilderError:
        depth_df = pd.DataFrame({"Time": flow_df["Time"]})

    result = pd.DataFrame({"Time": flow_df["Time"]})

    result[f"{definition.name}_continuation_flow"] = flow_df[definition.continuation_links].sum(
        axis=1)
    result[f"{definition.name}_overflow_flow"] = flow_df[definition.overflow_links].sum(
        axis=1)

    if set(definition.continuation_links).issubset(depth_df.columns):
        result[f"{definition.name}_continuation_depth"] = depth_df[definition.continuation_links].max(
            axis=1)
    else:
        result[f"{definition.name}_continuation_depth"] = pd.NA

    if set(definition.overflow_links).issubset(depth_df.columns):
        result[f"{definition.name}_overflow_depth"] = depth_df[definition.overflow_links].max(
            axis=1)
    else:
        result[f"{definition.name}_overflow_depth"] = pd.NA

    return EffectiveCSOTimeSeries(
        name=definition.name,
        data=result,
        components={
            "continuation": list(definition.continuation_links),
            "overflow": list(definition.overflow_links),
        },
    )


def build_effective_series_bulk(
    definitions: Iterable[EffectiveCSODefinition],
    data_source: DataSourceInfo,
) -> Dict[str, EffectiveCSOTimeSeries]:
    """Build effective series for multiple CSOs."""

    outputs: Dict[str, EffectiveCSOTimeSeries] = {}
    for definition in definitions:
        outputs[definition.name] = build_effective_series(
            definition, data_source)
    return outputs


def _load_link_dataframe(
    data_folder: Path,
    links: Sequence[str],
    suffixes: Sequence[str],
) -> pd.DataFrame:
    """Load selected link columns from CSV exports."""

    import glob

    link_set = set(links)
    if not link_set:
        raise EffectiveSeriesBuilderError("No links provided for aggregation.")

    csv_files: List[str] = []
    for suffix in suffixes:
        csv_files.extend(glob.glob(str(data_folder / f"*{suffix}")))

    if not csv_files:
        raise EffectiveSeriesBuilderError(
            "No CSV exports found with suffixes: " + ", ".join(suffixes)
        )

    merged_df: pd.DataFrame | None = None
    remaining = set(link_set)

    for file_path in csv_files:
        # Read only when we still need columns from this file
        head = pd.read_csv(file_path, nrows=0)
        available_cols = set(head.columns) & remaining
        if not available_cols:
            continue

        use_cols = ["Time"] + sorted(available_cols)
        df = pd.read_csv(
            file_path,
            usecols=use_cols,
            parse_dates=["Time"],
            dayfirst=True,
        )

        merged_df = df if merged_df is None else _merge_on_time(merged_df, df)
        remaining -= available_cols

        if not remaining:
            break

    if merged_df is None:
        raise EffectiveSeriesBuilderError(
            "Requested links not found in CSV exports.")

    merged_df.sort_values("Time", inplace=True)
    merged_df.reset_index(drop=True, inplace=True)
    return merged_df


def _merge_on_time(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    """Merge two time-indexed dataframes on the Time column."""

    merged = pd.merge(left, right, on="Time", how="outer")
    merged.sort_values("Time", inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged
