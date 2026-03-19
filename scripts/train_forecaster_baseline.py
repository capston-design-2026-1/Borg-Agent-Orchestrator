import json
import os
from pathlib import Path

import polars as pl

DEFAULT_FORECASTER_DIR = Path.home() / "Documents" / "borg_processed" / "datasets" / "forecaster"
DEFAULT_OUTPUT_DIR = DEFAULT_FORECASTER_DIR / "baseline"
DEFAULT_CLUSTERS = ("b", "c", "d", "e", "f", "g")
DEFAULT_VALID_FRACTION = 0.2
DEFAULT_FEATURES = (
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
)

FORECASTER_DIR = Path(os.environ.get("BORG_FORECASTER_DIR", DEFAULT_FORECASTER_DIR)).expanduser()
OUTPUT_DIR = Path(os.environ.get("BORG_BASELINE_DIR", DEFAULT_OUTPUT_DIR)).expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_clusters() -> list[str]:
    raw = os.environ.get("BORG_CLUSTERS")
    if not raw:
        return list(DEFAULT_CLUSTERS)
    return [cluster.strip() for cluster in raw.split(",") if cluster.strip()]


def validation_fraction() -> float:
    raw = os.environ.get("BORG_VALID_FRACTION")
    if not raw:
        return DEFAULT_VALID_FRACTION
    return float(raw)


def feature_names() -> list[str]:
    raw = os.environ.get("BORG_BASELINE_FEATURES")
    if not raw:
        return list(DEFAULT_FEATURES)
    return [feature.strip() for feature in raw.split(",") if feature.strip()]


def forecaster_file(cluster_id: str) -> Path:
    return FORECASTER_DIR / f"{cluster_id}_forecaster.parquet"


def metrics_file() -> Path:
    return OUTPUT_DIR / "metrics.json"


def weights_file() -> Path:
    return OUTPUT_DIR / "weights.json"


def load_forecaster_data(clusters: list[str]) -> pl.DataFrame:
    frames = []
    for cluster_id in clusters:
        path = forecaster_file(cluster_id)
        if not path.exists():
            print(f"Skipping {cluster_id}: missing {path.name}")
            continue
        frames.append(pl.read_parquet(path))

    if not frames:
        raise FileNotFoundError("No forecaster parquet files were found for the requested clusters.")

    return pl.concat(frames, how="vertical_relaxed")


def split_by_time(frame: pl.DataFrame, valid_fraction: float) -> tuple[pl.DataFrame, pl.DataFrame, int]:
    if not 0.0 < valid_fraction < 1.0:
        raise ValueError("Validation fraction must be between 0 and 1.")

    split_time = (
        frame
        .select(pl.col("end_time").quantile(1.0 - valid_fraction).alias("split_time"))
        .item()
    )

    train_df = frame.filter(pl.col("end_time") < split_time)
    valid_df = frame.filter(pl.col("end_time") >= split_time)
    return train_df, valid_df, int(split_time)


def compute_feature_statistics(train_df: pl.DataFrame, features: list[str]) -> dict[str, dict[str, float]]:
    stats = {}

    for feature in features:
        summary = train_df.select(
            [
                pl.col(feature).cast(pl.Float64, strict=False).median().alias("median"),
                pl.col(feature).cast(pl.Float64, strict=False).mean().alias("mean"),
                pl.col(feature).cast(pl.Float64, strict=False).std().alias("std"),
            ]
        ).to_dicts()[0]

        median = summary["median"] if summary["median"] is not None else 0.0
        mean = summary["mean"] if summary["mean"] is not None else median
        std = summary["std"] if summary["std"] not in (None, 0.0) else 1.0

        stats[feature] = {"median": float(median), "mean": float(mean), "std": float(std)}

    return stats


def standardize_frame(
    frame: pl.DataFrame,
    features: list[str],
    feature_stats: dict[str, dict[str, float]],
) -> pl.DataFrame:
    exprs = []
    for feature in features:
        stats = feature_stats[feature]
        exprs.append(
            (
                pl.col(feature)
                .cast(pl.Float64, strict=False)
                .fill_null(stats["median"])
                .sub(stats["mean"])
                .truediv(stats["std"])
            ).alias(feature)
        )
    return frame.with_columns(exprs)


def fit_feature_weights(train_df: pl.DataFrame, features: list[str]) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    feature_stats = compute_feature_statistics(train_df, features)
    standardized = standardize_frame(train_df, features, feature_stats)

    positives = standardized.filter(pl.col("target_failure_15m"))
    negatives = standardized.filter(~pl.col("target_failure_15m"))

    weights = {}
    for feature in features:
        pos_mean = positives.select(pl.col(feature).mean().alias("value")).item()
        neg_mean = negatives.select(pl.col(feature).mean().alias("value")).item()
        pos_mean = float(pos_mean) if pos_mean is not None else 0.0
        neg_mean = float(neg_mean) if neg_mean is not None else 0.0
        weights[feature] = pos_mean - neg_mean

    return feature_stats, weights


def score_frame(
    frame: pl.DataFrame,
    features: list[str],
    feature_stats: dict[str, dict[str, float]],
    weights: dict[str, float],
) -> pl.DataFrame:
    standardized = standardize_frame(frame, features, feature_stats)

    score_expr = pl.lit(0.0)
    for feature in features:
        score_expr = score_expr + pl.col(feature) * pl.lit(weights[feature])

    return standardized.with_columns(score_expr.alias("risk_score"))


def main() -> None:
    clusters = parse_clusters()
    valid_fraction = validation_fraction()
    features = feature_names()

    print(f"Reading forecaster datasets from: {FORECASTER_DIR}")
    print(f"Writing baseline artifacts to: {OUTPUT_DIR}")
    print(f"Clusters: {clusters}")
    print(f"Validation fraction: {valid_fraction}")
    print(f"Features: {features}")

    frame = load_forecaster_data(clusters)
    train_df, valid_df, split_time = split_by_time(frame, valid_fraction)
    feature_stats, weights = fit_feature_weights(train_df, features)
    scored_valid_df = score_frame(valid_df, features, feature_stats, weights)

    print(f"Loaded rows: {frame.height}")
    print(f"Split timestamp: {split_time}")
    print(f"Train rows: {train_df.height}")
    print(f"Validation rows: {valid_df.height}")
    print(f"Validation rows with scores: {scored_valid_df.height}")


if __name__ == "__main__":
    main()
