from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    import optuna
except Exception:  # pragma: no cover
    optuna = None


@dataclass(slots=True)
class TuningResult:
    alpha: float
    beta: float
    gamma: float
    score: float
    learning_rate: float | None = None


def tune_reward_weights(
    objective_fn: Callable[[float, float, float], float],
    *,
    n_trials: int = 30,
    storage: str | None = None,
    study_name: str = "orchestrator_reward_weights",
) -> TuningResult:
    if optuna is None:
        raise RuntimeError("optuna is not installed. Install optional dependency to run tuning.")

    if storage and storage.startswith("sqlite:///"):
        sqlite_path = Path(storage.removeprefix("sqlite:///"))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    study = optuna.create_study(
        direction="maximize",
        storage=storage,
        study_name=study_name,
        load_if_exists=True,
    )

    def objective(trial):
        alpha = trial.suggest_float("alpha", 0.5, 2.5)
        beta = trial.suggest_float("beta", 0.1, 2.0)
        gamma = trial.suggest_float("gamma", 0.1, 2.0)
        return objective_fn(alpha, beta, gamma)

    study.optimize(objective, n_trials=n_trials)
    best = study.best_trial
    return TuningResult(
        alpha=float(best.params["alpha"]),
        beta=float(best.params["beta"]),
        gamma=float(best.params["gamma"]),
        score=float(best.value),
    )


def tune_policy_and_rewards(
    objective_fn: Callable[[float, float, float, float], float],
    *,
    n_trials: int,
    storage_path: str | Path,
    study_name: str = "orchestrator_policy_and_rewards",
) -> TuningResult:
    if optuna is None:
        raise RuntimeError("optuna is not installed. Install optional dependency to run tuning.")

    storage_file = Path(storage_path)
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_url = f"sqlite:///{storage_file}"

    study = optuna.create_study(
        direction="maximize",
        storage=storage_url,
        study_name=study_name,
        load_if_exists=True,
    )

    def objective(trial):
        alpha = trial.suggest_float("alpha", 0.5, 2.5)
        beta = trial.suggest_float("beta", 0.1, 2.0)
        gamma = trial.suggest_float("gamma", 0.1, 2.0)
        learning_rate = trial.suggest_float("learning_rate", 1e-5, 3e-3, log=True)
        return objective_fn(alpha, beta, gamma, learning_rate)

    study.optimize(objective, n_trials=max(1, n_trials))
    best = study.best_trial
    return TuningResult(
        alpha=float(best.params["alpha"]),
        beta=float(best.params["beta"]),
        gamma=float(best.params["gamma"]),
        learning_rate=float(best.params["learning_rate"]),
        score=float(best.value),
    )
