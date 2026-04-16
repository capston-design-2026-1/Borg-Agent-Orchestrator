from __future__ import annotations

from orchestrator.types import ActionKind, AgentAction, ScoreFeedback


PRIORITY_ORDER = {"AgentA": 1, "AgentC": 2, "AgentB": 3}


def resolve(actions: list[AgentAction], feedback: ScoreFeedback | None = None) -> AgentAction:
    if not actions:
        return AgentAction("Referee", ActionKind.NOOP, score=0.0)

    sorted_actions = sorted(actions, key=lambda a: (PRIORITY_ORDER.get(a.agent_name, 99), -a.score))
    agent_a = next((a for a in sorted_actions if a.agent_name == "AgentA"), None)

    if agent_a and agent_a.kind == ActionKind.MIGRATE:
        return agent_a

    scored_actions = []
    for action in sorted_actions:
        weight = 1.0
        if feedback is not None:
            weight = float(feedback.agent_weights.get(action.agent_name, 1.0))
        scored_actions.append((action.score * weight, PRIORITY_ORDER.get(action.agent_name, 99), action))

    for _, _, action in sorted(scored_actions, key=lambda item: (-item[0], item[1])):
        if action.kind != ActionKind.NOOP:
            return action
    return sorted_actions[0]
