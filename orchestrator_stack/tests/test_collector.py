from orchestrator.layer1.collector import prometheus_rows_to_trace


def test_prometheus_rows_to_trace_groups_by_timestamp():
    rows = [
        {"timestamp": 100, "node_id": "n1", "cpu_util": 0.5, "mem_util": 0.4, "disk_util": 0.3, "net_util": 0.2},
        {"timestamp": 100, "node_id": "n2", "cpu_util": 0.6, "mem_util": 0.5, "disk_util": 0.4, "net_util": 0.3},
        {"timestamp": 160, "node_id": "n1", "cpu_util": 0.4, "mem_util": 0.3, "disk_util": 0.2, "net_util": 0.1},
    ]

    trace = prometheus_rows_to_trace(rows, interval_seconds=60)
    assert len(trace) == 2
    assert len(trace[0]["nodes"]) == 2
