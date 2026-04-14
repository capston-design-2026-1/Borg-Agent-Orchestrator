from __future__ import annotations

from dataclasses import dataclass
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


def tune_reward_weights(objective_fn: Callable[[float, float, float], float], n_trials: int = 30) -> TuningResult:
    if optuna is None:
        raise RuntimeError("optuna is not installed. Install optional dependency to run tuning.")

    def objective(trial):
        alpha = trial.suggest_float("alpha", 0.5, 2.5)
        beta = trial.suggest_float("beta", 0.1, 2.0)
        gamma = trial.suggest_float("gamma", 0.1, 2.0)
        return objective_fn(alpha, beta, gamma)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    best = study.best_trial
    return TuningResult(
        alpha=float(best.params["alpha"]),
        beta=float(best.params["beta"]),
        gamma=float(best.params["gamma"]),
        score=float(best.value),
    )
