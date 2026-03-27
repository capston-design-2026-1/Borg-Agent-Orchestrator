import polars as pl

from src.advanced_xgboost.settings import feature_store_dir, parse_clusters
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
    feature_frame = load_feature_data(clusters)
    metrics = train_and_evaluate(feature_frame)
    print(f"✅ XGBoost training complete: {metrics}")


if __name__ == "__main__":
    main()
