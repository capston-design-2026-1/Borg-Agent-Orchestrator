from __future__ import annotations

import json
import subprocess

from orchestrator.layer1 import kubernetes_actions
from orchestrator.types import ActionKind, AgentAction


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["kubectl"], returncode=returncode, stdout=stdout, stderr=stderr)


def _fake_kubectl(monkeypatch, deployments: list[str]):
    commands: list[list[str]] = []

    def fake_run(kubeconfig, args):
        commands.append(args)
        if args[-2:] == ["-o", "json"]:
            payload = {"items": [{"metadata": {"name": name}} for name in deployments]}
            return _completed(json.dumps(payload))
        return _completed("ok")

    monkeypatch.setattr(kubernetes_actions, "_run_kubectl", fake_run)
    return commands


def test_resource_cap_scales_admission_pressure_down(monkeypatch):
    commands = _fake_kubectl(monkeypatch, ["admission-cap", "safety-throttle"])

    result = kubernetes_actions.execute_live_kubernetes_action(
        AgentAction("AgentC", ActionKind.RESOURCE_CAP, payload={"cpu_cap": 0.85, "mem_cap": 0.85}),
        "/tmp/kubeconfig",
        namespace="borg-orchestrator-exercise",
    )

    assert result["status"] == "applied"
    assert result["matched_deployments"] == ["admission-cap", "safety-throttle"]
    assert any("deployment/admission-cap" in command and "--requests=cpu=50m,memory=32Mi" in command for command in commands)
    assert any(command[-1] == "--replicas=1" and "deployment/admission-cap" in command for command in commands)
    assert any("deployment/comparison-load-generator" in command and "--limits=cpu=60m,memory=48Mi" in command for command in commands)
    assert not any("deployment/safety-throttle" in command and command[-1] == "--replicas=1" for command in commands)


def test_admission_reject_removes_only_exerciser_backlog(monkeypatch):
    commands = _fake_kubectl(monkeypatch, ["admission-queue"])

    result = kubernetes_actions.execute_live_kubernetes_action(
        AgentAction("AgentC", ActionKind.ADMISSION, payload={"decision": "reject"}),
        "/tmp/kubeconfig",
    )

    assert result["status"] == "applied"
    assert result["admission_decision"] == "reject"
    assert any(command[-1] == "--replicas=0" and "deployment/admission-queue" in command for command in commands)
    assert any("deployment/comparison-load-generator" in command for command in commands)


def test_memory_balloon_bounds_all_current_exercise_deployments(monkeypatch):
    commands = _fake_kubectl(monkeypatch, ["moderate-memory"])

    result = kubernetes_actions.execute_live_kubernetes_action(
        AgentAction("AgentB", ActionKind.MEMORY_BALLOON, payload={"mem_scale": 0.75}),
        "/tmp/kubeconfig",
    )

    assert result["status"] == "applied"
    assert any("--requests=cpu=400m,memory=48Mi" in command for command in commands)
    assert any("--limits=cpu=700m,memory=96Mi" in command for command in commands)
    assert any("--requests=cpu=10m,memory=12Mi" in command for command in commands)


def test_no_exercise_deployments_is_safe_noop(monkeypatch):
    _fake_kubectl(monkeypatch, [])

    result = kubernetes_actions.execute_live_kubernetes_action(
        AgentAction("AgentB", ActionKind.DVFS, payload={"clock_scale": 0.65}),
        "/tmp/kubeconfig",
    )

    assert result["status"] == "no_targets"
    assert result["operations"] == []
