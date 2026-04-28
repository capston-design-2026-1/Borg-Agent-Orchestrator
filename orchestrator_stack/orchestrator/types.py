from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionKind(str, Enum):
    MIGRATE = "migrate"
    REPLICATE = "replicate"
    THROTTLE = "throttle"
    POWER_STATE = "power_state"
    DVFS = "dvfs"
    MEMORY_BALLOON = "memory_balloon"
    ADMISSION = "admission"
    RESOURCE_CAP = "resource_cap"
    NOOP = "noop"


@dataclass(slots=True)
class NodeState:
    node_id: str
    cpu_util: float
    mem_util: float
    disk_util: float
    net_util: float
    power_state: str = "on"


@dataclass(slots=True)
class TaskState:
    task_id: str
    node_id: str
    urgency: float
    queue_priority: int
    alive: bool = True


@dataclass(slots=True)
class Observation:
    timestamp: int
    nodes: list[NodeState]
    tasks: list[TaskState]
    p_fail_scores: dict[str, float]
    demand_projection: dict[str, float]
    queue_length: int
    energy_price: float


@dataclass(slots=True)
class AgentAction:
    agent_name: str
    kind: ActionKind
    target: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    priority: int = 0


@dataclass(slots=True)
class StepResult:
    next_observation: Observation
    reward_by_agent: dict[str, float]
    done: bool
    info: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GlobalScore:
    raw_rewards: dict[str, float]
    alpha: float
    beta: float
    gamma: float

    @property
    def total(self) -> float:
        return (
            self.alpha * self.raw_rewards.get("AgentA", 0.0)
            + self.beta * self.raw_rewards.get("AgentB", 0.0)
            + self.gamma * self.raw_rewards.get("AgentC", 0.0)
        )
