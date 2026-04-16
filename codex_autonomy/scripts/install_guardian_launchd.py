from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _plist_content(label: str, python_bin: Path, script_path: Path, config_path: Path, log_dir: Path) -> str:
    stdout_log = (log_dir / "guardian.launchd.stdout.log").resolve()
    stderr_log = (log_dir / "guardian.launchd.stderr.log").resolve()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_bin}</string>
    <string>{script_path}</string>
    <string>--config</string>
    <string>{config_path}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>{config_path.parents[2]}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>{stdout_log}</string>
  <key>StandardErrorPath</key>
  <string>{stderr_log}</string>
</dict>
</plist>
"""


def _supports_yaml(python_bin: Path) -> bool:
    probe = subprocess.run(
        [str(python_bin), "-c", "import yaml"],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.returncode == 0


def _resolve_python_bin(repo_root: Path) -> Path:
    candidates: list[Path] = []
    repo_venv = (repo_root / ".venv/bin/python").absolute()
    candidates.append(repo_venv)
    current = Path(sys.executable).absolute()
    if current not in candidates:
        candidates.append(current)

    for candidate in candidates:
        if not candidate.exists() or not os.access(candidate, os.X_OK):
            continue
        if _supports_yaml(candidate):
            return candidate

    attempted = ", ".join(str(path) for path in candidates)
    raise SystemExit(
        "no usable python interpreter found for guardian launchd install; "
        f"expected one of [{attempted}] to be executable and import PyYAML"
    )


def _run(args: list[str]) -> None:
    subprocess.run(args, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install launchd service for codex autonomy guardian")
    parser.add_argument("--config", required=True)
    parser.add_argument("--label", default="com.borg.codex.autonomy.guardian")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    python_bin = _resolve_python_bin(repo_root)
    script_path = (repo_root / "codex_autonomy/scripts/run_guardian.py").resolve()
    config_path = Path(args.config).resolve()
    log_dir = (repo_root / "codex_autonomy/runtime").resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    launch_agents = Path.home() / "Library/LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / f"{args.label}.plist"
    plist_path.write_text(_plist_content(args.label, python_bin, script_path, config_path, log_dir), encoding="utf-8")

    uid = str(os.getuid())
    _run(["launchctl", "bootout", f"gui/{uid}", str(plist_path)])
    _run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)])
    _run(["launchctl", "enable", f"gui/{uid}/{args.label}"])
    _run(["launchctl", "kickstart", "-k", f"gui/{uid}/{args.label}"])

    print(f"installed: {plist_path}")
    print(f"label: {args.label}")


if __name__ == "__main__":
    main()
