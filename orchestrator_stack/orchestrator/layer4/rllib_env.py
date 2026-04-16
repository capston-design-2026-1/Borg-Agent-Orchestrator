from __future__ import annotations

from typing import Any

import numpy as np

try:
    from gymnasium.spaces import Box, Discrete
    from ray.rllib.env.multi_agent_env import MultiAgentEnv
except Exception:  # pragma: no cover
    Box = None  # type: ignore[assignment]
    Discrete = None  # type: ignore[assignment]
    MultiAgentEnv = object  # type: ignore[misc,assignment]

from orchestrator.layer4.policy import POLICY_SPACES, decode_agent_action, default_policy_actions
from orchestrator.layer4.referee import resolve
from orchestrator.layer6.scoreboard import Scoreboard
from orchestrator.types import Observation, StepResult


class OrchestratorMultiAgentEnv(MultiAgentEnv):  # type: ignore[misc]
    """RLlib-compatible multi-agent environment for orchestrator training."""

    def __init__(self, env_config: dict[str, Any]):
        super().__init__()
        self.backend = env_config["backend"]
        self.possible_agents = ["AgentA", "AgentB", "AgentC"]
        self.agents = list(self.possible_agents)
        self.scoreboard = Scoreboard(
            alpha=float(env_config.get("alpha", 1.0)),
            beta=float(env_config.get("beta", 0.6)),
            gamma=float(env_config.get("gamma", 0.8)),
        )
        self._obs: Observation | None = None
        self._feedback = None

        if Box is not None and Discrete is not None:
            self.observation_spaces = {
                "AgentA": Box(low=0.0, high=1.0, shape=(6,), dtype=float),
                "AgentB": Box(low=0.0, high=1.0, shape=(6,), dtype=float),
                "AgentC": Box(low=0.0, high=1.0, shape=(6,), dtype=float),
            }
            self.action_spaces = {
                "AgentA": Discrete(POLICY_SPACES["AgentA"].action_count),
                "AgentB": Discrete(POLICY_SPACES["AgentB"].action_count),
                "AgentC": Discrete(POLICY_SPACES["AgentC"].action_count),
            }

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        self.scoreboard.reset()
        self._feedback = None
        self._obs = self.backend.reset()
        packed = self._pack_obs(self._obs)
        return packed, {}

    def step(self, action_dict):
        assert self._obs is not None
        action_ids = default_policy_actions(self._obs)
        for agent_name in ("AgentA", "AgentB", "AgentC"):
            if agent_name in action_dict:
                action_ids[agent_name] = int(action_dict[agent_name])

        proposals = [
            decode_agent_action("AgentA", action_ids["AgentA"], self._obs),
            decode_agent_action("AgentB", action_ids["AgentB"], self._obs),
            decode_agent_action("AgentC", action_ids["AgentC"], self._obs),
        ]
        validated = resolve(proposals, feedback=self._feedback)
        result: StepResult = self.backend.step(validated)
        self._obs = result.next_observation

        update = self.scoreboard.update(result.reward_by_agent)
        self._feedback = update.feedback
        rewards = {
            "AgentA": update.feedback.adjusted_rewards.get("AgentA", 0.0),
            "AgentB": update.feedback.adjusted_rewards.get("AgentB", 0.0),
            "AgentC": update.feedback.adjusted_rewards.get("AgentC", 0.0),
        }
        terminated = {"__all__": result.done, "AgentA": result.done, "AgentB": result.done, "AgentC": result.done}
        truncated = {"__all__": False, "AgentA": False, "AgentB": False, "AgentC": False}
        shared_info = {
            **result.info,
            "global_score": update.feedback.global_score,
            "scoreboard": self.scoreboard.snapshot(),
            "agent_weights": dict(update.feedback.agent_weights),
        }
        infos = {"AgentA": shared_info, "AgentB": shared_info, "AgentC": shared_info}
        return self._pack_obs(self._obs), rewards, terminated, truncated, infos

    def _pack_obs(self, obs: Observation) -> dict[str, np.ndarray]:
        max_risk = max(obs.p_fail_scores.values(), default=0.0)
        max_demand = max(obs.demand_projection.values(), default=0.0)
        cpu_avg = sum(n.cpu_util for n in obs.nodes) / max(1, len(obs.nodes))
        mem_avg = sum(n.mem_util for n in obs.nodes) / max(1, len(obs.nodes))
        queue_norm = min(1.0, obs.queue_length / max(1, len(obs.tasks) + 1))
        energy_norm = min(1.0, obs.energy_price / 0.2)
        vector = np.asarray(
            [queue_norm, energy_norm, float(max_risk), float(max_demand), float(cpu_avg), float(mem_avg)],
            dtype=np.float32,
        )
        return {"AgentA": vector.copy(), "AgentB": vector.copy(), "AgentC": vector.copy()}
