from __future__ import annotations

from dataclasses import dataclass

from orchestrator.types import ActionKind, AgentAction, Observation


@dataclass(slots=True)
class AgentPolicySpace:
    name: str
    action_count: int


POLICY_SPACES = {
    "AgentA": AgentPolicySpace("AgentA", action_count=2),  # 0 noop, 1 migrate highest-risk
    "AgentB": AgentPolicySpace("AgentB", action_count=3),  # 0 noop, 1 sleep low-demand, 2 wake high-demand
    "AgentC": AgentPolicySpace("AgentC", action_count=3),  # 0 admit, 1 queue, 2 reject
}


def default_policy_actions(obs: Observation) -> dict[str, int]:
    max_risk = max(obs.p_fail_scores.values(), default=0.0)
    min_demand = min(obs.demand_projection.values(), default=1.0)

    agent_a = 1 if max_risk >= 0.7 else 0
    agent_b = 1 if min_demand < 0.3 else (2 if max(obs.demand_projection.values(), default=0.0) > 0.8 else 0)
    agent_c = 1 if obs.queue_length > 100 else 0
    return {"AgentA": agent_a, "AgentB": agent_b, "AgentC": agent_c}


def decode_agent_action(agent_name: str, action_id: int, obs: Observation) -> AgentAction:
    if agent_name == "AgentA":
        if action_id == 1 and obs.p_fail_scores:
            node_id, score = max(obs.p_fail_scores.items(), key=lambda kv: kv[1])
            return AgentAction("AgentA", ActionKind.MIGRATE, target=node_id, score=float(score), priority=1)
        return AgentAction("AgentA", ActionKind.NOOP, score=0.0, priority=1)

    if agent_name == "AgentB":
        if action_id == 1 and obs.demand_projection:
            node_id, demand = min(obs.demand_projection.items(), key=lambda kv: kv[1])
            return AgentAction(
                "AgentB",
                ActionKind.POWER_STATE,
                target=node_id,
                payload={"state": "sleep"},
                score=1.0 - float(demand),
                priority=3,
            )
        if action_id == 2 and obs.demand_projection:
            node_id, demand = max(obs.demand_projection.items(), key=lambda kv: kv[1])
            return AgentAction(
                "AgentB",
                ActionKind.POWER_STATE,
                target=node_id,
                payload={"state": "on"},
                score=float(demand),
                priority=3,
            )
        return AgentAction("AgentB", ActionKind.NOOP, score=0.0, priority=3)

    if agent_name == "AgentC":
        if action_id == 1:
            return AgentAction("AgentC", ActionKind.ADMISSION, payload={"decision": "queue"}, score=1.0, priority=2)
        if action_id == 2:
            return AgentAction("AgentC", ActionKind.ADMISSION, payload={"decision": "reject"}, score=1.0, priority=2)
        return AgentAction("AgentC", ActionKind.ADMISSION, payload={"decision": "admit"}, score=0.5, priority=2)

    return AgentAction(agent_name, ActionKind.NOOP, score=0.0, priority=99)
