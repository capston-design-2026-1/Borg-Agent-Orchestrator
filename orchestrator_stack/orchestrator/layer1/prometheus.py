from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


NODE_LABEL_KEYS = ("node_id", "node", "instance", "host", "hostname", "machine")


def _node_id_from_metric(metric: dict[str, Any]) -> str:
    for key in NODE_LABEL_KEYS:
        value = metric.get(key)
        if value:
            return str(value)
    return "unknown-node"


def _query_range_url(base_url: str, *, query: str, start: str, end: str, step: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1/query_range?{urlencode({'query': query, 'start': start, 'end': end, 'step': step})}"


def _fetch_query_range(base_url: str, *, query: str, start: str, end: str, step: str) -> list[dict[str, Any]]:
    url = _query_range_url(base_url, query=query, start=start, end=end, step=step)
    with urlopen(url, timeout=30) as response:  # noqa: S310 - explicit user-provided Prometheus endpoint.
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") != "success":
        raise ValueError(f"Prometheus query_range failed for query {query!r}: {payload}")
    result = payload.get("data", {}).get("result", [])
    if not isinstance(result, list):
        raise ValueError(f"Prometheus query_range returned non-list result for query {query!r}.")
    return result


def query_prometheus_metric_rows(
    *,
    base_url: str,
    query_map: dict[str, str],
    start: str,
    end: str,
    step: str,
) -> list[dict[str, Any]]:
    rows_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for field_name, query in query_map.items():
        series_list = _fetch_query_range(base_url, query=query, start=start, end=end, step=step)
        for series in series_list:
            metric = series.get("metric", {})
            node_id = _node_id_from_metric(metric if isinstance(metric, dict) else {})
            values = series.get("values", [])
            if not isinstance(values, list):
                continue
            for point in values:
                if not isinstance(point, list | tuple) or len(point) != 2:
                    continue
                timestamp = int(float(point[0]))
                row = rows_by_key.setdefault((timestamp, node_id), {"timestamp": timestamp, "node_id": node_id})
                row[field_name] = float(point[1])

    return [rows_by_key[key] for key in sorted(rows_by_key)]


def export_prometheus_metric_rows(
    *,
    base_url: str,
    query_map: dict[str, str],
    start: str,
    end: str,
    step: str,
    out_path: str | Path,
) -> Path:
    rows = query_prometheus_metric_rows(base_url=base_url, query_map=query_map, start=start, end=end, step=step)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return out
