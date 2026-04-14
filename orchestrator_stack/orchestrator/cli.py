from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from orchestrator.config import OrchestratorConfig
from orchestrator.layer1.collector import build_trace_file
from orchestrator.layer1.trace_ingestor import load_trace_rows
from orchestrator.layer3.predictors import train_demand_model, train_models_from_trace, train_safety_model
from orchestrator.main import run_episode, run_full_process, run_policy_training, train_brain_models


def _load_npz(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    return data["x"], data["y"]


def cmd_build_trace(args: argparse.Namespace) -> None:
    out = build_trace_file(args.metrics, args.out, interval_seconds=args.interval_seconds)
    print(json.dumps({"trace_path": str(out)}, indent=2))


def cmd_train_risk(args: argparse.Namespace) -> None:
    x, y = _load_npz(Path(args.dataset))
    path = train_safety_model(x, y.astype(np.int32), args.out)
    print(json.dumps({"risk_model": str(path)}, indent=2))


def cmd_train_demand(args: argparse.Namespace) -> None:
    x, y = _load_npz(Path(args.dataset))
    path = train_demand_model(x, y.astype(np.float32), args.out)
    print(json.dumps({"demand_model": str(path)}, indent=2))


def cmd_train_brains(args: argparse.Namespace) -> None:
    rows = load_trace_rows(args.trace)
    risk, demand = train_models_from_trace(rows, args.risk_out, args.demand_out)
    print(json.dumps({"risk_model": str(risk), "demand_model": str(demand)}, indent=2))


def cmd_train_brains_from_config(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    result = train_brain_models(cfg)
    print(json.dumps(result, indent=2))


def cmd_run(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    summary = run_episode(cfg)
    print(json.dumps(asdict(summary), indent=2))


def cmd_train_policy(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    result = run_policy_training(cfg, output_dir=args.output_dir)
    print(json.dumps(result, indent=2))


def cmd_tune(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    from orchestrator.main import tune_reward_layer

    result = tune_reward_layer(cfg, trials=args.trials)
    print(json.dumps(result, indent=2))


def cmd_tune_policy_and_rewards(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    from orchestrator.main import tune_policy_and_reward_layer

    result = tune_policy_and_reward_layer(cfg, trials=args.trials)
    print(json.dumps(result, indent=2))


def cmd_full_process(args: argparse.Namespace) -> None:
    cfg = OrchestratorConfig.load(args.config)
    result = run_full_process(cfg, tune_trials=args.trials)
    print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Borg full orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build_trace = sub.add_parser("build-trace")
    p_build_trace.add_argument("--metrics", required=True)
    p_build_trace.add_argument("--out", required=True)
    p_build_trace.add_argument("--interval-seconds", type=int, default=60)
    p_build_trace.set_defaults(func=cmd_build_trace)

    p_train_risk = sub.add_parser("train-risk")
    p_train_risk.add_argument("--dataset", required=True)
    p_train_risk.add_argument("--out", required=True)
    p_train_risk.set_defaults(func=cmd_train_risk)

    p_train_demand = sub.add_parser("train-demand")
    p_train_demand.add_argument("--dataset", required=True)
    p_train_demand.add_argument("--out", required=True)
    p_train_demand.set_defaults(func=cmd_train_demand)

    p_train_brains = sub.add_parser("train-brains")
    p_train_brains.add_argument("--trace", required=True)
    p_train_brains.add_argument("--risk-out", required=True)
    p_train_brains.add_argument("--demand-out", required=True)
    p_train_brains.set_defaults(func=cmd_train_brains)

    p_train_brains_cfg = sub.add_parser("train-brains-from-config")
    p_train_brains_cfg.add_argument("--config", required=True)
    p_train_brains_cfg.set_defaults(func=cmd_train_brains_from_config)

    p_run = sub.add_parser("run")
    p_run.add_argument("--config", required=True)
    p_run.set_defaults(func=cmd_run)

    p_train_policy = sub.add_parser("train-policy")
    p_train_policy.add_argument("--config", required=True)
    p_train_policy.add_argument("--output-dir", default="orchestrator_stack/runtime/rllib")
    p_train_policy.set_defaults(func=cmd_train_policy)

    p_tune = sub.add_parser("tune")
    p_tune.add_argument("--config", required=True)
    p_tune.add_argument("--trials", type=int, default=20)
    p_tune.set_defaults(func=cmd_tune)

    p_tune_policy = sub.add_parser("tune-policy-rewards")
    p_tune_policy.add_argument("--config", required=True)
    p_tune_policy.add_argument("--trials", type=int, default=20)
    p_tune_policy.set_defaults(func=cmd_tune_policy_and_rewards)

    p_full = sub.add_parser("full-process")
    p_full.add_argument("--config", required=True)
    p_full.add_argument("--trials", type=int, default=5)
    p_full.set_defaults(func=cmd_full_process)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
