from __future__ import annotations

from dataclasses import dataclass

from orchestrator.types import ActionKind, AgentAction, Observation


@dataclass(slots=True)
class AgentARiskMitigator:
    priority: int = 1

    def act(self, obs: Observation) -> AgentAction:
        if not obs.p_fail_scores:
            return AgentAction("AgentA", ActionKind.NOOP, score=0.0, priority=self.priority)
        node_id, score = max(obs.p_fail_scores.items(), key=lambda kv: kv[1])
        if score >= 0.7:
            return AgentAction("AgentA", ActionKind.MIGRATE, target=node_id, score=float(score), priority=self.priority)
        return AgentAction("AgentA", ActionKind.NOOP, score=float(score), priority=self.priority)


@dataclass(slots=True)
class AgentBEfficiencyOptimizer:
    priority: int = 3

    def act(self, obs: Observation) -> AgentAction:
        if not obs.demand_projection:
            return AgentAction("AgentB", ActionKind.NOOP, score=0.0, priority=self.priority)

        node_id, demand = min(obs.demand_projection.items(), key=lambda kv: kv[1])
        if demand < 0.3:
            return AgentAction(
                "AgentB",
                ActionKind.POWER_STATE,
                target=node_id,
                payload={"state": "sleep"},
                score=1.0 - float(demand),
                priority=self.priority,
            )
        return AgentAction("AgentB", ActionKind.NOOP, score=1.0 - float(demand), priority=self.priority)


@dataclass(slots=True)
class AgentCGatekeeper:
    priority: int = 2

    def act(self, obs: Observation) -> AgentAction:
        overloaded = sum(1 for n in obs.nodes if n.cpu_util > 0.85 or n.mem_util > 0.85)
        if obs.queue_length > 120 or overloaded > max(1, len(obs.nodes) // 2):
            return AgentAction(
                "AgentC",
                ActionKind.ADMISSION,
                payload={"decision": "queue"},
                score=1.0,
                priority=self.priority,
            )
        if obs.queue_length < 20 and overloaded == 0:
            return AgentAction(
                "AgentC",
                ActionKind.ADMISSION,
                payload={"decision": "admit"},
                score=1.0,
                priority=self.priority,
            )
        return AgentAction(
            "AgentC",
            ActionKind.ADMISSION,
            payload={"decision": "admit"},
            score=0.5,
            priority=self.priority,
        )
