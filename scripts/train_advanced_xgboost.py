import polars as pl

from src.advanced_xgboost.features import target_column_name
from src.advanced_xgboost.settings import feature_store_dir, parse_clusters, parse_prediction_horizon_minutes
from src.advanced_xgboost.train import train_and_evaluate


def feature_file(cluster_id: str):
    return feature_store_dir() / f"{cluster_id}_advanced_failure_features.parquet"


def load_feature_data(clusters: list[str]) -> pl.DataFrame:
    frames = []
    for cluster_id in clusters:
        path = feature_file(cluster_id)
        if not path.exists():
            print(f"Skipping {cluster_id}: missing {path.name}")
            continue
        frames.append(pl.read_parquet(path))

    if not frames:
        raise FileNotFoundError("No advanced feature parquet files were found for the requested clusters.")

    return pl.concat(frames, how="vertical_relaxed")


def main() -> None:
    clusters = parse_clusters()
    print(f"Reading advanced feature datasets from: {feature_store_dir()}")
    print(f"Clusters: {clusters}")
    print(f"Prediction horizons (minutes): {parse_prediction_horizon_minutes()}")
    feature_frame = load_feature_data(clusters)
    all_metrics = []
    for minutes in parse_prediction_horizon_minutes():
        target = target_column_name(minutes)
        metrics = train_and_evaluate(feature_frame, target)
        all_metrics.append(metrics)
        print(f"✅ XGBoost training complete for {target}: {metrics}")


if __name__ == "__main__":
    main()
