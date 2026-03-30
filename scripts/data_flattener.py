import os
from pathlib import Path

import polars as pl

DEFAULT_RAW_DIR = Path.home() / "Documents" / "borg_data"
DEFAULT_OUT_DIR = Path.home() / "Documents" / "borg_processed"
DEFAULT_CLUSTERS = ("b", "c", "d", "e", "f", "g")

RAW_DIR = Path(os.environ.get("BORG_RAW_DIR", DEFAULT_RAW_DIR)).expanduser()
OUT_DIR = Path(os.environ.get("BORG_PROCESSED_DIR", DEFAULT_OUT_DIR)).expanduser()
OUT_DIR.mkdir(parents=True, exist_ok=True)
FLAT_SHARD_DIR = OUT_DIR / "flat_shards"
FLAT_SHARD_DIR.mkdir(parents=True, exist_ok=True)


def parse_clusters() -> list[str]:
    raw = os.environ.get("BORG_CLUSTERS")
    if not raw:
        return list(DEFAULT_CLUSTERS)
    return [cluster.strip() for cluster in raw.split(",") if cluster.strip()]


def raw_shard_paths(cluster_id: str, kind: str) -> list[Path]:
    kind_dir = RAW_DIR / kind
    legacy_name = {
        "machines": f"{cluster_id}_machines.json.gz",
        "events": f"{cluster_id}_events.json.gz",
        "usage": f"{cluster_id}_usage.json.gz",
    }[kind]
    shard_glob = {
        "machines": f"{cluster_id}_machines-*.json.gz",
        "events": f"{cluster_id}_events-*.json.gz",
        "usage": f"{cluster_id}_usage-*.json.gz",
    }[kind]

    paths = []
    legacy_path = kind_dir / legacy_name
    if legacy_path.exists():
        paths.append(legacy_path)
    paths.extend(sorted(kind_dir.glob(shard_glob)))
    return paths


def shard_output_path(cluster_id: str, kind: str, raw_path: Path) -> Path:
    cluster_dir = FLAT_SHARD_DIR / kind / cluster_id
    cluster_dir.mkdir(parents=True, exist_ok=True)
    raw_name = raw_path.name.removesuffix(".json.gz")
    return cluster_dir / f"{raw_name}.parquet"


def read_ndjson_permissive(path: Path, kind: str) -> pl.DataFrame:
    schema_overrides: dict[str, pl.DataType] = {}

    if kind == "usage":
        schema_overrides = {
            "assigned_memory": pl.Float64,
            "page_cache_memory": pl.Float64,
            "sample_rate": pl.Float64,
            "memory_accesses_per_instruction": pl.Float64,
            "start_time": pl.Int64,
            "end_time": pl.Int64,
            "collection_id": pl.Int64,
            "instance_index": pl.Int64,
            "machine_id": pl.Int64,
            "alloc_collection_id": pl.Int64,
            "alloc_instance_index": pl.Int64,
        }
    elif kind == "events":
        schema_overrides = {
            "time": pl.Int64,
            "collection_id": pl.Int64,
            "instance_index": pl.Int64,
            "machine_id": pl.Int64,
            "alloc_collection_id": pl.Int64,
            "alloc_instance_index": pl.Int64,
            "type": pl.Int64,
            "priority": pl.Int64,
            "scheduling_class": pl.Int64,
            "resource_request": pl.Object,
            "constraint": pl.Object,
        }
    elif kind == "machines":
        schema_overrides = {
            "time": pl.Int64,
            "machine_id": pl.Int64,
            "type": pl.Int64,
            "capacity": pl.Object,
        }

    return pl.read_ndjson(
        path,
        infer_schema_length=10000,
        schema_overrides=schema_overrides,
        ignore_errors=True,
        low_memory=True,
    )


def flatten_cluster(cluster_id):
    print(f"\n⚡️ Flattening Cluster: {cluster_id}")

    # --- Helper to safely get columns ---
    def safe_extract(df, root_col, field_name, new_name):
        if root_col in df.columns:
            # We cast to Float64 immediately to prevent the Int/Float mismatch
            return pl.col(root_col).struct.field(field_name).cast(pl.Float64).alias(new_name)
        return pl.lit(None).cast(pl.Float64).alias(new_name)

    machine_paths = raw_shard_paths(cluster_id, "machines")
    if machine_paths:
        for m_path in machine_paths:
            out_path = shard_output_path(cluster_id, "machines", m_path)
            if out_path.exists():
                print(f"Skipping existing machine shard output {out_path.name}")
                continue
            print(f"Processing machine shard {m_path.name}")
            df_m = read_ndjson_permissive(m_path, "machines")
            if "capacity" not in df_m.columns:
                continue

            df_m = df_m.with_columns([
                safe_extract(df_m, "capacity", "cpus", "machine_cpu"),
                safe_extract(df_m, "capacity", "memory", "machine_mem")
            ]).drop("capacity")
            df_m = df_m.filter(pl.col("machine_cpu").is_not_null())
            df_m.write_parquet(out_path)
        print(f"✅ Machines processed: {len(machine_paths)} shard(s).")

    event_paths = raw_shard_paths(cluster_id, "events")
    if event_paths:
        for e_path in event_paths:
            out_path = shard_output_path(cluster_id, "events", e_path)
            if out_path.exists():
                print(f"Skipping existing event shard output {out_path.name}")
                continue
            print(f"Processing event shard {e_path.name}")
            df_e = read_ndjson_permissive(e_path, "events")
            df_e = df_e.with_columns([
                safe_extract(df_e, "resource_request", "cpus", "req_cpu"),
                safe_extract(df_e, "resource_request", "memory", "req_mem")
            ])
            cols_to_drop = [c for c in ["resource_request", "constraint"] if c in df_e.columns]
            df_e = df_e.drop(cols_to_drop)
            df_e.write_parquet(out_path)
        print(f"✅ Events processed: {len(event_paths)} shard(s).")

    usage_paths = raw_shard_paths(cluster_id, "usage")
    if usage_paths:
        for u_path in usage_paths:
            out_path = shard_output_path(cluster_id, "usage", u_path)
            if out_path.exists():
                print(f"Skipping existing usage shard output {out_path.name}")
                continue
            print(f"Processing usage shard {u_path.name}")
            df_u = read_ndjson_permissive(u_path, "usage")

            df_u = df_u.with_columns([
                safe_extract(df_u, "average_usage", "cpus", "avg_cpu"),
                safe_extract(df_u, "average_usage", "memory", "avg_mem"),
                safe_extract(df_u, "maximum_usage", "cpus", "max_cpu"),
                safe_extract(df_u, "maximum_usage", "memory", "max_mem")
            ])

            to_drop = ["average_usage", "maximum_usage", "cpu_histogram", "cycles_per_instruction",
                       "memory_accesses_per_1000_instructions"]
            existing_drop = [c for c in to_drop if c in df_u.columns]
            df_u = df_u.drop(existing_drop).with_columns(pl.lit(cluster_id).alias("cluster_id"))

            df_u.write_parquet(out_path)
        print(f"✅ Usage processed: {len(usage_paths)} shard(s).")


if __name__ == "__main__":
    print(f"Reading raw Borg data from: {RAW_DIR}")
    print(f"Writing flattened data to: {OUT_DIR}")
    print(f"Writing flattened shard parquet to: {FLAT_SHARD_DIR}")

    clusters = parse_clusters()

    for c in clusters:
        try:
            flatten_cluster(c)
        except Exception as e:
            print(f"❌ Error in cluster {c}: {e}")

    print("\n🚀 All done! Raw data can stay outside the repository.")
