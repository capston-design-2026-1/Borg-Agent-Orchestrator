import os
import sys
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.schema.common import canonicalize_forecaster_frame
from src.schema.common import common_forecaster_file
from src.schema.common import common_forecaster_output_dir

DEFAULT_FORECASTER_DIR = Path.home() / "Documents" / "borg_processed" / "datasets" / "forecaster"
DEFAULT_OUTPUT_BASE_DIR = DEFAULT_FORECASTER_DIR
DEFAULT_CLUSTERS = ("b", "c", "d", "e", "f", "g")
DEFAULT_SOURCE_PLATFORM = "borg"

FORECASTER_DIR = Path(os.environ.get("BORG_FORECASTER_DIR", DEFAULT_FORECASTER_DIR)).expanduser()
OUTPUT_BASE_DIR = Path(os.environ.get("BORG_COMMON_DATASET_DIR", DEFAULT_OUTPUT_BASE_DIR)).expanduser()


def parse_clusters() -> list[str]:
    raw = os.environ.get("BORG_CLUSTERS")
    if not raw:
        return list(DEFAULT_CLUSTERS)
    return [cluster.strip() for cluster in raw.split(",") if cluster.strip()]


def source_platform_name() -> str:
    return os.environ.get("BORG_SOURCE_PLATFORM", DEFAULT_SOURCE_PLATFORM).strip() or DEFAULT_SOURCE_PLATFORM


def forecaster_file(cluster_id: str) -> Path:
    return FORECASTER_DIR / f"{cluster_id}_forecaster.parquet"


def export_cluster(cluster_id: str, source_platform: str) -> Path:
    input_path = forecaster_file(cluster_id)
    if not input_path.exists():
        raise FileNotFoundError(f"Missing forecaster dataset for cluster {cluster_id}: {input_path}")

    frame = pl.read_parquet(input_path)
    canonical = canonicalize_forecaster_frame(frame, source_platform=source_platform)

    output_path = common_forecaster_file(OUTPUT_BASE_DIR, cluster_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_parquet(output_path)

    positives = canonical.filter(pl.col("target_failure_within_horizon")).height
    print(
        f"✅ {cluster_id}: wrote {canonical.height} rows to {output_path} "
        f"(positive labels: {positives})"
    )
    return output_path


def main() -> None:
    clusters = parse_clusters()
    source_platform = source_platform_name()

    print(f"Reading source forecaster datasets from: {FORECASTER_DIR}")
    print(f"Writing canonical forecaster datasets to: {common_forecaster_output_dir(OUTPUT_BASE_DIR)}")
    print(f"Source platform label: {source_platform}")
    print(f"Clusters: {clusters}")

    for cluster_id in clusters:
        path = forecaster_file(cluster_id)
        if not path.exists():
            print(f"Skipping {cluster_id}: missing {path.name}")
            continue
        export_cluster(cluster_id, source_platform)


if __name__ == "__main__":
    main()
