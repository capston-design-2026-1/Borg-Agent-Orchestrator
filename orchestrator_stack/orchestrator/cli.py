from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from orchestrator.config import OrchestratorConfig
from orchestrator.layer5.optuna_tuner import tune_reward_weights
from orchestrator.layer3.predictors import train_demand_model, train_safety_model
from orchestrator.main import run_episode


def _load_npz(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    return data["x"], data["y"]


def cmd_train_risk(args: argparse.Namespace) -> None:
    x, y = _load_npz(Path(args.dataset))
    train_safety_model(x, y.astype(np.int32), args.out)
    print(f"saved risk model: {args.out}")


def cmd_train_demand(args: argparse.Namespace) -> None:
    x, y = _load_npz(Path(args.dataset))
    train_demand_model(x, y.astype(np.float32), args.out)
    print(f"saved demand model: {args.out}")


def cmd_run(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    summary = run_episode(cfg)
    print(json.dumps({"steps": summary.steps, "total_score": summary.total_score, "avg_score": summary.avg_score}, indent=2))


def cmd_tune(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)

    def objective(alpha: float, beta: float, gamma: float) -> float:
        trial_cfg = OrchestratorConfig(
            trace_path=cfg.trace_path,
            risk_model_path=cfg.risk_model_path,
            demand_model_path=cfg.demand_model_path,
            use_aiopslab_backend=cfg.use_aiopslab_backend,
            episode_steps=cfg.episode_steps,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
        )
        return run_episode(trial_cfg).total_score

    result = tune_reward_weights(objective_fn=objective, n_trials=args.trials)
    print(json.dumps(result.__dict__, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Borg full orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_train_risk = sub.add_parser("train-risk")
    p_train_risk.add_argument("--dataset", required=True)
    p_train_risk.add_argument("--out", required=True)
    p_train_risk.set_defaults(func=cmd_train_risk)

    p_train_demand = sub.add_parser("train-demand")
    p_train_demand.add_argument("--dataset", required=True)
    p_train_demand.add_argument("--out", required=True)
    p_train_demand.set_defaults(func=cmd_train_demand)

    p_run = sub.add_parser("run")
    p_run.add_argument("--config", required=True)
    p_run.set_defaults(func=cmd_run)

    p_tune = sub.add_parser("tune")
    p_tune.add_argument("--config", required=True)
    p_tune.add_argument("--trials", type=int, default=20)
    p_tune.set_defaults(func=cmd_tune)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
