from __future__ import annotations

import subprocess
import threading
import time
from queue import Empty, Queue
from pathlib import Path
from typing import Callable

from codex_autonomy.models import SessionResult


class SessionAdapter:
    def __init__(self, command_template: str, timeout_seconds: int):
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        *,
        workdir: Path,
        prompt_file: Path,
        heartbeat_seconds: float = 8.0,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> SessionResult:
        command = self.command_template.format(prompt_file=str(prompt_file), workdir=str(workdir))
        started = time.time()
        proc = subprocess.Popen(
            command,
            cwd=str(workdir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            bufsize=1,
        )

        q: Queue[tuple[str, str | None]] = Queue()
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        stdout_chars = 0
        stderr_chars = 0
        stdout_lines_count = 0
        stderr_lines_count = 0

        def _reader(stream_name: str, stream) -> None:
            try:
                while True:
                    line = stream.readline()
                    if line == "":
                        break
                    q.put((stream_name, line))
            finally:
                q.put((stream_name, None))

        t_out = threading.Thread(target=_reader, args=("stdout", proc.stdout), daemon=True)
        t_err = threading.Thread(target=_reader, args=("stderr", proc.stderr), daemon=True)
        t_out.start()
        t_err.start()

        done_streams = set()
        next_heartbeat = started + max(1.0, float(heartbeat_seconds))
        timed_out = False

        while True:
            now = time.time()
            if now - started > self.timeout_seconds:
                timed_out = True
                proc.terminate()
                time.sleep(1.0)
                if proc.poll() is None:
                    proc.kill()
                break

            try:
                stream_name, payload = q.get(timeout=0.2)
                if payload is None:
                    done_streams.add(stream_name)
                else:
                    if stream_name == "stdout":
                        stdout_lines.append(payload)
                        stdout_chars += len(payload)
                        stdout_lines_count += 1
                    else:
                        stderr_lines.append(payload)
                        stderr_chars += len(payload)
                        stderr_lines_count += 1
            except Empty:
                pass

            if progress_callback and now >= next_heartbeat:
                progress_callback(
                    {
                        "elapsed_seconds": now - started,
                        "stdout_chars": stdout_chars,
                        "stderr_chars": stderr_chars,
                        "stdout_lines": stdout_lines_count,
                        "stderr_lines": stderr_lines_count,
                        "stdout_tail": "".join(stdout_lines[-3:]),
                        "stderr_tail": "".join(stderr_lines[-3:]),
                        "running": proc.poll() is None,
                    }
                )
                next_heartbeat = now + max(1.0, float(heartbeat_seconds))

            if proc.poll() is not None and len(done_streams) >= 2 and q.empty():
                break

        t_out.join(timeout=1.0)
        t_err.join(timeout=1.0)

        return_code = proc.returncode if proc.returncode is not None else 124
        if timed_out:
            stderr_lines.append(f"\n[session_adapter] timeout after {self.timeout_seconds}s\n")
            return_code = 124

        duration = time.time() - started
        return SessionResult(
            return_code=return_code,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
            duration_seconds=duration,
            timed_out=timed_out,
        )
