from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codex_autonomy.config import load_config  # noqa: E402
from codex_autonomy.guardian import run_guardian_forever  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex autonomy guardian")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    run_guardian_forever(config, config_path)


if __name__ == "__main__":
    main()
