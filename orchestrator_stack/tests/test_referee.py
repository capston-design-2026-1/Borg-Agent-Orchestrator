from orchestrator.layer4.referee import resolve
from orchestrator.types import ActionKind, AgentAction


def test_referee_prioritizes_agent_a_migration():
    action = resolve(
        [
            AgentAction("AgentB", ActionKind.POWER_STATE, target="node-1", score=0.9),
            AgentAction("AgentA", ActionKind.MIGRATE, target="node-1", score=0.7),
            AgentAction("AgentC", ActionKind.ADMISSION, score=0.8),
        ]
    )
    assert action.agent_name == "AgentA"
    assert action.kind == ActionKind.MIGRATE
