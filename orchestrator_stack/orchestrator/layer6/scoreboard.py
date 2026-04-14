from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.types import GlobalScore


@dataclass(slots=True)
class Scoreboard:
    alpha: float
    beta: float
    gamma: float
    history: list[GlobalScore] = field(default_factory=list)

    def update(self, reward_by_agent: dict[str, float]) -> GlobalScore:
        score = GlobalScore(raw_rewards=reward_by_agent, alpha=self.alpha, beta=self.beta, gamma=self.gamma)
        self.history.append(score)
        return score

    def total(self) -> float:
        return sum(s.total for s in self.history)

    def average(self) -> float:
        if not self.history:
            return 0.0
        return self.total() / len(self.history)
