from __future__ import annotations

import subprocess
import time
from pathlib import Path

from codex_autonomy.models import SessionResult


class SessionAdapter:
    def __init__(self, command_template: str, timeout_seconds: int):
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def run(self, *, workdir: Path, prompt_file: Path) -> SessionResult:
        command = self.command_template.format(prompt_file=str(prompt_file), workdir=str(workdir))
        started = time.time()
        proc = subprocess.run(
            command,
            cwd=str(workdir),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            shell=True,
        )
        duration = time.time() - started
        return SessionResult(
            return_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=duration,
        )
