import os
from pathlib import Path

import polars as pl

DEFAULT_RAW_DIR = Path.home() / "Documents" / "borg_data"
DEFAULT_OUT_DIR = Path.home() / "Documents" / "borg_processed"

RAW_DIR = Path(os.environ.get("BORG_RAW_DIR", DEFAULT_RAW_DIR)).expanduser()
OUT_DIR = Path(os.environ.get("BORG_PROCESSED_DIR", DEFAULT_OUT_DIR)).expanduser()
OUT_DIR.mkdir(parents=True, exist_ok=True)


def flatten_cluster(cluster_id):
    """Parses nested JSON files into flat Parquet for a specific cluster."""
    print(f"\n⚡️ Flattening Cluster: {cluster_id}")

    # --- 1. PROCESS MACHINES (The Hardware Grid) ---
    m_path = RAW_DIR / "machines" / f"{cluster_id}_machines.json.gz"
    if m_path.exists():
        # We read as NDJSON because Google's 2019 trace is newline-delimited JSON
        df_m = pl.read_ndjson(m_path)
        # Extract nested 'capacity' fields
        df_m = df_m.with_columns([
            pl.col("capacity").struct.field("cpus").alias("machine_cpu"),
            pl.col("capacity").struct.field("memory").alias("machine_mem")
        ]).drop("capacity")

        df_m.write_parquet(OUT_DIR / f"{cluster_id}_machines.parquet")
        print(f"✅ Machines: {df_m.shape[0]} nodes processed.")

    # --- 2. PROCESS EVENTS (Lifecycle & Failure Labels) ---
    e_path = RAW_DIR / "events" / f"{cluster_id}_events.json.gz"
    if e_path.exists():
        df_e = pl.read_ndjson(e_path)
        # Extract nested 'resource_request'
        df_e = df_e.with_columns([
            pl.col("resource_request").struct.field("cpus").alias("req_cpu"),
            pl.col("resource_request").struct.field("memory").alias("req_mem")
        ]).drop("resource_request")

        df_e.write_parquet(OUT_DIR / f"{cluster_id}_events.parquet")
        print(f"✅ Events: {df_e.shape[0]} events processed.")

    # --- 3. PROCESS USAGE (The Time-Series) ---
    u_path = RAW_DIR / "usage" / f"{cluster_id}_usage.json.gz"
    if u_path.exists():
        # Usage files are huge. Polars read_ndjson is memory-efficient.
        df_u = pl.read_ndjson(u_path)

        # Flatten average and maximum usage dictionaries
        # We drop 'cpu_histogram' to keep your 24GB RAM happy
        df_u = df_u.with_columns([
            pl.col("average_usage").struct.field("cpus").alias("avg_cpu"),
            pl.col("average_usage").struct.field("memory").alias("avg_mem"),
            pl.col("maximum_usage").struct.field("cpus").alias("max_cpu"),
            pl.col("maximum_usage").struct.field("memory").alias("max_mem")
        ]).drop(["average_usage", "maximum_usage", "cpu_histogram"])

        # Add cluster label for multi-cluster training later
        df_u = df_u.with_columns(pl.lit(cluster_id).alias("cluster_id"))

        df_u.write_parquet(OUT_DIR / f"{cluster_id}_usage.parquet")
        print(f"✅ Usage: {df_u.shape[0]} usage samples processed.")


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
