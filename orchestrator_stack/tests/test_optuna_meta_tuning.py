from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.config import OrchestratorConfig
from orchestrator.layer5.optuna_tuner import TuningResult, tune_policy_and_rewards
from orchestrator.main import tune_policy_and_reward_layer


class OptunaMetaTuningTests(unittest.TestCase):
    def test_layer5_policy_tuner_samples_rl_hyperparameters(self) -> None:
        calls: list[tuple[float, float, float, float, int, int, int, int]] = []

        def objective(
            alpha: float,
            beta: float,
            gamma: float,
            learning_rate: float,
            train_batch_size: int,
            minibatch_size: int,
            num_epochs: int,
            rollout_fragment_length: int,
        ) -> float:
            calls.append(
                (
                    alpha,
                    beta,
                    gamma,
                    learning_rate,
                    train_batch_size,
                    minibatch_size,
                    num_epochs,
                    rollout_fragment_length,
                )
            )
            self.assertLessEqual(minibatch_size, train_batch_size)
            return float(train_batch_size - minibatch_size + num_epochs + rollout_fragment_length)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = tune_policy_and_rewards(
                objective,
                n_trials=1,
                storage_path=Path(tmpdir) / "optuna.db",
                study_name="test_policy_reward_meta",
            )

        self.assertEqual(len(calls), 1)
        self.assertIsNotNone(result.learning_rate)
        self.assertIsNotNone(result.train_batch_size)
        self.assertIsNotNone(result.minibatch_size)
        self.assertIsNotNone(result.num_epochs)
        self.assertIsNotNone(result.rollout_fragment_length)

    def test_main_policy_tuner_invokes_ppo_training(self) -> None:
        config = OrchestratorConfig(
            trace_path=Path("orchestrator_stack/examples/sample_trace.json"),
            risk_model_path=Path("orchestrator_stack/examples/models/risk_model.json"),
            demand_model_path=Path("orchestrator_stack/examples/models/demand_model.json"),
            rllib_train_iters=2,
            ppo_learning_rate=3e-4,
            ppo_train_batch_size=32,
            ppo_minibatch_size=16,
            ppo_num_epochs=1,
            ppo_rollout_fragment_length=8,
            optuna_storage_path=Path("orchestrator_stack/runtime/optuna/test_main_optuna.db"),
        )

        trainer_calls: list[dict[str, object]] = []

        def fake_train_multiagent_ppo(backend, **kwargs):
            trainer_calls.append({"backend": backend, **kwargs})
            return {
                "status": "trained",
                "episode_reward_mean": 12.5,
                "learning_rate": kwargs["learning_rate"],
                "train_batch_size": kwargs["train_batch_size"],
                "minibatch_size": kwargs["minibatch_size"],
                "num_epochs": kwargs["num_epochs"],
                "rollout_fragment_length": kwargs["rollout_fragment_length"],
            }

        def fake_tune_policy_and_rewards(objective_fn, **kwargs):
            score = objective_fn(1.8, 0.9, 1.1, 2e-4, 64, 32, 2, 16)
            return TuningResult(
                alpha=1.8,
                beta=0.9,
                gamma=1.1,
                score=score,
                learning_rate=2e-4,
                train_batch_size=64,
                minibatch_size=32,
                num_epochs=2,
                rollout_fragment_length=16,
            )

        with (
            patch("orchestrator.main.ensure_trace_exists", return_value=config.trace_path),
            patch("orchestrator.main.load_trace_rows", return_value=[{"timestamp": "t0", "nodes": [], "tasks": []}]),
            patch("orchestrator.main._build_predictor_runtime", side_effect=lambda rows, cfg: {"rows": rows, "cfg": cfg}),
            patch("orchestrator.main.train_multiagent_ppo", side_effect=fake_train_multiagent_ppo),
            patch("orchestrator.main.evaluate_heuristic_policy", return_value={"total_score": 100.0}),
            patch("orchestrator.main.tune_policy_and_rewards", side_effect=fake_tune_policy_and_rewards),
        ):
            result = tune_policy_and_reward_layer(config, trials=1)

        self.assertEqual(len(trainer_calls), 1)
        self.assertEqual(trainer_calls[0]["learning_rate"], 2e-4)
        self.assertEqual(trainer_calls[0]["train_batch_size"], 64)
        self.assertEqual(trainer_calls[0]["minibatch_size"], 32)
        self.assertEqual(trainer_calls[0]["num_epochs"], 2)
        self.assertEqual(trainer_calls[0]["rollout_fragment_length"], 16)
        self.assertEqual(result["score"], 17.5)


if __name__ == "__main__":
    unittest.main()
