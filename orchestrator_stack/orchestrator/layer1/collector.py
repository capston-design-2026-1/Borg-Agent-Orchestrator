from __future__ import annotations

import json
from pathlib import Path
from typing import Any


METRIC_KEYS = ("cpu_util", "mem_util", "disk_util", "net_util")


def _metric_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_node(raw: dict[str, Any]) -> dict[str, Any]:
    node = {
        "node_id": str(raw.get("node_id", "unknown-node")),
        "cpu_util": _metric_value(raw.get("cpu_util")),
        "mem_util": _metric_value(raw.get("mem_util")),
        "disk_util": _metric_value(raw.get("disk_util")),
        "net_util": _metric_value(raw.get("net_util")),
        "power_state": str(raw.get("power_state", "on")),
    }
    for key in METRIC_KEYS:
        node[key] = min(1.0, max(0.0, node[key]))
    return node


def _normalize_task(raw: dict[str, Any], fallback_node_id: str) -> dict[str, Any]:
    return {
        "task_id": str(raw.get("task_id", "unknown-task")),
        "node_id": str(raw.get("node_id", fallback_node_id)),
        "urgency": min(1.0, max(0.0, _metric_value(raw.get("urgency", 0.5), 0.5))),
        "queue_priority": int(raw.get("queue_priority", 1)),
        "alive": bool(raw.get("alive", True)),
    }


def prometheus_rows_to_trace(rows: list[dict[str, Any]], interval_seconds: int = 60) -> list[dict[str, Any]]:
    """
    Convert Prometheus/JSON-ish rows into orchestrator trace rows.

    Expected input row shapes (either):
    1) already grouped by timestamp with keys {timestamp, nodes, tasks}
    2) flat point rows with keys {timestamp, node_id, cpu_util, mem_util, disk_util, net_util, ...}
    """
    if not rows:
        return []

    if "nodes" in rows[0]:
        normalized: list[dict[str, Any]] = []
        for row in rows:
            nodes = [_normalize_node(n) for n in row.get("nodes", [])]
            fallback_node = nodes[0]["node_id"] if nodes else "unknown-node"
            tasks = [_normalize_task(t, fallback_node) for t in row.get("tasks", [])]
            normalized.append(
                {
                    "timestamp": int(row.get("timestamp", 0)),
                    "nodes": nodes,
                    "tasks": tasks,
                    "queue_length": int(row.get("queue_length", len(tasks))),
                    "energy_price": _metric_value(row.get("energy_price", 0.1), 0.1),
                    "task_death": bool(row.get("task_death", False)),
                }
            )
        return normalized

    buckets: dict[int, dict[str, Any]] = {}
    for raw in rows:
        ts = int(raw.get("timestamp", 0))
        bucket_ts = ts - (ts % max(1, interval_seconds))
        bucket = buckets.setdefault(
            bucket_ts,
            {
                "timestamp": bucket_ts,
                "nodes": {},
                "tasks": [],
                "queue_length": 0,
                "energy_price": 0.1,
                "task_death": False,
            },
        )
        node_id = str(raw.get("node_id", "unknown-node"))
        bucket["nodes"][node_id] = _normalize_node(raw)
        if "task_id" in raw:
            bucket["tasks"].append(_normalize_task(raw, node_id))

        if "queue_length" in raw:
            bucket["queue_length"] = max(int(raw["queue_length"]), int(bucket["queue_length"]))
        if "energy_price" in raw:
            bucket["energy_price"] = _metric_value(raw["energy_price"], 0.1)
        if raw.get("task_death"):
            bucket["task_death"] = True

    trace: list[dict[str, Any]] = []
    for ts in sorted(buckets.keys()):
        bucket = buckets[ts]
        nodes = list(bucket["nodes"].values())
        tasks = bucket["tasks"]
        trace.append(
            {
                "timestamp": ts,
                "nodes": nodes,
                "tasks": tasks,
                "queue_length": int(bucket["queue_length"] or len(tasks)),
                "energy_price": float(bucket["energy_price"]),
                "task_death": bool(bucket["task_death"]),
            }
        )
    return trace


def validate_prometheus_schema(rows: list[dict[str, Any]]) -> None:
    """Detect metric/key drift in Prometheus JSON before trace conversion."""
    if not rows:
        return

    # Check first row for mandatory fields
    first = rows[0]
    is_grouped = "nodes" in first
    
    if is_grouped:
        if "timestamp" not in first:
            raise ValueError("Schema drift: Grouped row missing 'timestamp' key.")
        nodes = first.get("nodes", [])
        if not isinstance(nodes, list):
            raise ValueError(f"Schema drift: 'nodes' must be a list, got {type(nodes)}")
        if nodes and "node_id" not in nodes[0]:
            raise ValueError("Schema drift: Node entry missing 'node_id' key.")
    else:
        mandatory = ("timestamp", "node_id")
        for key in mandatory:
            if key not in first:
                raise ValueError(f"Schema drift: Flat row missing mandatory key '{key}'.")
        
        # Check for at least one metric key
        if not any(k in first for k in METRIC_KEYS):
            raise ValueError(f"Schema drift: No metric keys {METRIC_KEYS} found in flat row.")


def build_trace_file(metrics_path: str | Path, trace_path: str | Path, interval_seconds: int = 60) -> Path:
    raw = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    validate_prometheus_schema(raw)
    trace = prometheus_rows_to_trace(raw, interval_seconds=interval_seconds)
    out = Path(trace_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return out
