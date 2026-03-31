import concurrent.futures
import os
import time
from collections import Counter
from pathlib import Path

import polars as pl

from scripts.data_flattener import (
    FLAT_SHARD_DIR,
    OUT_DIR,
    RAW_DIR,
    flatten_workers,
    heartbeat_seconds,
    parse_clusters,
    process_shard,
    raw_shard_paths,
    shard_output_path,
)

DEFAULT_KINDS = ("machines", "events", "usage")


def parse_kinds() -> list[str]:
    raw = os.environ.get("BORG_FLATTEN_KINDS")
    if not raw:
        return list(DEFAULT_KINDS)
    return [kind.strip() for kind in raw.split(",") if kind.strip()]


def build_tasks(clusters: list[str], kinds: list[str]) -> list[tuple[str, str, str]]:
    tasks: list[tuple[str, str, str]] = []
    for cluster_id in clusters:
        print(f"\n[detailed_flatten] queue cluster={cluster_id}")
        for kind in kinds:
            paths = raw_shard_paths(cluster_id, kind)
            queued = 0
            skipped = 0
            for raw_path in paths:
                out_path = shard_output_path(cluster_id, kind, raw_path)
                if out_path.exists():
                    skipped += 1
                    continue
                tasks.append((cluster_id, kind, str(raw_path)))
                queued += 1
            print(
                f"[detailed_flatten] cluster={cluster_id} kind={kind} "
                f"raw_shards={len(paths)} queued={queued} skipped_existing={skipped}"
            )
    return tasks


def audit_kind(cluster_id: str, kind: str) -> str:
    shard_dir = FLAT_SHARD_DIR / kind / cluster_id
    paths = sorted(shard_dir.glob("*.parquet"))
    if not paths:
        return (
            f"[detailed_flatten] audit cluster={cluster_id} kind={kind} "
            "status=missing_shards"
        )

    key_columns = {
        "events": ["time", "collection_id", "instance_index", "machine_id", "type"],
        "usage": ["start_time", "end_time", "collection_id", "instance_index", "machine_id"],
        "machines": ["time", "machine_id", "type", "machine_cpu", "machine_mem"],
    }[kind]

    expressions = [pl.len().alias("rows")]
    for column in key_columns:
        expressions.append(pl.col(column).is_not_null().sum().alias(f"{column}_non_null"))

    totals = None
    for path in paths:
        frame = pl.scan_parquet(str(path)).select(expressions).collect().to_dicts()[0]
        if totals is None:
            totals = {key: int(value) for key, value in frame.items()}
        else:
            for key, value in frame.items():
                totals[key] += int(value)

    if totals is None:
        return (
            f"[detailed_flatten] audit cluster={cluster_id} kind={kind} "
            "status=empty"
        )

    rows = totals.pop("rows")
    non_null_summary = " ".join(
        f"{column}={totals[f'{column}_non_null']}/{rows}"
        for column in key_columns
    )
    return (
        f"[detailed_flatten] audit cluster={cluster_id} kind={kind} "
        f"shards={len(paths)} rows={rows} {non_null_summary}"
    )


if __name__ == "__main__":
    print(f"[detailed_flatten] raw_dir={RAW_DIR}")
    print(f"[detailed_flatten] processed_dir={OUT_DIR}")
    print(f"[detailed_flatten] flat_shard_dir={FLAT_SHARD_DIR}")

    clusters = parse_clusters()
    kinds = parse_kinds()
    workers = flatten_workers()
    tasks = build_tasks(clusters, kinds)

    print(
        f"\n[detailed_flatten] workers={workers} heartbeat_seconds={heartbeat_seconds()} "
        f"pending_tasks={len(tasks)}"
    )

    if not tasks:
        print("[detailed_flatten] no pending work")
    else:
        heartbeat = heartbeat_seconds()
        total = len(tasks)
        completed = 0
        started_at = time.monotonic()
        next_heartbeat = started_at + heartbeat
        completed_by_kind: Counter[str] = Counter()

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            task_iter = iter(tasks)
            future_to_task: dict[concurrent.futures.Future[str], tuple[str, str, str]] = {}

            def submit_next() -> bool:
                try:
                    cluster_id, kind, raw_path = next(task_iter)
                except StopIteration:
                    return False

                raw_name = Path(raw_path).name
                print(
                    f"[detailed_flatten] start cluster={cluster_id} kind={kind} shard={raw_name}",
                    flush=True,
                )
                future = executor.submit(process_shard, cluster_id, kind, raw_path)
                future_to_task[future] = (cluster_id, kind, raw_path)
                return True

            for _ in range(min(workers, total)):
                submit_next()

            while future_to_task:
                done, _ = concurrent.futures.wait(
                    future_to_task,
                    timeout=1,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )

                if not done:
                    now = time.monotonic()
                    if now >= next_heartbeat:
                        elapsed = now - started_at
                        rate = completed / elapsed if elapsed > 0 else 0.0
                        remaining = total - completed
                        eta = remaining / rate if rate > 0 else float("inf")
                        print(
                            "[detailed_flatten] heartbeat "
                            f"completed={completed}/{total} running={len(future_to_task)} "
                            f"rate={rate:.2f}_tasks_per_sec eta_seconds={eta if eta != float('inf') else 'inf'} "
                            f"by_kind={dict(completed_by_kind)}",
                            flush=True,
                        )
                        next_heartbeat = now + heartbeat
                    continue

                for future in done:
                    cluster_id, kind, raw_path = future_to_task.pop(future)
                    completed += 1
                    try:
                        print(f"[detailed_flatten] {future.result()}", flush=True)
                    except Exception as error:
                        print(
                            f"[detailed_flatten] error cluster={cluster_id} kind={kind} "
                            f"shard={Path(raw_path).name} error={error}",
                            flush=True,
                        )
                    completed_by_kind[kind] += 1
                    submit_next()

    for cluster_id in clusters:
        for kind in kinds:
            print(audit_kind(cluster_id, kind), flush=True)
