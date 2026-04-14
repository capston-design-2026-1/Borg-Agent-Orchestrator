from __future__ import annotations

from typing import Any

try:
    from ray.rllib.env.multi_agent_env import MultiAgentEnv
except Exception:  # pragma: no cover
    MultiAgentEnv = object  # type: ignore[misc,assignment]

from orchestrator.layer4.agents import AgentARiskMitigator, AgentBEfficiencyOptimizer, AgentCGatekeeper
from orchestrator.layer4.referee import resolve
from orchestrator.layer6.scoreboard import Scoreboard
from orchestrator.types import Observation, StepResult


class OrchestratorMultiAgentEnv(MultiAgentEnv):  # type: ignore[misc]
    """RLlib-compatible environment wrapper for the orchestrator loop."""

    def __init__(self, env_config: dict[str, Any]):
        self.backend = env_config["backend"]
        self.scoreboard = Scoreboard(
            alpha=float(env_config.get("alpha", 1.0)),
            beta=float(env_config.get("beta", 0.6)),
            gamma=float(env_config.get("gamma", 0.8)),
        )
        self.agents = {
            "AgentA": AgentARiskMitigator(),
            "AgentB": AgentBEfficiencyOptimizer(),
            "AgentC": AgentCGatekeeper(),
        }
        self._obs: Observation | None = None

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        self._obs = self.backend.reset()
        packed = self._pack_obs(self._obs)
        return packed, {}

    def step(self, action_dict):
        assert self._obs is not None
        proposals = [
            self.agents["AgentA"].act(self._obs),
            self.agents["AgentB"].act(self._obs),
            self.agents["AgentC"].act(self._obs),
        ]
        action = resolve(proposals)
        result: StepResult = self.backend.step(action)
        self._obs = result.next_observation

        score = self.scoreboard.update(result.reward_by_agent)
        rewards = {"AgentA": score.raw_rewards.get("AgentA", 0.0), "AgentB": score.raw_rewards.get("AgentB", 0.0), "AgentC": score.raw_rewards.get("AgentC", 0.0)}
        terminated = {"__all__": result.done, "AgentA": result.done, "AgentB": result.done, "AgentC": result.done}
        truncated = {"__all__": False, "AgentA": False, "AgentB": False, "AgentC": False}

        obs = self._pack_obs(self._obs)
        infos = {"AgentA": result.info, "AgentB": result.info, "AgentC": result.info}
        return obs, rewards, terminated, truncated, infos

    def _pack_obs(self, obs: Observation) -> dict[str, list[float]]:
        max_risk = max(obs.p_fail_scores.values(), default=0.0)
        max_demand = max(obs.demand_projection.values(), default=0.0)
        util = [sum(n.cpu_util for n in obs.nodes) / max(1, len(obs.nodes)), sum(n.mem_util for n in obs.nodes) / max(1, len(obs.nodes))]
        base = [float(obs.queue_length), float(obs.energy_price), float(max_risk), float(max_demand), util[0], util[1]]
        return {"AgentA": base, "AgentB": base, "AgentC": base}
