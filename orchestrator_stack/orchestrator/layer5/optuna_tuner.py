from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    import optuna
except Exception:  # pragma: no cover
    optuna = None


from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class TuningResult:
    alpha: float
    beta: float
    gamma: float
    score: float
    learning_rate: float | None = None


def export_study_report(study: optuna.Study, study_name: str) -> Path:
    """Export study results to a KST-timestamped markdown report in reports/."""
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    ts = now.strftime("%Y%m%d%H%M")
    
    report_path = Path(f"reports/{ts}_optuna_{study_name}.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    best = study.best_trial
    
    content = [
        f"# Optuna Study Report: {study_name}",
        f"\n- **Generated (KST):** {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Best Score:** {best.value:.4f}",
        f"- **Best Params:**",
    ]
    for k, v in best.params.items():
        content.append(f"    - {k}: {v}")
        
    content.append("\n## Top 5 Trials")
    trials = sorted(study.trials, key=lambda t: t.value if t.value is not None else -1e9, reverse=True)
    for i, t in enumerate(trials[:5]):
        content.append(f"{i+1}. Trial {t.number}: Score {t.value:.4f} (Params: {t.params})")
        
    report_path.write_text("\n".join(content), encoding="utf-8")
    return report_path


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
    export_study_report(study, study_name)
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
    export_study_report(study, study_name)
    best = study.best_trial
    return TuningResult(
        alpha=float(best.params["alpha"]),
        beta=float(best.params["beta"]),
        gamma=float(best.params["gamma"]),
        learning_rate=float(best.params["learning_rate"]),
        score=float(best.value),
    )
