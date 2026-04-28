import asyncio
import json

from orchestrator.layer2.aiopslab_contract import AIOpsLabPolicyAgent, initialize_aiopslab_problem


class FakeOrchestrator:
    def __init__(self):
        self.registered = None

    def init_problem(self, problem_id):
        assert problem_id == "problem-1"
        return "desc", "instructions", ["get_metrics"]

    def register_agent(self, agent):
        self.registered = agent


def test_initialize_aiopslab_problem_uses_confirmed_contract():
    agent = AIOpsLabPolicyAgent()
    orchestrator = FakeOrchestrator()

    context = initialize_aiopslab_problem(orchestrator, problem_id="problem-1", agent=agent)

    assert context == ("desc", "instructions", ["get_metrics"])
    assert orchestrator.registered is agent
    assert agent.problem_desc == "desc"


def test_aiopslab_policy_agent_returns_serialized_orchestrator_action():
    agent = AIOpsLabPolicyAgent()
    state = json.dumps(
        {
            "timestamp": 1,
            "nodes": [{"node_id": "n1", "cpu_util": 0.9, "mem_util": 0.8, "disk_util": 0.2, "net_util": 0.1}],
            "tasks": [{"task_id": "t1", "node_id": "n1"}],
            "p_fail_scores": {"n1": 0.91},
            "demand_projection": {"n1": 0.8},
            "queue_length": 10,
            "energy_price": 0.1,
        }
    )

    action = json.loads(asyncio.run(agent.get_action(state)))

    assert action["agent"] == "AgentA"
    assert action["kind"] == "migrate"
    assert action["target"] == "n1"
