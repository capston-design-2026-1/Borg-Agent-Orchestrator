from orchestrator.layer2.feature_extractor import FEATURE_COUNT, node_feature_vector, trace_rows_to_training_matrices
from orchestrator.types import NodeState, Observation, TaskState


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
    assert matrices.x.shape[1] == FEATURE_COUNT
    assert matrices.y_risk.shape[0] == matrices.x.shape[0]
    assert matrices.y_demand.shape[0] == matrices.x.shape[0]
    assert matrices.y_risk.tolist() == [1, 0, 0, 0]
    assert [round(value, 2) for value in matrices.y_demand.tolist()] == [0.42, 0.32, 0.42, 0.32]


def test_node_feature_vector_includes_task_pressure_and_power_state():
    obs = Observation(
        timestamp=1,
        nodes=[
            NodeState("n1", cpu_util=0.8, mem_util=0.5, disk_util=0.2, net_util=0.1, power_state="on"),
            NodeState("n2", cpu_util=0.2, mem_util=0.3, disk_util=0.4, net_util=0.2, power_state="sleep"),
        ],
        tasks=[
            TaskState("t1", "n1", urgency=0.5, queue_priority=2, alive=True),
            TaskState("t2", "n1", urgency=0.3, queue_priority=1, alive=True),
            TaskState("t3", "queue", urgency=0.9, queue_priority=3, alive=False),
        ],
        p_fail_scores={"n1": 0.9},
        demand_projection={"n1": 0.7},
        queue_length=4,
        energy_price=0.13,
    )

    n1 = node_feature_vector(obs, "n1")
    n2 = node_feature_vector(obs, "n2")

    assert len(n1) == FEATURE_COUNT
    assert n1[4] > n2[4]
    assert n1[5] > 0.0
    assert n1[7] == 1.0
    assert n2[7] == 0.0


def test_trace_rows_to_training_matrices_uses_future_state_targets():
    rows = [
        {
            "timestamp": 1,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.4, "mem_util": 0.5, "disk_util": 0.2, "net_util": 0.1},
            ],
            "tasks": [{"task_id": "t1", "node_id": "n1", "alive": True}],
            "queue_length": 2,
            "energy_price": 0.1,
        },
        {
            "timestamp": 2,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.95, "mem_util": 0.92, "disk_util": 0.2, "net_util": 0.1},
            ],
            "tasks": [{"task_id": "t1", "node_id": "n1", "alive": False}],
            "queue_length": 4,
            "energy_price": 0.11,
            "p_fail_scores": {"n1": 0.96},
            "demand_projection": {"n1": 0.83},
        },
    ]

    matrices = trace_rows_to_training_matrices(rows)

    assert matrices.y_risk.tolist() == [1, 1]
    assert [round(value, 2) for value in matrices.y_demand.tolist()] == [0.83, 0.83]


def test_trace_rows_to_training_matrices_normalizes_aiopslab_state_shapes():
    rows = [
        {
            "state": {
                "ts": 100,
                "machines": {
                    "n1": {"cpu": 0.95, "memory_usage": 0.92, "disk": 0.2, "network": 0.1, "state": "on"},
                    "n2": {"cpu": 0.25, "memory_usage": 0.35, "disk": 0.1, "network": 0.2, "state": "sleep"},
                },
                "pods": {
                    "t1": {"assigned_node": "n1", "priority_score": 0.7, "priority": 2, "running": "true"},
                    "t2": {"queued": True, "priority_score": 0.4, "priority": 1},
                },
                "metrics": {"queue_length": 4, "energy_price": 0.15},
                "risk_scores": {"n1": 0.91},
                "demand_scores": {"n1": 0.72, "n2": 0.21},
            }
        },
        {
            "state": {
                "ts": 160,
                "machines": {
                    "n1": {"cpu": 0.62, "memory_usage": 0.58, "disk": 0.2, "network": 0.1, "state": "on"},
                    "n2": {"cpu": 0.31, "memory_usage": 0.4, "disk": 0.1, "network": 0.2, "state": "on"},
                },
                "pods": {
                    "t1": {"assigned_node": "n1", "priority_score": 0.7, "priority": 2, "running": True}
                },
                "metrics": {"queue_length": 2, "energy_price": 0.14},
            }
        },
    ]

    matrices = trace_rows_to_training_matrices(rows)

    assert matrices.x.shape == (4, FEATURE_COUNT)
    assert matrices.y_risk.tolist() == [1, 0, 0, 0]
    assert matrices.y_demand[0] > matrices.y_demand[1]


def test_trace_rows_to_training_matrices_accepts_flat_metric_rows():
    rows = [
        {
            "timestamp": 100,
            "node_id": "n1",
            "cpu_util": 0.8,
            "mem_util": 0.7,
            "disk_util": 0.2,
            "net_util": 0.1,
            "task_id": "t1",
            "queue_length": 5,
            "energy_price": 0.1,
        },
        {
            "timestamp": 100,
            "node_id": "n2",
            "cpu_util": 0.2,
            "mem_util": 0.3,
            "disk_util": 0.2,
            "net_util": 0.1,
            "task_id": "t2",
            "queue_length": 5,
            "energy_price": 0.1,
        },
        {
            "timestamp": 160,
            "node_id": "n1",
            "cpu_util": 0.95,
            "mem_util": 0.96,
            "disk_util": 0.2,
            "net_util": 0.1,
            "task_id": "t3",
            "queue_length": 4,
            "energy_price": 0.11,
        },
        {
            "timestamp": 160,
            "node_id": "n2",
            "cpu_util": 0.4,
            "mem_util": 0.5,
            "disk_util": 0.2,
            "net_util": 0.1,
            "task_id": "t4",
            "queue_length": 4,
            "energy_price": 0.11,
        },
    ]

    matrices = trace_rows_to_training_matrices(rows)

    assert matrices.x.shape == (4, FEATURE_COUNT)
    assert matrices.y_risk.tolist() == [1, 0, 1, 0]
