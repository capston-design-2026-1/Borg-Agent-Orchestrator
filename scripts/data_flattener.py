import os
from pathlib import Path

import polars as pl

DEFAULT_RAW_DIR = Path.home() / "Documents" / "borg_data"
DEFAULT_OUT_DIR = Path.home() / "Documents" / "borg_processed"

RAW_DIR = Path(os.environ.get("BORG_RAW_DIR", DEFAULT_RAW_DIR)).expanduser()
OUT_DIR = Path(os.environ.get("BORG_PROCESSED_DIR", DEFAULT_OUT_DIR)).expanduser()
OUT_DIR.mkdir(parents=True, exist_ok=True)


def flatten_cluster(cluster_id):
    print(f"\n⚡️ Flattening Cluster: {cluster_id}")

    # --- Helper to safely get columns ---
    def safe_extract(df, root_col, field_name, new_name):
        if root_col in df.columns:
            # We cast to Float64 immediately to prevent the Int/Float mismatch
            return pl.col(root_col).struct.field(field_name).cast(pl.Float64).alias(new_name)
        return pl.lit(None).cast(pl.Float64).alias(new_name)

    # --- 1. MACHINES ---
    m_path = RAW_DIR / "machines" / f"{cluster_id}_machines.json.gz"
    if m_path.exists():
        df_m = pl.read_ndjson(m_path, infer_schema_length=10000)
        if "capacity" in df_m.columns:
            df_m = df_m.with_columns([
                safe_extract(df_m, "capacity", "cpus", "machine_cpu"),
                safe_extract(df_m, "capacity", "memory", "machine_mem")
            ]).drop("capacity")
            df_m = df_m.filter(pl.col("machine_cpu").is_not_null())
            df_m.write_parquet(OUT_DIR / f"{cluster_id}_machines.parquet")
            print(f"✅ Machines processed.")

    # --- 2. EVENTS ---
    e_path = RAW_DIR / "events" / f"{cluster_id}_events.json.gz"
    if e_path.exists():
        # High infer_schema_length is key for the 2019 trace
        df_e = pl.read_ndjson(e_path, infer_schema_length=10000)
        df_e = df_e.with_columns([
            safe_extract(df_e, "resource_request", "cpus", "req_cpu"),
            safe_extract(df_e, "resource_request", "memory", "req_mem")
        ])
        # Drop only if it exists
        cols_to_drop = [c for c in ["resource_request", "constraint"] if c in df_e.columns]
        df_e = df_e.drop(cols_to_drop)
        df_e.write_parquet(OUT_DIR / f"{cluster_id}_events.parquet")
        print(f"✅ Events processed.")

    # --- 3. USAGE ---
    u_path = RAW_DIR / "usage" / f"{cluster_id}_usage.json.gz"
    if u_path.exists():
        df_u = pl.read_ndjson(u_path, infer_schema_length=10000)

        df_u = df_u.with_columns([
            safe_extract(df_u, "average_usage", "cpus", "avg_cpu"),
            safe_extract(df_u, "average_usage", "memory", "avg_mem"),
            safe_extract(df_u, "maximum_usage", "cpus", "max_cpu"),
            safe_extract(df_u, "maximum_usage", "memory", "max_mem")
        ])

        # Drop columns safely
        to_drop = ["average_usage", "maximum_usage", "cpu_histogram", "cycles_per_instruction",
                   "memory_accesses_per_1000_instructions"]
        existing_drop = [c for c in to_drop if c in df_u.columns]
        df_u = df_u.drop(existing_drop).with_columns(pl.lit(cluster_id).alias("cluster_id"))

        df_u.write_parquet(OUT_DIR / f"{cluster_id}_usage.parquet")
        print(f"✅ Usage processed.")


if __name__ == "__main__":
    print(f"Reading raw Borg data from: {RAW_DIR}")
    print(f"Writing flattened data to: {OUT_DIR}")

    clusters = ["a", "b", "c", "d", "e", "f", "g", "h"]

    for c in clusters:
        try:
            flatten_cluster(c)
        except Exception as e:
            print(f"❌ Error in cluster {c}: {e}")

    print("\n🚀 All done! Raw data can stay outside the repository.")
