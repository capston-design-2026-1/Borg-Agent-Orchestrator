from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator.layer4.policy import default_policy_actions
from orchestrator.layer4.rllib_env import OrchestratorMultiAgentEnv
from orchestrator.layer4.referee import resolve
from orchestrator.layer4.policy import decode_agent_action
from orchestrator.layer6.scoreboard import Scoreboard

try:
    from ray.rllib.algorithms.ppo import PPOConfig
except Exception:  # pragma: no cover
    PPOConfig = None


def train_multiagent_ppo(
    backend,
    *,
    alpha: float,
    beta: float,
    gamma: float,
    learning_rate: float,
    train_iters: int,
    output_dir: str | Path,
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if PPOConfig is None:
        return {
            "status": "skipped",
            "reason": "ray[rllib] is not installed",
            "output_dir": str(out),
        }

    env_name = "OrchestratorMultiAgentEnv"

    # Delayed import avoids hard dependency when RLlib is not installed.
    from ray.tune.registry import register_env

    register_env(env_name, lambda cfg: OrchestratorMultiAgentEnv(cfg))

    policies = {"AgentA", "AgentB", "AgentC"}

    config = (
        PPOConfig()
        .environment(env=env_name, env_config={"backend": backend, "alpha": alpha, "beta": beta, "gamma": gamma})
        .framework("torch")
        .training(lr=learning_rate)
        .multi_agent(
            policies=policies,
            policy_mapping_fn=lambda agent_id, *args, **kwargs: agent_id,
        )
        .rollouts(num_rollout_workers=0)
    )

    algo = config.build()
    last_result: dict[str, Any] = {}
    for _ in range(max(1, train_iters)):
        last_result = algo.train()

    checkpoint = algo.save(checkpoint_dir=str(out))
    return {
        "status": "trained",
        "checkpoint": str(checkpoint),
        "train_iters": int(train_iters),
        "episode_reward_mean": float(last_result.get("episode_reward_mean", 0.0)),
    }


def evaluate_heuristic_policy(backend, *, alpha: float, beta: float, gamma: float, steps: int) -> dict[str, float | int]:
    obs = backend.reset()
    scoreboard = Scoreboard(alpha=alpha, beta=beta, gamma=gamma)

    for _ in range(max(1, steps)):
        action_ids = default_policy_actions(obs)
        proposals = [
            decode_agent_action("AgentA", action_ids["AgentA"], obs),
            decode_agent_action("AgentB", action_ids["AgentB"], obs),
            decode_agent_action("AgentC", action_ids["AgentC"], obs),
        ]
        action = resolve(proposals)
        result = backend.step(action)
        scoreboard.update(result.reward_by_agent)
        obs = result.next_observation
        if result.done:
            break

    return {
        "steps": len(scoreboard.history),
        "total_score": scoreboard.total(),
        "avg_score": scoreboard.average(),
    }
