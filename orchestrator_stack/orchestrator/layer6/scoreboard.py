from __future__ import annotations

from dataclasses import dataclass, field

from orchestrator.types import GlobalScore, ScoreFeedback, ScoreboardUpdate


AGENT_NAMES = ("AgentA", "AgentB", "AgentC")


@dataclass(slots=True)
class Scoreboard:
    alpha: float
    beta: float
    gamma: float
    feedback_gain: float = 0.15
    team_spirit: float = 0.2
    recent_window: int = 5
    history: list[GlobalScore] = field(default_factory=list)
    feedback_history: list[ScoreFeedback] = field(default_factory=list)
    cumulative_by_agent: dict[str, float] = field(default_factory=lambda: {agent: 0.0 for agent in AGENT_NAMES})
    adjusted_cumulative_by_agent: dict[str, float] = field(default_factory=lambda: {agent: 0.0 for agent in AGENT_NAMES})

    def reset(self) -> None:
        self.history.clear()
        self.feedback_history.clear()
        for agent in AGENT_NAMES:
            self.cumulative_by_agent[agent] = 0.0
            self.adjusted_cumulative_by_agent[agent] = 0.0

    def update(self, reward_by_agent: dict[str, float]) -> ScoreboardUpdate:
        score = GlobalScore(raw_rewards=reward_by_agent, alpha=self.alpha, beta=self.beta, gamma=self.gamma)
        self.history.append(score)
        for agent in AGENT_NAMES:
            self.cumulative_by_agent[agent] += float(reward_by_agent.get(agent, 0.0))
        feedback = self._build_feedback(score)
        self.feedback_history.append(feedback)
        for agent in AGENT_NAMES:
            self.adjusted_cumulative_by_agent[agent] += feedback.adjusted_rewards[agent]
        return ScoreboardUpdate(score=score, feedback=feedback)

    def total(self) -> float:
        return sum(s.total for s in self.history)

    def adjusted_total(self) -> float:
        return sum(self.adjusted_cumulative_by_agent.values())

    def average(self) -> float:
        if not self.history:
            return 0.0
        return self.total() / len(self.history)

    def adjusted_average(self) -> float:
        if not self.history:
            return 0.0
        return self.adjusted_total() / len(self.history)

    def snapshot(self) -> dict[str, float | int]:
        last_feedback = self.feedback_history[-1] if self.feedback_history else None
        return {
            "steps": len(self.history),
            "total": self.total(),
            "adjusted_total": self.adjusted_total(),
            "average": self.average(),
            "adjusted_average": self.adjusted_average(),
            "agent_a": self.cumulative_by_agent["AgentA"],
            "agent_b": self.cumulative_by_agent["AgentB"],
            "agent_c": self.cumulative_by_agent["AgentC"],
            "adjusted_agent_a": self.adjusted_cumulative_by_agent["AgentA"],
            "adjusted_agent_b": self.adjusted_cumulative_by_agent["AgentB"],
            "adjusted_agent_c": self.adjusted_cumulative_by_agent["AgentC"],
            "balance_gap": last_feedback.balance_gap if last_feedback else 0.0,
            "last_global_score": last_feedback.global_score if last_feedback else 0.0,
            "last_dominant_agent": last_feedback.dominant_agent or "",
        }

    def latest_feedback(self) -> ScoreFeedback | None:
        if not self.feedback_history:
            return None
        return self.feedback_history[-1]

    def _build_feedback(self, score: GlobalScore) -> ScoreFeedback:
        cumulative_values = list(self.cumulative_by_agent.values())
        cohort_average = sum(cumulative_values) / max(1, len(cumulative_values))
        balance_gap = max(cumulative_values, default=0.0) - min(cumulative_values, default=0.0)
        normalizer = max(1.0, abs(cohort_average), balance_gap, max(abs(v) for v in cumulative_values) if cumulative_values else 1.0)
        recent_by_agent = self._recent_average_by_agent()
        agent_weights: dict[str, float] = {}
        adjusted_rewards: dict[str, float] = {}

        for agent in AGENT_NAMES:
            deficit = (cohort_average - self.cumulative_by_agent[agent]) / normalizer
            weight = 1.0 + (self.feedback_gain * deficit)
            bounded_weight = min(1.25, max(0.75, weight))
            agent_weights[agent] = bounded_weight
            adjusted_rewards[agent] = float(score.raw_rewards.get(agent, 0.0)) * bounded_weight + (score.total * self.team_spirit)

        dominant_agent = max(self.cumulative_by_agent, key=self.cumulative_by_agent.get, default=None)
        return ScoreFeedback(
            global_score=score.total,
            adjusted_rewards=adjusted_rewards,
            agent_weights=agent_weights,
            cumulative_by_agent=dict(self.cumulative_by_agent),
            recent_by_agent=recent_by_agent,
            dominant_agent=dominant_agent,
            balance_gap=balance_gap,
        )

    def _recent_average_by_agent(self) -> dict[str, float]:
        recent_scores = self.history[-max(1, self.recent_window) :]
        if not recent_scores:
            return {agent: 0.0 for agent in AGENT_NAMES}
        return {
            agent: sum(float(score.raw_rewards.get(agent, 0.0)) for score in recent_scores) / len(recent_scores)
            for agent in AGENT_NAMES
        }
