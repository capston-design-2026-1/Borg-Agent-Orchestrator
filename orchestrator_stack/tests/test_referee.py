from orchestrator.layer4.referee import resolve
from orchestrator.types import ActionKind, AgentAction, ScoreFeedback


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


def test_referee_uses_scoreboard_feedback_when_safety_override_is_absent():
    feedback = ScoreFeedback(
        global_score=4.0,
        adjusted_rewards={"AgentA": 1.0, "AgentB": 3.0, "AgentC": 1.0},
        agent_weights={"AgentA": 1.0, "AgentB": 1.8, "AgentC": 0.7},
        cumulative_by_agent={"AgentA": 4.0, "AgentB": 0.0, "AgentC": 2.0},
        recent_by_agent={"AgentA": 1.0, "AgentB": 0.0, "AgentC": 0.5},
        dominant_agent="AgentA",
        balance_gap=4.0,
    )
    action = resolve(
        [
            AgentAction("AgentB", ActionKind.POWER_STATE, target="node-1", score=0.6),
            AgentAction("AgentC", ActionKind.ADMISSION, payload={"decision": "queue"}, score=1.0),
        ],
        feedback=feedback,
    )

    assert action.agent_name == "AgentB"
    assert action.kind == ActionKind.POWER_STATE
