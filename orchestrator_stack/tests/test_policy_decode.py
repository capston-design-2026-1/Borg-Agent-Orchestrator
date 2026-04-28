from orchestrator.layer4.policy import decode_agent_action
from orchestrator.types import NodeState, Observation


def test_decode_agent_a_migrate_action():
    obs = Observation(
        timestamp=1,
        nodes=[NodeState("n1", 0.9, 0.8, 0.2, 0.1), NodeState("n2", 0.2, 0.2, 0.1, 0.1)],
        tasks=[],
        p_fail_scores={"n1": 0.95, "n2": 0.1},
        demand_projection={"n1": 0.8, "n2": 0.2},
        queue_length=10,
        energy_price=0.1,
    )

    action = decode_agent_action("AgentA", 1, obs)
    assert action.target == "n1"


def test_decode_secondary_architecture_actions():
    obs = Observation(
        timestamp=1,
        nodes=[NodeState("n1", 0.9, 0.8, 0.2, 0.1), NodeState("n2", 0.2, 0.2, 0.1, 0.1)],
        tasks=[],
        p_fail_scores={"n1": 0.95, "n2": 0.1},
        demand_projection={"n1": 0.8, "n2": 0.2},
        queue_length=10,
        energy_price=0.1,
    )

    assert decode_agent_action("AgentA", 2, obs).kind.value == "replicate"
    assert decode_agent_action("AgentA", 3, obs).kind.value == "throttle"
    assert decode_agent_action("AgentB", 3, obs).kind.value == "dvfs"
    assert decode_agent_action("AgentB", 4, obs).kind.value == "memory_balloon"
    assert decode_agent_action("AgentC", 3, obs).payload["decision"] == "deprioritize"
    assert decode_agent_action("AgentC", 4, obs).kind.value == "resource_cap"
