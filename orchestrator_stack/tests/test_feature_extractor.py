from orchestrator.layer2.feature_extractor import trace_rows_to_training_matrices


def test_trace_rows_to_training_matrices_shapes():
    rows = [
        {
            "timestamp": 100,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.8, "mem_util": 0.9, "disk_util": 0.2, "net_util": 0.1},
                {"node_id": "n2", "cpu_util": 0.2, "mem_util": 0.3, "disk_util": 0.2, "net_util": 0.1},
            ],
            "tasks": [{"task_id": "t1", "node_id": "n1"}],
            "queue_length": 5,
            "energy_price": 0.1,
            "task_death": False,
        },
        {
            "timestamp": 160,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.7, "mem_util": 0.7, "disk_util": 0.2, "net_util": 0.1},
                {"node_id": "n2", "cpu_util": 0.3, "mem_util": 0.4, "disk_util": 0.2, "net_util": 0.1},
            ],
            "tasks": [{"task_id": "t2", "node_id": "n2"}],
            "queue_length": 4,
            "energy_price": 0.11,
            "task_death": False,
        },
    ]

    matrices = trace_rows_to_training_matrices(rows)
    assert matrices.x.shape[1] == 6
    assert matrices.y_risk.shape[0] == matrices.x.shape[0]
    assert matrices.y_demand.shape[0] == matrices.x.shape[0]
