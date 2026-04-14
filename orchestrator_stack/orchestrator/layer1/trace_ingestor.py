from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_trace_rows(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    return json.loads(source.read_text(encoding="utf-8"))
