from __future__ import annotations

from dataclasses import dataclass

from orchestrator.config import OrchestratorConfig
from orchestrator.layer1.trace_ingestor import load_trace_rows
from orchestrator.layer2.simulator import AIOpsLabBackend, TraceDrivenTwinBackend
from orchestrator.layer3.predictors import ResourceDemandForecast, SafetyRiskForecast
from orchestrator.layer4.agents import AgentARiskMitigator, AgentBEfficiencyOptimizer, AgentCGatekeeper
from orchestrator.layer4.referee import resolve
from orchestrator.layer6.scoreboard import Scoreboard


@dataclass(slots=True)
class RunSummary:
    steps: int
    total_score: float
    avg_score: float


def run_episode(config: OrchestratorConfig) -> RunSummary:
    rows = load_trace_rows(config.trace_path)
    backend = AIOpsLabBackend(rows) if config.use_aiopslab_backend else TraceDrivenTwinBackend(rows)
    risk_model = SafetyRiskForecast.load(config.risk_model_path)
    demand_model = ResourceDemandForecast.load(config.demand_model_path)

    agent_a = AgentARiskMitigator()
    agent_b = AgentBEfficiencyOptimizer()
    agent_c = AgentCGatekeeper()
    scoreboard = Scoreboard(alpha=config.alpha, beta=config.beta, gamma=config.gamma)

    obs = backend.reset()
    total_steps = min(config.episode_steps, len(rows))

    for _ in range(total_steps):
        obs.p_fail_scores = risk_model.predict(obs)
        obs.demand_projection = demand_model.predict(obs)

        proposals = [agent_a.act(obs), agent_b.act(obs), agent_c.act(obs)]
        validated_action = resolve(proposals)

        result = backend.step(validated_action)
        scoreboard.update(result.reward_by_agent)
        obs = result.next_observation
        if result.done:
            break

    return RunSummary(steps=len(scoreboard.history), total_score=scoreboard.total(), avg_score=scoreboard.average())
