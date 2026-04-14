from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class OrchestratorConfig:
    trace_path: Path
    risk_model_path: Path
    demand_model_path: Path
    raw_metrics_path: Path | None = None
    use_aiopslab_backend: bool = False
    aiopslab_problem_id: str = "misconfig-1"
    aiopslab_max_steps: int = 50
    episode_steps: int = 200
    alpha: float = 1.0
    beta: float = 0.6
    gamma: float = 0.8
    rllib_train_iters: int = 5
    ppo_learning_rate: float = 3e-4
    optuna_storage_path: Path = Path("orchestrator_stack/runtime/optuna/orchestrator.db")

    @staticmethod
    def load(path: str | Path) -> "OrchestratorConfig":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw_metrics = raw.get("raw_metrics_path")
        return OrchestratorConfig(
            trace_path=Path(raw["trace_path"]),
            risk_model_path=Path(raw["risk_model_path"]),
            demand_model_path=Path(raw["demand_model_path"]),
            raw_metrics_path=Path(raw_metrics) if raw_metrics else None,
            use_aiopslab_backend=bool(raw.get("use_aiopslab_backend", False)),
            aiopslab_problem_id=str(raw.get("aiopslab_problem_id", "misconfig-1")),
            aiopslab_max_steps=int(raw.get("aiopslab_max_steps", 50)),
            episode_steps=int(raw.get("episode_steps", 200)),
            alpha=float(raw.get("alpha", 1.0)),
            beta=float(raw.get("beta", 0.6)),
            gamma=float(raw.get("gamma", 0.8)),
            rllib_train_iters=int(raw.get("rllib_train_iters", 5)),
            ppo_learning_rate=float(raw.get("ppo_learning_rate", 3e-4)),
            optuna_storage_path=Path(raw.get("optuna_storage_path", "orchestrator_stack/runtime/optuna/orchestrator.db")),
        )
