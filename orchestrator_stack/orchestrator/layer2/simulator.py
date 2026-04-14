from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from orchestrator.types import ActionKind, AgentAction, NodeState, Observation, StepResult, TaskState


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
        current = self.rows[self.index]
        applied = self._apply_action(current, action)
        rewards = self._reward_from_action(current, action, applied)

        self.index = min(self.index + 1, len(self.rows) - 1)
        next_obs = self._to_observation(self.rows[self.index])
        done = self.index >= len(self.rows) - 1

        info = {
            "applied": action.kind.value,
            "agent": action.agent_name,
            "target": action.target,
            "task_map": {t.task_id: t.node_id for t in next_obs.tasks},
            "cluster_cpu_avg": sum(n.cpu_util for n in next_obs.nodes) / max(1, len(next_obs.nodes)),
            "cluster_mem_avg": sum(n.mem_util for n in next_obs.nodes) / max(1, len(next_obs.nodes)),
            "queue_length": next_obs.queue_length,
        }
        return StepResult(next_observation=next_obs, reward_by_agent=rewards, done=done, info=info)

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
            for t in row.get("tasks", [])
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

    def _apply_action(self, row: dict, action: AgentAction) -> dict[str, bool]:
        applied = {
            "migrated": False,
            "powered": False,
            "queued": False,
            "rejected": False,
            "admitted": False,
        }

        if action.kind == ActionKind.MIGRATE:
            applied["migrated"] = action.target is not None
        elif action.kind == ActionKind.POWER_STATE:
            applied["powered"] = action.payload.get("state") in {"sleep", "off", "on"}
        elif action.kind == ActionKind.ADMISSION:
            decision = action.payload.get("decision", "admit")
            if decision == "queue":
                applied["queued"] = True
            elif decision == "reject":
                applied["rejected"] = True
            else:
                applied["admitted"] = True
        return applied

    def _reward_from_action(self, row: dict, action: AgentAction, applied: dict[str, bool]) -> dict[str, float]:
        rewards = {"AgentA": 1.0, "AgentB": 1.0, "AgentC": 1.0}
        p_fail = max(row.get("p_fail_scores", {"x": 0.0}).values(), default=0.0)
        demand = max(row.get("demand_projection", {"x": 0.0}).values(), default=0.0)

        if action.agent_name == "AgentA":
            if applied["migrated"] and p_fail > 0.75:
                rewards["AgentA"] += 10.0
            if applied["migrated"] and p_fail < 0.4:
                rewards["AgentA"] -= 20.0
        if action.agent_name == "AgentB":
            if applied["powered"] and demand < 0.35:
                rewards["AgentB"] += 5.0
            if applied["powered"] and demand > 0.75:
                rewards["AgentB"] -= 30.0
        if action.agent_name == "AgentC":
            qlen = int(row.get("queue_length", 0))
            if applied["admitted"] and qlen < 80:
                rewards["AgentC"] += 5.0
            if applied["rejected"] and qlen < 60:
                rewards["AgentC"] -= 20.0
            if applied["admitted"] and qlen > 120:
                rewards["AgentC"] -= 50.0

        if row.get("task_death", False):
            rewards["AgentA"] -= 100.0
        return rewards


class AIOpsLabBackend(TraceDrivenTwinBackend):
    """
    AIOpsLab adapter surface.

    Current implementation keeps the same protocol as the trace backend.
    Replace `_to_observation` and `step` with direct AIOpsLab environment calls
    when binding to a live deployment.
    """
