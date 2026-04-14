from __future__ import annotations

from orchestrator.types import ActionKind, AgentAction


PRIORITY_ORDER = {"AgentA": 1, "AgentC": 2, "AgentB": 3}


def resolve(actions: list[AgentAction]) -> AgentAction:
    if not actions:
        return AgentAction("Referee", ActionKind.NOOP, score=0.0)

    sorted_actions = sorted(actions, key=lambda a: (PRIORITY_ORDER.get(a.agent_name, 99), -a.score))
    agent_a = next((a for a in sorted_actions if a.agent_name == "AgentA"), None)

    if agent_a and agent_a.kind == ActionKind.MIGRATE:
        return agent_a

    for action in sorted_actions:
        if action.kind != ActionKind.NOOP:
            return action
    return sorted_actions[0]
