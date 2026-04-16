from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep OpenMP runtime contention low when mixing xgboost + torch/ray in one process.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")

# Keep Ray artifacts inside repository runtime paths to avoid user-home permission issues.
RUNTIME = ROOT / "runtime"
os.environ.setdefault("RAY_TMPDIR", str(RUNTIME / "ray_tmp"))
os.environ.setdefault("RAY_AIR_LOCAL_CACHE_DIR", str(RUNTIME / "ray_air"))
os.environ.setdefault("TUNE_RESULT_DIR", str(RUNTIME / "rllib"))
os.environ.setdefault("RAY_ENABLE_UV_RUN_RUNTIME_ENV", "0")

from orchestrator.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
