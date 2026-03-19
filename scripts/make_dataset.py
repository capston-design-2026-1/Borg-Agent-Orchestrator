import os
from pathlib import Path

import polars as pl

DEFAULT_PROCESSED_DIR = Path.home() / "Documents" / "borg_processed"
DEFAULT_DATASET_DIR = DEFAULT_PROCESSED_DIR / "datasets"
DEFAULT_CLUSTERS = ("a", "b", "c", "d", "e", "f", "g", "h")

PROCESSED_DIR = Path(os.environ.get("BORG_PROCESSED_DIR", DEFAULT_PROCESSED_DIR)).expanduser()
DATASET_DIR = Path(os.environ.get("BORG_DATASET_DIR", DEFAULT_DATASET_DIR)).expanduser()
DATASET_DIR.mkdir(parents=True, exist_ok=True)


def parse_clusters() -> list[str]:
    raw = os.environ.get("BORG_CLUSTERS")
    if not raw:
        return list(DEFAULT_CLUSTERS)
    return [cluster.strip() for cluster in raw.split(",") if cluster.strip()]


def int_col(name: str) -> pl.Expr:
    return pl.col(name).cast(pl.Int64, strict=False)


def float_col(name: str) -> pl.Expr:
    return pl.col(name).cast(pl.Float64, strict=False)


def str_col(name: str) -> pl.Expr:
    return pl.col(name).cast(pl.Utf8, strict=False)


def cluster_file(cluster_id: str, suffix: str) -> Path:
    return PROCESSED_DIR / f"{cluster_id}_{suffix}.parquet"


def dataset_file(cluster_id: str) -> Path:
    return DATASET_DIR / f"{cluster_id}_dataset.parquet"


def load_event_features(cluster_id: str) -> pl.LazyFrame:
    events = pl.scan_parquet(cluster_file(cluster_id, "events"))

    return (
        events
        .select(
            [
                int_col("time").alias("event_time"),
                int_col("collection_id").alias("collection_id"),
                int_col("instance_index").alias("instance_index"),
                int_col("machine_id").alias("event_machine_id"),
                int_col("alloc_collection_id").alias("alloc_collection_id"),
                int_col("alloc_instance_index").alias("alloc_instance_index"),
                int_col("type").alias("event_type"),
                int_col("scheduling_class").alias("scheduling_class"),
                int_col("priority").alias("priority"),
                str_col("missing_type").alias("missing_type"),
                float_col("req_cpu").alias("req_cpu"),
                float_col("req_mem").alias("req_mem"),
            ]
        )
        .filter(pl.col("collection_id").is_not_null() & pl.col("instance_index").is_not_null())
        .sort(["collection_id", "instance_index", "event_time"])
        .group_by(["collection_id", "instance_index"])
        .agg(
            [
                pl.col("event_time").min().alias("first_event_time"),
                pl.col("event_time").max().alias("last_event_time"),
                pl.len().alias("event_count"),
                pl.col("event_type").last().alias("final_event_type"),
                pl.col("scheduling_class").drop_nulls().last().alias("scheduling_class"),
                pl.col("priority").drop_nulls().last().alias("priority"),
                pl.col("req_cpu").max().alias("req_cpu"),
                pl.col("req_mem").max().alias("req_mem"),
                pl.col("event_machine_id").drop_nulls().last().alias("last_event_machine_id"),
                pl.col("alloc_collection_id").drop_nulls().last().alias("alloc_collection_id"),
                pl.col("alloc_instance_index").drop_nulls().last().alias("alloc_instance_index"),
                pl.col("missing_type").drop_nulls().last().alias("missing_type"),
            ]
        )
    )


def load_machine_features(cluster_id: str) -> pl.LazyFrame:
    machines = pl.scan_parquet(cluster_file(cluster_id, "machines"))

    return (
        machines
        .select(
            [
                int_col("time").alias("machine_event_time"),
                int_col("machine_id").alias("machine_id"),
                float_col("machine_cpu").alias("machine_cpu"),
                float_col("machine_mem").alias("machine_mem"),
                int_col("type").alias("machine_event_type"),
                str_col("switch_id").alias("switch_id"),
                str_col("platform_id").alias("platform_id"),
            ]
        )
        .filter(pl.col("machine_id").is_not_null())
        .sort(["machine_id", "machine_event_time"])
        .group_by("machine_id")
        .agg(
            [
                pl.col("machine_event_time").max().alias("last_machine_event_time"),
                pl.col("machine_cpu").drop_nulls().last().alias("machine_cpu"),
                pl.col("machine_mem").drop_nulls().last().alias("machine_mem"),
                pl.col("machine_event_type").drop_nulls().last().alias("machine_event_type"),
                pl.col("switch_id").drop_nulls().last().alias("switch_id"),
                pl.col("platform_id").drop_nulls().last().alias("platform_id"),
            ]
        )
    )


def main() -> None:
    print(f"Reading flattened parquet files from: {PROCESSED_DIR}")
    print(f"Writing joined datasets to: {DATASET_DIR}")
    print(f"Clusters: {parse_clusters()}")


if __name__ == "__main__":
    main()
