from __future__ import annotations

from typing import Any

try:
    from pettingzoo import ParallelEnv
except Exception:  # pragma: no cover
    ParallelEnv = object  # type: ignore[misc,assignment]

from orchestrator.layer4.rllib_env import OrchestratorMultiAgentEnv


class OrchestratorParallelEnv(ParallelEnv):  # type: ignore[misc]
    """PettingZoo-style parallel wrapper around the orchestrator backend."""

    metadata = {"name": "borg_orchestrator_parallel_v0", "render_modes": []}

    def __init__(self, env_config: dict[str, Any]):
        self._env = OrchestratorMultiAgentEnv(env_config)
        self.possible_agents = list(self._env.possible_agents)
        self.agents = list(self.possible_agents)
        self.observation_spaces = getattr(self._env, "observation_spaces", {})
        self.action_spaces = getattr(self._env, "action_spaces", {})

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None):
        self.agents = list(self.possible_agents)
        return self._env.reset(seed=seed, options=options)

    def step(self, actions: dict[str, int]):
        observations, rewards, terminated, truncated, infos = self._env.step(actions)
        terminations = {agent: bool(terminated.get(agent, terminated.get("__all__", False))) for agent in self.possible_agents}
        truncations = {agent: bool(truncated.get(agent, truncated.get("__all__", False))) for agent in self.possible_agents}
        if all(terminations.values()) or all(truncations.values()):
            self.agents = []
        else:
            self.agents = list(self.possible_agents)
        return observations, rewards, terminations, truncations, infos

    def observation_space(self, agent: str):
        return self.observation_spaces[agent]

    def action_space(self, agent: str):
        return self.action_spaces[agent]
