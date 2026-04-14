from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from orchestrator.types import AgentAction, NodeState, Observation, StepResult, TaskState


class SimulatorBackend(Protocol):
    def reset(self) -> Observation: ...

    def step(self, action: AgentAction) -> StepResult: ...


@dataclass(slots=True)
class TraceDrivenTwinBackend:
    rows: list[dict]
    index: int = 0

    def reset(self) -> Observation:
        self.index = 0
        return self._to_observation(self.rows[self.index])

    def step(self, action: AgentAction) -> StepResult:
        row = self.rows[self.index]
        base_reward = self._reward_from_action(row, action)
        self.index = min(self.index + 1, len(self.rows) - 1)
        next_obs = self._to_observation(self.rows[self.index])
        done = self.index >= len(self.rows) - 1
        rewards = {
            "AgentA": base_reward["AgentA"],
            "AgentB": base_reward["AgentB"],
            "AgentC": base_reward["AgentC"],
        }
        return StepResult(next_observation=next_obs, reward_by_agent=rewards, done=done, info={"applied": action.kind.value})

    def _to_observation(self, row: dict) -> Observation:
        nodes = [
            NodeState(
                node_id=n["node_id"],
                cpu_util=float(n["cpu_util"]),
                mem_util=float(n["mem_util"]),
                disk_util=float(n.get("disk_util", 0.0)),
                net_util=float(n.get("net_util", 0.0)),
                power_state=n.get("power_state", "on"),
            )
            for n in row["nodes"]
        ]
        tasks = [
            TaskState(
                task_id=t["task_id"],
                node_id=t["node_id"],
                urgency=float(t.get("urgency", 0.5)),
                queue_priority=int(t.get("queue_priority", 1)),
                alive=bool(t.get("alive", True)),
            )
            for t in row["tasks"]
        ]
        return Observation(
            timestamp=int(row["timestamp"]),
            nodes=nodes,
            tasks=tasks,
            p_fail_scores=row.get("p_fail_scores", {}),
            demand_projection=row.get("demand_projection", {}),
            queue_length=int(row.get("queue_length", 0)),
            energy_price=float(row.get("energy_price", 0.1)),
        )

    def _reward_from_action(self, row: dict, action: AgentAction) -> dict[str, float]:
        rewards = {"AgentA": 0.0, "AgentB": 0.0, "AgentC": 0.0}
        p_fail = max(row.get("p_fail_scores", {"x": 0.0}).values(), default=0.0)
        demand = max(row.get("demand_projection", {"x": 0.0}).values(), default=0.0)

        if action.agent_name == "AgentA":
            rewards["AgentA"] += 10.0 if (action.kind.value == "migrate" and p_fail > 0.75) else 1.0
            rewards["AgentA"] -= 20.0 if action.kind.value == "migrate" and p_fail < 0.4 else 0.0
        if action.agent_name == "AgentB":
            rewards["AgentB"] += 5.0 if action.kind.value == "power_state" and demand < 0.35 else 1.0
            rewards["AgentB"] -= 30.0 if action.kind.value == "power_state" and demand > 0.75 else 0.0
        if action.agent_name == "AgentC":
            rewards["AgentC"] += 5.0 if action.kind.value == "admission" and row.get("queue_length", 0) < 40 else 2.0
            rewards["AgentC"] -= 50.0 if action.kind.value == "admission" and row.get("queue_length", 0) > 100 else 0.0

        if row.get("task_death", False):
            rewards["AgentA"] -= 100.0
        return rewards


class AIOpsLabBackend(TraceDrivenTwinBackend):
    """
    Placeholder adapter for Microsoft AIOpsLab.

    This keeps interface parity with the local twin backend so users can swap
    from traces to full digital-twin integrations without changing orchestrator
    control flow.
    """
