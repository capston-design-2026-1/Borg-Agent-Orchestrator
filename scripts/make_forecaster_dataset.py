import os
from pathlib import Path

import polars as pl

DEFAULT_DATASET_DIR = Path.home() / "Documents" / "borg_processed" / "datasets"
DEFAULT_OUTPUT_DIR = DEFAULT_DATASET_DIR / "forecaster"
DEFAULT_CLUSTERS = ("b", "c", "d", "e", "f", "g")
DEFAULT_FAILURE_EVENT_TYPES = (2, 3, 6)
DEFAULT_PREDICTION_HORIZON = 15 * 60 * 1_000_000

DATASET_DIR = Path(os.environ.get("BORG_DATASET_DIR", DEFAULT_DATASET_DIR)).expanduser()
OUTPUT_DIR = Path(os.environ.get("BORG_FORECASTER_DIR", DEFAULT_OUTPUT_DIR)).expanduser()


def parse_clusters() -> list[str]:
    raw = os.environ.get("BORG_CLUSTERS")
    if not raw:
        return list(DEFAULT_CLUSTERS)
    return [cluster.strip() for cluster in raw.split(",") if cluster.strip()]


def parse_failure_event_types() -> list[int]:
    raw = os.environ.get("BORG_FAILURE_EVENT_TYPES")
    if not raw:
        return list(DEFAULT_FAILURE_EVENT_TYPES)
    return [int(value.strip()) for value in raw.split(",") if value.strip()]


def prediction_horizon() -> int:
    raw = os.environ.get("BORG_PREDICTION_HORIZON_US")
    if not raw:
        return DEFAULT_PREDICTION_HORIZON
    return int(raw)


def dataset_file(cluster_id: str) -> Path:
    return DATASET_DIR / f"{cluster_id}_dataset.parquet"


def output_file(cluster_id: str) -> Path:
    return OUTPUT_DIR / f"{cluster_id}_forecaster.parquet"


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


def build_forecaster_frame(cluster_id: str) -> pl.DataFrame:
    from src.advanced_xgboost.features import build_feature_frame

    if prediction_horizon() != DEFAULT_PREDICTION_HORIZON:
        raise ValueError("The baseline target is 15 minutes; use the advanced track for other horizons")
    return build_feature_frame(
        pl.scan_parquet(dataset_file(cluster_id)), parse_failure_event_types(), [15]
    ).collect(engine="streaming")


def write_forecaster_frame(cluster_id: str) -> Path:
    frame = build_forecaster_frame(cluster_id)
    path = output_file(cluster_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "README.md").write_text(
        "# Baseline forecaster features (causal schema v2)\n\n"
        "Prediction time is end_time. target_failure_15m is null without complete future event coverage. "
        "Use only the declared model feature columns; future outcome fields are label metadata.\n",
        encoding="utf-8",
    )
    frame.write_parquet(path)

    positive_rows = frame.filter(pl.col("target_failure_15m")).height
    positive_rate = positive_rows / frame.height if frame.height else 0.0

    print(
        f"✅ {cluster_id}: wrote {frame.height} rows to {path} "
        f"(positive labels: {positive_rows}, rate: {positive_rate:.4%})"
    )
    return path


def main() -> None:
    clusters = parse_clusters()

    print(f"Reading joined datasets from: {DATASET_DIR}")
    print(f"Writing forecaster datasets to: {OUTPUT_DIR}")
    print(f"Clusters: {clusters}")
    print(f"Failure event types: {parse_failure_event_types()}")
    print(f"Prediction horizon (us): {prediction_horizon()}")

    for cluster_id in clusters:
        path = dataset_file(cluster_id)
        if not path.exists():
            print(f"Skipping {cluster_id}: missing {path.name}")
            continue
        write_forecaster_frame(cluster_id)


if __name__ == "__main__":
    main()
