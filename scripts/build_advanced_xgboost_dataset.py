import polars as pl

from src.advanced_xgboost.features import build_feature_frame
from src.advanced_xgboost.settings import (
    feature_store_dir,
    joined_dataset_dir,
    parse_clusters,
    parse_failure_event_types,
    prediction_horizon_us,
)


def dataset_file(cluster_id: str):
    return joined_dataset_dir() / f"{cluster_id}_dataset.parquet"


def feature_file(cluster_id: str):
    return feature_store_dir() / f"{cluster_id}_advanced_failure_features.parquet"


def write_cluster_features(cluster_id: str) -> None:
    feature_store_dir().mkdir(parents=True, exist_ok=True)
    frame = build_feature_frame(
        pl.scan_parquet(dataset_file(cluster_id)),
        failure_event_types=parse_failure_event_types(),
        horizon_us=prediction_horizon_us(),
    ).collect(engine="streaming")

    path = feature_file(cluster_id)
    frame.write_parquet(path)
    positives = frame.filter(pl.col("target_failure_15m")).height
    print(
        f"✅ {cluster_id}: wrote {frame.height} rows to {path} "
        f"(positive labels: {positives})"
    )


def main() -> None:
    clusters = parse_clusters()
    print(f"Reading joined datasets from: {joined_dataset_dir()}")
    print(f"Writing advanced feature datasets to: {feature_store_dir()}")
    print(f"Clusters: {clusters}")
    print(f"Failure event types: {parse_failure_event_types()}")
    print(f"Prediction horizon (us): {prediction_horizon_us()}")

    for cluster_id in clusters:
        path = dataset_file(cluster_id)
        if not path.exists():
            print(f"Skipping {cluster_id}: missing {path.name}")
            continue
        write_cluster_features(cluster_id)


if __name__ == "__main__":
    main()
