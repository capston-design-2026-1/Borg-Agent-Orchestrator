from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from orchestrator.layer4.policy import default_policy_actions
from orchestrator.layer4.rllib_env import OrchestratorMultiAgentEnv
from orchestrator.layer4.referee import resolve
from orchestrator.layer4.policy import decode_agent_action
from orchestrator.layer6.scoreboard import Scoreboard

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
    os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Keep RLlib/Tune artifacts inside the repository runtime path so the
    # full-process command is runnable in sandboxed or CI environments.
    os.environ.setdefault("RAY_AIR_LOCAL_CACHE_DIR", str(out))
    os.environ.setdefault("RAY_RESULTS_DIR", str(out))

    try:
        from ray.rllib.algorithms.ppo import PPOConfig
    except Exception:  # pragma: no cover
        PPOConfig = None

    if PPOConfig is None:
        return {
            "status": "skipped",
            "reason": "ray[rllib] is not installed",
            "output_dir": str(out),
        }

    env_name = "OrchestratorMultiAgentEnv"
    try:
        from ray.rllib.algorithms import algorithm as ray_algorithm
        import ray.train.constants as ray_train_constants

        ray_algorithm.DEFAULT_STORAGE_PATH = str(out)
        ray_train_constants.DEFAULT_STORAGE_PATH = str(out)
    except Exception:
        pass

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

    try:
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
        return {
            "status": "trained",
            "checkpoint": checkpoint_path,
            "train_iters": int(train_iters),
            "episode_reward_mean": float(last_result.get("episode_reward_mean", 0.0)),
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "reason": f"rllib runtime failed: {exc}",
            "checkpoint": None,
            "train_iters": int(train_iters),
            "output_dir": str(out),
        }
    finally:
        try:
            import ray

            ray.shutdown()
        except Exception:
            pass


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
