from __future__ import annotations

from pathlib import Path

import polars as pl

COMMON_FORECASTER_SCHEMA_VERSION = "v1"
COMMON_FORECASTER_COLUMNS = (
    "source_platform",
    "source_schema_version",
    "source_cluster_id",
    "source_workload_id",
    "source_workload_instance_id",
    "source_node_id",
    "window_start_us",
    "window_end_us",
    "window_duration_us",
    "observed_cpu_avg",
    "observed_cpu_peak",
    "observed_mem_avg",
    "observed_mem_peak",
    "observed_cpu_avg_ratio",
    "observed_cpu_peak_ratio",
    "observed_mem_avg_ratio",
    "observed_mem_peak_ratio",
    "requested_cpu",
    "requested_mem",
    "workload_priority",
    "workload_class",
    "event_count",
    "cpu_avg_prev_1",
    "cpu_avg_delta_1",
    "cpu_avg_roll3_mean",
    "cpu_peak_prev_1",
    "cpu_peak_delta_1",
    "cpu_peak_roll3_mean",
    "mem_avg_prev_1",
    "mem_avg_delta_1",
    "mem_avg_roll3_mean",
    "mem_peak_prev_1",
    "mem_peak_delta_1",
    "mem_peak_roll3_mean",
    "cpu_avg_ratio_prev_1",
    "cpu_avg_ratio_delta_1",
    "cpu_avg_ratio_roll3_mean",
    "cpu_peak_ratio_prev_1",
    "cpu_peak_ratio_delta_1",
    "cpu_peak_ratio_roll3_mean",
    "mem_avg_ratio_prev_1",
    "mem_avg_ratio_delta_1",
    "mem_avg_ratio_roll3_mean",
    "mem_peak_ratio_prev_1",
    "mem_peak_ratio_delta_1",
    "mem_peak_ratio_roll3_mean",
    "terminal_event_time_us",
    "terminal_event_type",
    "time_to_terminal_event_us",
    "is_failure_terminal_event",
    "target_failure_within_horizon",
    "terminal_event_before_window_end",
)


def common_forecaster_output_dir(base_dir: Path) -> Path:
    return base_dir / "common_forecaster"


def common_forecaster_file(base_dir: Path, cluster_id: str) -> Path:
    return common_forecaster_output_dir(base_dir) / f"{cluster_id}_common_forecaster.parquet"


def canonicalize_forecaster_frame(frame: pl.DataFrame, source_platform: str = "borg") -> pl.DataFrame:
    canonical = frame.select(
        [
            pl.lit(source_platform).alias("source_platform"),
            pl.lit(COMMON_FORECASTER_SCHEMA_VERSION).alias("source_schema_version"),
            pl.col("cluster_id").cast(pl.Utf8, strict=False).alias("source_cluster_id"),
            pl.col("collection_id").cast(pl.Utf8, strict=False).alias("source_workload_id"),
            pl.col("instance_index").cast(pl.Utf8, strict=False).alias("source_workload_instance_id"),
            pl.col("machine_id").cast(pl.Utf8, strict=False).alias("source_node_id"),
            pl.col("start_time").cast(pl.Int64, strict=False).alias("window_start_us"),
            pl.col("end_time").cast(pl.Int64, strict=False).alias("window_end_us"),
            pl.col("usage_window").cast(pl.Int64, strict=False).alias("window_duration_us"),
            pl.col("avg_cpu").cast(pl.Float64, strict=False).alias("observed_cpu_avg"),
            pl.col("max_cpu").cast(pl.Float64, strict=False).alias("observed_cpu_peak"),
            pl.col("avg_mem").cast(pl.Float64, strict=False).alias("observed_mem_avg"),
            pl.col("max_mem").cast(pl.Float64, strict=False).alias("observed_mem_peak"),
            pl.col("avg_cpu_utilization").cast(pl.Float64, strict=False).alias("observed_cpu_avg_ratio"),
            pl.col("max_cpu_utilization").cast(pl.Float64, strict=False).alias("observed_cpu_peak_ratio"),
            pl.col("avg_mem_utilization").cast(pl.Float64, strict=False).alias("observed_mem_avg_ratio"),
            pl.col("max_mem_utilization").cast(pl.Float64, strict=False).alias("observed_mem_peak_ratio"),
            pl.col("req_cpu").cast(pl.Float64, strict=False).alias("requested_cpu"),
            pl.col("req_mem").cast(pl.Float64, strict=False).alias("requested_mem"),
            pl.col("priority").cast(pl.Int64, strict=False).alias("workload_priority"),
            pl.col("scheduling_class").cast(pl.Int64, strict=False).alias("workload_class"),
            pl.col("event_count").cast(pl.UInt32, strict=False).alias("event_count"),
            pl.col("avg_cpu_lag_1").cast(pl.Float64, strict=False).alias("cpu_avg_prev_1"),
            pl.col("avg_cpu_delta_1").cast(pl.Float64, strict=False).alias("cpu_avg_delta_1"),
            pl.col("avg_cpu_roll3_mean").cast(pl.Float64, strict=False).alias("cpu_avg_roll3_mean"),
            pl.col("max_cpu_lag_1").cast(pl.Float64, strict=False).alias("cpu_peak_prev_1"),
            pl.col("max_cpu_delta_1").cast(pl.Float64, strict=False).alias("cpu_peak_delta_1"),
            pl.col("max_cpu_roll3_mean").cast(pl.Float64, strict=False).alias("cpu_peak_roll3_mean"),
            pl.col("avg_mem_lag_1").cast(pl.Float64, strict=False).alias("mem_avg_prev_1"),
            pl.col("avg_mem_delta_1").cast(pl.Float64, strict=False).alias("mem_avg_delta_1"),
            pl.col("avg_mem_roll3_mean").cast(pl.Float64, strict=False).alias("mem_avg_roll3_mean"),
            pl.col("max_mem_lag_1").cast(pl.Float64, strict=False).alias("mem_peak_prev_1"),
            pl.col("max_mem_delta_1").cast(pl.Float64, strict=False).alias("mem_peak_delta_1"),
            pl.col("max_mem_roll3_mean").cast(pl.Float64, strict=False).alias("mem_peak_roll3_mean"),
            pl.col("avg_cpu_utilization_lag_1").cast(pl.Float64, strict=False).alias("cpu_avg_ratio_prev_1"),
            pl.col("avg_cpu_utilization_delta_1").cast(pl.Float64, strict=False).alias("cpu_avg_ratio_delta_1"),
            pl.col("avg_cpu_utilization_roll3_mean").cast(pl.Float64, strict=False).alias("cpu_avg_ratio_roll3_mean"),
            pl.col("max_cpu_utilization_lag_1").cast(pl.Float64, strict=False).alias("cpu_peak_ratio_prev_1"),
            pl.col("max_cpu_utilization_delta_1").cast(pl.Float64, strict=False).alias("cpu_peak_ratio_delta_1"),
            pl.col("max_cpu_utilization_roll3_mean").cast(pl.Float64, strict=False).alias("cpu_peak_ratio_roll3_mean"),
            pl.col("avg_mem_utilization_lag_1").cast(pl.Float64, strict=False).alias("mem_avg_ratio_prev_1"),
            pl.col("avg_mem_utilization_delta_1").cast(pl.Float64, strict=False).alias("mem_avg_ratio_delta_1"),
            pl.col("avg_mem_utilization_roll3_mean").cast(pl.Float64, strict=False).alias("mem_avg_ratio_roll3_mean"),
            pl.col("max_mem_utilization_lag_1").cast(pl.Float64, strict=False).alias("mem_peak_ratio_prev_1"),
            pl.col("max_mem_utilization_delta_1").cast(pl.Float64, strict=False).alias("mem_peak_ratio_delta_1"),
            pl.col("max_mem_utilization_roll3_mean").cast(pl.Float64, strict=False).alias("mem_peak_ratio_roll3_mean"),
            pl.col("last_event_time").cast(pl.Int64, strict=False).alias("terminal_event_time_us"),
            pl.col("final_event_type").cast(pl.Int64, strict=False).alias("terminal_event_type"),
            pl.col("time_to_terminal_event_us").cast(pl.Int64, strict=False).alias("time_to_terminal_event_us"),
            pl.col("is_failure_terminal_event").cast(pl.Boolean, strict=False).alias("is_failure_terminal_event"),
            pl.col("target_failure_15m").cast(pl.Boolean, strict=False).alias("target_failure_within_horizon"),
            pl.col("terminal_event_before_window_end").cast(pl.Boolean, strict=False).alias("terminal_event_before_window_end"),
        ]
    )
    missing = [column for column in COMMON_FORECASTER_COLUMNS if column not in canonical.columns]
    if missing:
        raise ValueError(f"Canonical forecaster frame is missing required columns: {missing}")
    return canonical.select(list(COMMON_FORECASTER_COLUMNS))
