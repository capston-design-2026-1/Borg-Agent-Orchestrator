from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from orchestrator.layer2.feature_extractor import FEATURE_COUNT


OUT_DIR = Path(__file__).resolve().parent


def _build_sample_metrics(path: Path) -> None:
    rng = np.random.default_rng(7)
    rows = []
    base_ts = 1_700_000_000
    for step in range(200):
        ts = base_ts + (step * 60)
        queue = int(max(1, 50 + 30 * np.sin(step / 13)))
        energy = float(np.clip(0.1 + 0.03 * np.cos(step / 15), 0.04, 0.2))
        for node_idx in range(6):
            cpu = float(np.clip(0.5 + 0.35 * np.sin((step + node_idx) / 17) + rng.normal(0, 0.04), 0, 1))
            mem = float(np.clip(0.45 + 0.33 * np.cos((step + node_idx) / 19) + rng.normal(0, 0.04), 0, 1))
            disk = float(np.clip(0.4 + 0.1 * np.sin((step + node_idx) / 23), 0, 1))
            net = float(np.clip(0.35 + 0.15 * np.cos((step + node_idx) / 21), 0, 1))
            rows.append(
                {
                    "timestamp": ts,
                    "node_id": f"node-{node_idx + 1}",
                    "cpu_util": cpu,
                    "mem_util": mem,
                    "disk_util": disk,
                    "net_util": net,
                    "task_id": f"task-{step}-{node_idx}",
                    "urgency": float(np.clip(0.5 + 0.4 * rng.normal(), 0, 1)),
                    "queue_priority": int(rng.integers(1, 4)),
                    "queue_length": queue,
                    "energy_price": energy,
                    "task_death": bool(cpu > 0.95 and mem > 0.95 and rng.random() < 0.05),
                }
            )
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> None:
    rng = np.random.default_rng(42)
    x_risk = rng.uniform(0, 1, size=(4000, FEATURE_COUNT)).astype(np.float32)
    y_risk = (
        (0.35 * x_risk[:, 0] + 0.25 * x_risk[:, 1] + 0.15 * x_risk[:, 4] + 0.15 * x_risk[:, 5] + 0.1 * x_risk[:, 6])
        > 0.62
    ).astype(np.int32)
    np.savez(OUT_DIR / "risk_train.npz", x=x_risk, y=y_risk)

    x_dem = rng.uniform(0, 1, size=(4000, FEATURE_COUNT)).astype(np.float32)
    y_dem = (
        0.25 * x_dem[:, 0]
        + 0.25 * x_dem[:, 1]
        + 0.15 * x_dem[:, 3]
        + 0.15 * x_dem[:, 4]
        + 0.1 * x_dem[:, 5]
        + 0.05 * x_dem[:, 6]
        - 0.05 * x_dem[:, 7]
        + rng.normal(0, 0.03, 4000)
    ).clip(0, 1).astype(np.float32)
    np.savez(OUT_DIR / "demand_train.npz", x=x_dem, y=y_dem)

    metrics_path = OUT_DIR / "sample_metrics.json"
    _build_sample_metrics(metrics_path)

    models_dir = OUT_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print("Generated:")
    print(f"- {(OUT_DIR / 'risk_train.npz').as_posix()}")
    print(f"- {(OUT_DIR / 'demand_train.npz').as_posix()}")
    print(f"- {metrics_path.as_posix()}")
    print(f"- {models_dir.as_posix()} (empty; fill via train-risk/train-demand or train-brains)")


if __name__ == "__main__":
    main()
