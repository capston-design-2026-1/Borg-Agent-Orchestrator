import json

from orchestrator.layer2.simulator import AIOpsLabBackend, TraceDrivenTwinBackend, state_to_observation
from orchestrator.types import ActionKind, AgentAction


def test_state_to_observation_normalizes_nested_aiopslab_payload():
    payload = {
        "state": {
            "hosts": [
                {"id": "node-a", "cpu": "1.2", "mem": "0.7", "disk": 0.3, "network": 0.4, "state": "sleep"}
            ],
            "pods": [
                {"id": "task-a", "assigned_node": "missing-node", "priority_score": "0.9", "priority": "4", "alive": "true"}
            ],
            "metrics": {"pending_queue_length": "3", "energy_price": "0.21"},
            "risk_scores": {"node-a": "0.95"},
            "demand_scores": {"node-a": "0.66"},
            "ts": "101",
        }
    }

    obs = state_to_observation(json.dumps(payload))
    assert obs.timestamp == 101
    assert obs.nodes[0].node_id == "node-a"
    assert obs.nodes[0].cpu_util == 1.0
    assert obs.nodes[0].power_state == "sleep"
    assert obs.tasks[0].node_id == "queue"
    assert obs.queue_length == 3
    assert obs.p_fail_scores["node-a"] == 0.95
    assert obs.demand_projection["node-a"] == 0.66


def test_state_to_observation_reads_nested_resource_metrics():
    payload = {
        "current_state": {
            "timestamp": 17,
            "machines": [
                {
                    "id": "node-a",
                    "resources": {
                        "cpu": {"percent": 72},
                        "memory": {"utilization": "0.81"},
                        "disk": {"used_ratio": "0.34"},
                        "network": {"usage": 18},
                    },
                    "power": "sleep",
                    "risk_score": "0.91",
                    "demand_score": "0.63",
                }
            ],
            "pods": [
                {"pod_id": "pod-1", "placement": {"node": "node-a"}, "status": {"healthy": "false"}},
                {"pod_id": "pod-2", "queued": True},
            ],
            "metrics": {"pending_queue_length": "3", "energyPrice": "0.14"},
        }
    }

    obs = state_to_observation(json.dumps(payload))

    assert obs.nodes[0].cpu_util == 0.72
    assert obs.nodes[0].mem_util == 0.81
    assert obs.nodes[0].disk_util == 0.34
    assert obs.nodes[0].net_util == 0.18
    assert obs.nodes[0].power_state == "sleep"
    assert obs.p_fail_scores["node-a"] == 0.91
    assert obs.demand_projection["node-a"] == 0.63
    assert obs.tasks[1].node_id == "queue"
    assert obs.tasks[1].alive is False


def test_trace_driven_backend_applies_migration_before_advancing_trace():
    rows = [
        {
            "timestamp": 100,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.9, "mem_util": 0.85, "disk_util": 0.2, "net_util": 0.2},
                {"node_id": "n2", "cpu_util": 0.3, "mem_util": 0.25, "disk_util": 0.2, "net_util": 0.2},
            ],
            "tasks": [
                {"task_id": "t1", "node_id": "n1", "urgency": 0.8, "queue_priority": 2, "alive": True},
            ],
            "queue_length": 2,
            "energy_price": 0.10,
            "p_fail_scores": {"n1": 0.88, "n2": 0.2},
            "demand_projection": {"n1": 0.8, "n2": 0.3},
        },
        {
            "timestamp": 160,
            "nodes": [
                {"node_id": "n1", "cpu_util": 0.86, "mem_util": 0.8, "disk_util": 0.2, "net_util": 0.2},
                {"node_id": "n2", "cpu_util": 0.35, "mem_util": 0.28, "disk_util": 0.2, "net_util": 0.2},
            ],
            "tasks": [
                {"task_id": "t1", "node_id": "n1", "urgency": 0.8, "queue_priority": 2, "alive": True},
            ],
            "queue_length": 2,
            "energy_price": 0.11,
            "p_fail_scores": {"n1": 0.8, "n2": 0.25},
            "demand_projection": {"n1": 0.78, "n2": 0.34},
        },
    ]

    backend = TraceDrivenTwinBackend(rows)
    backend.reset()
    result = backend.step(AgentAction(agent_name="AgentA", kind=ActionKind.MIGRATE, target="n2"))

    task_map = {task.task_id: task.node_id for task in result.next_observation.tasks}
    assert task_map["t1"] == "n2"
    cpu_by_node = {node.node_id: node.cpu_util for node in result.next_observation.nodes}
    assert cpu_by_node["n1"] < 0.86
    assert cpu_by_node["n2"] > 0.35
    assert result.reward_by_agent["AgentA"] > 10.0


def test_aiopslab_backend_prefers_initialized_session_and_unwraps_step_tuple():
    class FakeSession:
        def __init__(self) -> None:
            self.step_calls = []

        def reset(self):
            return {
                "state": {
                    "timestamp": 5,
                    "machines": [{"id": "node-a", "cpu": 0.82, "memory_usage": 0.76}],
                    "pods": [{"id": "task-a", "assigned_node": "node-a", "running": True}],
                }
            }

        def step(self, command):
            self.step_calls.append(command)
            return (
                {
                    "current_state": {
                        "timestamp": 6,
                        "machines": [{"id": "node-a", "cpu": 0.51, "memory_usage": 0.48}],
                        "pods": [{"id": "task-a", "assigned_node": "node-a", "running": True}],
                        "metrics": {"queue_length": 1, "energy_price": 0.11},
                    }
                },
                {"reward": 1.0},
                False,
                {"source": "session"},
            )

    class FailingOrchestrator:
        def reset(self):
            raise AssertionError("session reset should be used first")

        def step(self, command):
            raise AssertionError("session step should be used first")

    backend = AIOpsLabBackend("demo", max_steps=4, orchestrator=FailingOrchestrator())
    backend._session = FakeSession()

    reset_obs = backend.reset()
    assert reset_obs.timestamp == 5
    assert reset_obs.nodes[0].node_id == "node-a"

    result = backend.step(AgentAction(agent_name="AgentA", kind=ActionKind.MIGRATE, target="node-a"))

    assert backend._session.step_calls[0]["kind"] == ActionKind.MIGRATE.value
    assert result.next_observation.timestamp == 6
    assert result.next_observation.queue_length == 1
    assert result.info["status"] == "live_adapter"
