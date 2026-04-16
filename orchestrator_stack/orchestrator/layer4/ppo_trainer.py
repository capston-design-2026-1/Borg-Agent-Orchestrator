from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from orchestrator.layer4.policy import default_policy_actions
from orchestrator.layer4.rllib_env import OrchestratorMultiAgentEnv
from orchestrator.layer4.referee import resolve
from orchestrator.layer4.policy import decode_agent_action
from orchestrator.layer6.scoreboard import FeedbackLoop, Scoreboard

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
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")

    out = Path(output_dir).resolve()
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
        .training(
            lr=learning_rate,
            train_batch_size=32,
            minibatch_size=16,
            num_epochs=1,
        )
        .multi_agent(
            policies=policies,
            policy_mapping_fn=lambda agent_id, *args, **kwargs: agent_id,
        )
        .resources(num_gpus=0)
        .env_runners(num_env_runners=0, num_envs_per_env_runner=1, rollout_fragment_length=8, batch_mode="truncate_episodes")
        .reporting(min_sample_timesteps_per_iteration=8, min_train_timesteps_per_iteration=8, min_time_s_per_iteration=0)
    )

    algo = config.build_algo()
    last_result: dict[str, Any] = {}
    for _ in range(max(1, train_iters)):
        last_result = algo.train()

    checkpoint_result = algo.save(checkpoint_dir=str(out))
    checkpoint_path = str(out)
    try:
        checkpoint_path = str(checkpoint_result.checkpoint.path)
    except Exception:
        checkpoint_path = str(checkpoint_result)

    algo.stop()
    try:
        import ray

        ray.shutdown()
    except Exception:
        pass

    return {
        "status": "trained",
        "checkpoint": checkpoint_path,
        "train_iters": int(train_iters),
        "episode_reward_mean": float(last_result.get("episode_reward_mean", 0.0)),
    }


def evaluate_heuristic_policy(backend, *, alpha: float, beta: float, gamma: float, steps: int) -> dict[str, float | int]:
    obs = backend.reset()
    scoreboard = Scoreboard(alpha=alpha, beta=beta, gamma=gamma)
    feedback_loop = FeedbackLoop(scoreboard)

    for _ in range(max(1, steps)):
        action_ids = default_policy_actions(obs)
        proposals = [
            decode_agent_action("AgentA", action_ids["AgentA"], obs),
            decode_agent_action("AgentB", action_ids["AgentB"], obs),
            decode_agent_action("AgentC", action_ids["AgentC"], obs),
        ]
        action = feedback_loop.resolve(proposals, resolve)
        result = backend.step(action)
        feedback_loop.apply(result.reward_by_agent)
        obs = result.next_observation
        if result.done:
            break

    snap = scoreboard.snapshot()
    return {
        "steps": len(scoreboard.history),
        "total_score": scoreboard.total(),
        "avg_score": scoreboard.average(),
        "adjusted_total_score": float(snap["adjusted_total"]),
        "balance_gap": float(snap["balance_gap"]),
    }
