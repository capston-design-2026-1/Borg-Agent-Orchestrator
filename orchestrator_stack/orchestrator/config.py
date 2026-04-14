from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class OrchestratorConfig:
    trace_path: Path
    risk_model_path: Path
    demand_model_path: Path
    use_aiopslab_backend: bool = False
    episode_steps: int = 200
    alpha: float = 1.0
    beta: float = 0.6
    gamma: float = 0.8

    @staticmethod
    def load(path: str | Path) -> "OrchestratorConfig":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return OrchestratorConfig(
            trace_path=Path(raw["trace_path"]),
            risk_model_path=Path(raw["risk_model_path"]),
            demand_model_path=Path(raw["demand_model_path"]),
            use_aiopslab_backend=bool(raw.get("use_aiopslab_backend", False)),
            episode_steps=int(raw.get("episode_steps", 200)),
            alpha=float(raw.get("alpha", 1.0)),
            beta=float(raw.get("beta", 0.6)),
            gamma=float(raw.get("gamma", 0.8)),
        )
