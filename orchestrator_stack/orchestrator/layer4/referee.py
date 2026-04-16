from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.types import ActionKind, AgentAction


PRIORITY_ORDER = {"AgentA": 1, "AgentC": 2, "AgentB": 3}


@dataclass(slots=True)
class RefereeDecision:
    action: AgentAction
    rationale: str
    overridden: dict[str, str] = field(default_factory=dict)


def _admission_decision(action: AgentAction) -> str:
    return str(action.payload.get("decision", "admit"))


def _power_state(action: AgentAction) -> str:
    return str(action.payload.get("state", "on"))


def resolve_with_context(actions: list[AgentAction]) -> RefereeDecision:
    if not actions:
        return RefereeDecision(
            action=AgentAction("Referee", ActionKind.NOOP, score=0.0),
            rationale="no proposals",
        )

    meaningful = [action for action in actions if action.kind != ActionKind.NOOP]
    if not meaningful:
        fallback = min(
            actions,
            key=lambda action: (PRIORITY_ORDER.get(action.agent_name, action.priority or 99), -action.score),
        )
        return RefereeDecision(action=fallback, rationale="all agents proposed noop")

    agent_a_migrate = next(
        (
            action
            for action in meaningful
            if action.agent_name == "AgentA" and action.kind == ActionKind.MIGRATE
        ),
        None,
    )
    if agent_a_migrate is not None:
        overridden = {
            action.agent_name: "safety-first migration takes precedence"
            for action in meaningful
            if action is not agent_a_migrate
        }
        return RefereeDecision(
            action=agent_a_migrate,
            rationale="agent-a migration preempts lower-priority actions",
            overridden=overridden,
        )

    restrictive_admission = next(
        (
            action
            for action in meaningful
            if action.agent_name == "AgentC"
            and action.kind == ActionKind.ADMISSION
            and _admission_decision(action) in {"queue", "reject"}
        ),
        None,
    )
    if restrictive_admission is not None:
        overridden = {
            action.agent_name: "admission protection overrides non-safety actions"
            for action in meaningful
            if action is not restrictive_admission
        }
        return RefereeDecision(
            action=restrictive_admission,
            rationale="agent-c admission protection preempts efficiency actions",
            overridden=overridden,
        )

    power_state_actions = [
        action
        for action in meaningful
        if action.kind == ActionKind.POWER_STATE and _power_state(action) in {"sleep", "off", "on"}
    ]
    if power_state_actions:
        selected = max(power_state_actions, key=lambda action: action.score)
        overridden = {
            action.agent_name: "higher-scoring power-state action selected"
            for action in meaningful
            if action is not selected
        }
        return RefereeDecision(
            action=selected,
            rationale="power-state proposal selected by score",
            overridden=overridden,
        )

    selected = min(
        meaningful,
        key=lambda action: (PRIORITY_ORDER.get(action.agent_name, action.priority or 99), -action.score),
    )
    overridden = {
        action.agent_name: "lower referee precedence"
        for action in meaningful
        if action is not selected
    }
    return RefereeDecision(
        action=selected,
        rationale="selected by deterministic referee priority",
        overridden=overridden,
    )


def resolve(actions: list[AgentAction]) -> AgentAction:
    return resolve_with_context(actions).action
