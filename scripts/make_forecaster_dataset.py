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
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def main() -> None:
    print(f"Reading joined datasets from: {DATASET_DIR}")
    print(f"Writing forecaster datasets to: {OUTPUT_DIR}")
    print(f"Clusters: {parse_clusters()}")
    print(f"Failure event types: {parse_failure_event_types()}")
    print(f"Prediction horizon (us): {prediction_horizon()}")


if __name__ == "__main__":
    main()
