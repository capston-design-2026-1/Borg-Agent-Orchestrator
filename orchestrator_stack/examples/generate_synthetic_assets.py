from __future__ import annotations

from pathlib import Path

import numpy as np


OUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    rng = np.random.default_rng(42)
    x_risk = rng.uniform(0, 1, size=(4000, 4)).astype(np.float32)
    y_risk = ((0.55 * x_risk[:, 0] + 0.35 * x_risk[:, 1] + 0.1 * x_risk[:, 2]) > 0.62).astype(np.int32)
    np.savez(OUT_DIR / "risk_train.npz", x=x_risk, y=y_risk)

    x_dem = rng.uniform(0, 1, size=(4000, 4)).astype(np.float32)
    y_dem = (
        0.4 * x_dem[:, 0] + 0.4 * x_dem[:, 1] + 0.2 * x_dem[:, 3] + rng.normal(0, 0.03, 4000)
    ).clip(0, 1).astype(np.float32)
    np.savez(OUT_DIR / "demand_train.npz", x=x_dem, y=y_dem)

    models_dir = OUT_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    print("Generated:")
    print(f"- {(OUT_DIR / 'risk_train.npz').as_posix()}")
    print(f"- {(OUT_DIR / 'demand_train.npz').as_posix()}")
    print(f"- {models_dir.as_posix()} (empty; fill via train-risk/train-demand)")


if __name__ == "__main__":
    main()
