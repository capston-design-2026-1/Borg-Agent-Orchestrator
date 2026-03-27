from __future__ import annotations

import polars as pl


ADVANCED_FEATURE_COLUMNS = (
    "usage_window",
    "avg_cpu",
    "max_cpu",
    "avg_mem",
    "max_mem",
    "avg_cpu_utilization",
    "max_cpu_utilization",
    "avg_mem_utilization",
    "max_mem_utilization",
    "req_cpu",
    "req_mem",
    "priority",
    "scheduling_class",
    "event_count",
    "task_age_us",
    "machine_cpu",
    "machine_mem",
    "cpu_request_ratio",
    "mem_request_ratio",
    "avg_cpu_to_request_ratio",
    "avg_mem_to_request_ratio",
    "max_cpu_to_request_ratio",
    "max_mem_to_request_ratio",
    "cpu_headroom",
    "mem_headroom",
    "cpu_spike_gap",
    "mem_spike_gap",
    "machine_task_count_window",
    "collection_task_count_window",
    "machine_window_avg_cpu_sum",
    "machine_window_avg_mem_sum",
    "machine_window_avg_cpu_load_ratio",
    "machine_window_avg_mem_load_ratio",
    "collection_window_avg_cpu_sum",
    "collection_window_avg_mem_sum",
    "avg_cpu_roll6_std",
    "avg_mem_roll6_std",
    "avg_cpu_utilization_roll6_std",
    "avg_mem_utilization_roll6_std",
    "observed_failure_by_window",
    "machine_recent_failure_count_12",
    "collection_recent_failure_count_12",
    "machine_recent_terminal_count_12",
    "collection_recent_terminal_count_12",
    "avg_cpu_lag_1",
    "avg_cpu_delta_1",
    "avg_cpu_roll3_mean",
    "max_cpu_lag_1",
    "max_cpu_delta_1",
    "max_cpu_roll3_mean",
    "avg_mem_lag_1",
    "avg_mem_delta_1",
    "avg_mem_roll3_mean",
    "max_mem_lag_1",
    "max_mem_delta_1",
    "max_mem_roll3_mean",
    "avg_cpu_utilization_lag_1",
    "avg_cpu_utilization_delta_1",
    "avg_cpu_utilization_roll3_mean",
    "max_cpu_utilization_lag_1",
    "max_cpu_utilization_delta_1",
    "max_cpu_utilization_roll3_mean",
    "avg_mem_utilization_lag_1",
    "avg_mem_utilization_delta_1",
    "avg_mem_utilization_roll3_mean",
    "max_mem_utilization_lag_1",
    "max_mem_utilization_delta_1",
    "max_mem_utilization_roll3_mean",
)

MISSINGNESS_BASE_COLUMNS = (
    "avg_cpu",
    "max_cpu",
    "avg_mem",
    "max_mem",
    "avg_cpu_utilization",
    "max_cpu_utilization",
    "avg_mem_utilization",
    "max_mem_utilization",
    "req_cpu",
    "req_mem",
    "priority",
    "scheduling_class",
    "task_age_us",
    "machine_cpu",
    "machine_mem",
    "cpu_request_ratio",
    "mem_request_ratio",
    "avg_cpu_to_request_ratio",
    "avg_mem_to_request_ratio",
    "max_cpu_to_request_ratio",
    "max_mem_to_request_ratio",
    "cpu_headroom",
    "mem_headroom",
    "cpu_spike_gap",
    "mem_spike_gap",
    "machine_task_count_window",
    "collection_task_count_window",
    "machine_window_avg_cpu_sum",
    "machine_window_avg_mem_sum",
    "machine_window_avg_cpu_load_ratio",
    "machine_window_avg_mem_load_ratio",
    "collection_window_avg_cpu_sum",
    "collection_window_avg_mem_sum",
    "avg_cpu_roll6_std",
    "avg_mem_roll6_std",
    "avg_cpu_utilization_roll6_std",
    "avg_mem_utilization_roll6_std",
    "machine_recent_failure_count_12",
    "collection_recent_failure_count_12",
    "machine_recent_terminal_count_12",
    "collection_recent_terminal_count_12",
)

MISSINGNESS_FLAG_COLUMNS = tuple(f"{column}_is_missing" for column in MISSINGNESS_BASE_COLUMNS)


def safe_ratio(numerator: str, denominator: str, alias: str) -> pl.Expr:
    return (
        pl.when(pl.col(denominator).is_not_null() & (pl.col(denominator) != 0))
        .then(pl.col(numerator) / pl.col(denominator))
        .otherwise(None)
        .alias(alias)
    )


def add_temporal_features(frame: pl.LazyFrame) -> pl.LazyFrame:
    task_keys = ["collection_id", "instance_index"]
    temporal_bases = [
        "avg_cpu",
        "max_cpu",
        "avg_mem",
        "max_mem",
        "avg_cpu_utilization",
        "max_cpu_utilization",
        "avg_mem_utilization",
        "max_mem_utilization",
    ]

    expressions: list[pl.Expr] = []
    for feature in temporal_bases:
        lag_expr = pl.col(feature).shift(1).over(task_keys)
        expressions.extend(
            [
                lag_expr.alias(f"{feature}_lag_1"),
                (pl.col(feature) - lag_expr).alias(f"{feature}_delta_1"),
                pl.col(feature).rolling_mean(window_size=3, min_samples=1).over(task_keys).alias(f"{feature}_roll3_mean"),
            ]
        )

    return frame.with_columns(expressions)


def build_feature_frame(dataset: pl.LazyFrame, failure_event_types: list[int], horizon_us: int) -> pl.LazyFrame:
    task_keys = ["collection_id", "instance_index"]
    enriched = (
        dataset
        .sort(["machine_id", "collection_id", "instance_index", "end_time"])
        .with_columns(
            [
                (pl.col("end_time") - pl.col("first_event_time")).alias("task_age_us"),
                (pl.col("last_event_time") - pl.col("end_time")).alias("time_to_terminal_event_us"),
                pl.col("final_event_type").is_in(failure_event_types).alias("is_failure_terminal_event"),
                (pl.col("machine_cpu") - pl.col("avg_cpu")).alias("cpu_headroom"),
                (pl.col("machine_mem") - pl.col("avg_mem")).alias("mem_headroom"),
                (pl.col("max_cpu") - pl.col("avg_cpu")).alias("cpu_spike_gap"),
                (pl.col("max_mem") - pl.col("avg_mem")).alias("mem_spike_gap"),
                pl.len().over(["machine_id", "end_time"]).alias("machine_task_count_window"),
                pl.len().over(["collection_id", "end_time"]).alias("collection_task_count_window"),
                pl.col("avg_cpu").sum().over(["machine_id", "end_time"]).alias("machine_window_avg_cpu_sum"),
                pl.col("avg_mem").sum().over(["machine_id", "end_time"]).alias("machine_window_avg_mem_sum"),
                pl.col("avg_cpu").sum().over(["collection_id", "end_time"]).alias("collection_window_avg_cpu_sum"),
                pl.col("avg_mem").sum().over(["collection_id", "end_time"]).alias("collection_window_avg_mem_sum"),
            ]
        )
        .with_columns(
            [
                safe_ratio("req_cpu", "machine_cpu", "cpu_request_ratio"),
                safe_ratio("req_mem", "machine_mem", "mem_request_ratio"),
                safe_ratio("avg_cpu", "req_cpu", "avg_cpu_to_request_ratio"),
                safe_ratio("avg_mem", "req_mem", "avg_mem_to_request_ratio"),
                safe_ratio("max_cpu", "req_cpu", "max_cpu_to_request_ratio"),
                safe_ratio("max_mem", "req_mem", "max_mem_to_request_ratio"),
                safe_ratio("machine_window_avg_cpu_sum", "machine_cpu", "machine_window_avg_cpu_load_ratio"),
                safe_ratio("machine_window_avg_mem_sum", "machine_mem", "machine_window_avg_mem_load_ratio"),
            ]
        )
        .pipe(add_temporal_features)
        .with_columns(
            [
                pl.col("avg_cpu").rolling_std(window_size=6, min_samples=2).over(task_keys).alias("avg_cpu_roll6_std"),
                pl.col("avg_mem").rolling_std(window_size=6, min_samples=2).over(task_keys).alias("avg_mem_roll6_std"),
                pl.col("avg_cpu_utilization").rolling_std(window_size=6, min_samples=2).over(task_keys).alias("avg_cpu_utilization_roll6_std"),
                pl.col("avg_mem_utilization").rolling_std(window_size=6, min_samples=2).over(task_keys).alias("avg_mem_utilization_roll6_std"),
                (
                    pl.col("is_failure_terminal_event") &
                    pl.col("time_to_terminal_event_us").is_not_null() &
                    (pl.col("time_to_terminal_event_us") >= 0) &
                    (pl.col("time_to_terminal_event_us") <= horizon_us)
                ).alias("target_failure_15m"),
                (
                    pl.col("final_event_type").is_not_null() &
                    (pl.col("last_event_time") <= pl.col("end_time"))
                ).alias("terminal_event_before_window_end"),
            ]
        )
        .with_columns(
            [
                (
                    pl.col("is_failure_terminal_event") &
                    pl.col("terminal_event_before_window_end")
                ).cast(pl.Int8).alias("observed_failure_by_window"),
                (
                    pl.col("final_event_type").is_not_null() &
                    pl.col("terminal_event_before_window_end")
                ).cast(pl.Int8).alias("observed_terminal_by_window"),
            ]
        )
        .with_columns(
            [
                (
                    pl.col("observed_failure_by_window")
                    .shift(1)
                    .fill_null(0)
                    .rolling_sum(window_size=12, min_samples=1)
                    .over("machine_id")
                ).alias("machine_recent_failure_count_12"),
                (
                    pl.col("observed_failure_by_window")
                    .shift(1)
                    .fill_null(0)
                    .rolling_sum(window_size=12, min_samples=1)
                    .over("collection_id")
                ).alias("collection_recent_failure_count_12"),
                (
                    pl.col("observed_terminal_by_window")
                    .shift(1)
                    .fill_null(0)
                    .rolling_sum(window_size=12, min_samples=1)
                    .over("machine_id")
                ).alias("machine_recent_terminal_count_12"),
                (
                    pl.col("observed_terminal_by_window")
                    .shift(1)
                    .fill_null(0)
                    .rolling_sum(window_size=12, min_samples=1)
                    .over("collection_id")
                ).alias("collection_recent_terminal_count_12"),
            ]
        )
        .with_columns(
            [
                pl.col(column).is_null().cast(pl.Int8).alias(f"{column}_is_missing")
                for column in MISSINGNESS_BASE_COLUMNS
            ]
        )
    )

    return enriched.select(
        [
            pl.col("cluster_id"),
            pl.col("collection_id"),
            pl.col("instance_index"),
            pl.col("machine_id"),
            pl.col("start_time"),
            pl.col("end_time"),
            pl.col("source_cluster"),
            *[pl.col(column) for column in ADVANCED_FEATURE_COLUMNS],
            *[pl.col(column) for column in MISSINGNESS_FLAG_COLUMNS],
            pl.col("first_event_time"),
            pl.col("last_event_time"),
            pl.col("final_event_type"),
            pl.col("time_to_terminal_event_us"),
            pl.col("is_failure_terminal_event"),
            pl.col("observed_terminal_by_window"),
            pl.col("terminal_event_before_window_end"),
            pl.col("target_failure_15m"),
        ]
    )
