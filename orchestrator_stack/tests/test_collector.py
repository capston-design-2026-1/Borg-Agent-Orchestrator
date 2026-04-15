import json

import pytest

from orchestrator.layer1.collector import build_trace_file, prometheus_rows_to_trace, validate_prometheus_schema


def test_validate_prometheus_schema_raises_on_drift():
    # Missing node_id in flat row
    bad_rows = [{"timestamp": 100, "cpu_util": 0.5}]
    with pytest.raises(ValueError, match="Schema drift"):
        validate_prometheus_schema(bad_rows)


def test_prometheus_rows_to_trace_groups_by_timestamp():
    rows = [
        {"timestamp": 100, "node_id": "n1", "cpu_util": 0.5, "mem_util": 0.4, "disk_util": 0.3, "net_util": 0.2},
        {"timestamp": 100, "node_id": "n2", "cpu_util": 0.6, "mem_util": 0.5, "disk_util": 0.4, "net_util": 0.3},
        {"timestamp": 160, "node_id": "n1", "cpu_util": 0.4, "mem_util": 0.3, "disk_util": 0.2, "net_util": 0.1},
    ]

    trace = prometheus_rows_to_trace(rows, interval_seconds=60)
    assert len(trace) == 2
    assert len(trace[0]["nodes"]) == 2


def test_validate_prometheus_schema_detects_late_row_shape_drift():
    bad_rows = [
        {"timestamp": 100, "node_id": "n1", "cpu_util": 0.5},
        {"timestamp": 160, "nodes": [{"node_id": "n1", "cpu_util": 0.4, "mem_util": 0.3}]},
    ]
    with pytest.raises(ValueError, match="mixed row shapes"):
        validate_prometheus_schema(bad_rows)


def test_build_trace_file_rejects_non_list_payload(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    trace_path = tmp_path / "trace.json"
    metrics_path.write_text(json.dumps({"timestamp": 100}), encoding="utf-8")

    with pytest.raises(ValueError, match="must be a list"):
        build_trace_file(metrics_path, trace_path)


def test_validate_prometheus_schema_rejects_non_list_top_level():
    with pytest.raises(ValueError, match="expected top-level list"):
        validate_prometheus_schema({"timestamp": 100})  # type: ignore[arg-type]


def test_validate_prometheus_schema_rejects_negative_queue_length():
    bad_rows = [{"timestamp": 100, "node_id": "n1", "cpu_util": 0.5, "queue_length": -1}]
    with pytest.raises(ValueError, match="must be non-negative"):
        validate_prometheus_schema(bad_rows)


def test_prometheus_rows_to_trace_parses_bool_like_task_fields():
    rows = [
        {
            "timestamp": 100,
            "node_id": "n1",
            "cpu_util": 0.5,
            "mem_util": 0.4,
            "task_id": "t1",
            "alive": "false",
            "task_death": "false",
        }
    ]

    trace = prometheus_rows_to_trace(rows)
    assert trace[0]["tasks"][0]["alive"] is False
    assert trace[0]["task_death"] is False


def test_prometheus_rows_to_trace_rejects_non_positive_interval():
    rows = [{"timestamp": 100, "node_id": "n1", "cpu_util": 0.5}]
    with pytest.raises(ValueError, match="interval_seconds must be positive"):
        prometheus_rows_to_trace(rows, interval_seconds=0)
