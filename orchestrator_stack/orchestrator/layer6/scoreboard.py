from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.types import GlobalScore


@dataclass(slots=True)
class Scoreboard:
    alpha: float
    beta: float
    gamma: float
    history: list[GlobalScore] = field(default_factory=list)
    cumulative_by_agent: dict[str, float] = field(default_factory=lambda: {"AgentA": 0.0, "AgentB": 0.0, "AgentC": 0.0})

    def update(self, reward_by_agent: dict[str, float]) -> GlobalScore:
        score = GlobalScore(raw_rewards=reward_by_agent, alpha=self.alpha, beta=self.beta, gamma=self.gamma)
        self.history.append(score)
        for agent in self.cumulative_by_agent:
            self.cumulative_by_agent[agent] += float(reward_by_agent.get(agent, 0.0))
        return score

    def total(self) -> float:
        return sum(s.total for s in self.history)

    def average(self) -> float:
        if not self.history:
            return 0.0
        return self.total() / len(self.history)

    def snapshot(self) -> dict[str, float | int]:
        return {
            "steps": len(self.history),
            "total": self.total(),
            "average": self.average(),
            "agent_a": self.cumulative_by_agent["AgentA"],
            "agent_b": self.cumulative_by_agent["AgentB"],
            "agent_c": self.cumulative_by_agent["AgentC"],
        }
