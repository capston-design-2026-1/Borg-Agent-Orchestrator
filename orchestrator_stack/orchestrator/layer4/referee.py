from __future__ import annotations

from orchestrator.types import ActionKind, AgentAction


PRIORITY_ORDER = {"AgentA": 1, "AgentC": 2, "AgentB": 3}


def resolve(actions: list[AgentAction]) -> AgentAction:
    if not actions:
        return AgentAction("Referee", ActionKind.NOOP, score=0.0)

    indexed = sorted(actions, key=lambda a: (PRIORITY_ORDER.get(a.agent_name, 99), -a.score))
    top = indexed[0]

    # Safety guard: if AgentA proposes migration on a high-risk node, suppress
    # conflicting power-off actions from AgentB in the same step.
    if top.agent_name == "AgentA" and top.kind == ActionKind.MIGRATE:
        return top

    for action in indexed:
        if action.kind != ActionKind.NOOP:
            return action
    return indexed[0]
