from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from orchestrator.layer1.kubernetes_exerciser import LABEL
from orchestrator.types import ActionKind, AgentAction


DEFAULT_EXERCISE_NAMESPACE = "borg-orchestrator-exercise"


def _run_kubectl(kubeconfig: str | Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["kubectl", "--kubeconfig", str(kubeconfig), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _kubectl_json(kubeconfig: str | Path, args: list[str]) -> dict[str, Any]:
    completed = _run_kubectl(kubeconfig, [*args, "-o", "json"])
    if completed.returncode != 0:
        return {"items": [], "error": completed.stderr.strip() or completed.stdout.strip()}
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"items": [], "error": "kubectl returned non-JSON output"}


def _deployment_names(kubeconfig: str | Path, namespace: str) -> tuple[list[str], str | None]:
    payload = _kubectl_json(kubeconfig, ["-n", namespace, "get", "deployment", "-l", LABEL])
    names = [
        item.get("metadata", {}).get("name")
        for item in payload.get("items", [])
        if item.get("metadata", {}).get("name")
    ]
    return sorted(str(name) for name in names), payload.get("error")


def _target_deployments(names: list[str], *, prefer_admission: bool = False) -> list[str]:
    if prefer_admission:
        admission = [name for name in names if name.startswith("admission-")]
        if admission:
            return admission
    return list(names)


def _record_operation(
    kubeconfig: str | Path,
    operations: list[dict[str, Any]],
    description: str,
    args: list[str],
) -> None:
    completed = _run_kubectl(kubeconfig, args)
    operations.append(
        {
            "description": description,
            "command": "kubectl " + " ".join(args),
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    )


def _scale(
    kubeconfig: str | Path,
    namespace: str,
    deployments: list[str],
    replicas: int,
    operations: list[dict[str, Any]],
) -> None:
    for deployment in deployments:
        _record_operation(
            kubeconfig,
            operations,
            f"scale {deployment} to {replicas}",
            ["-n", namespace, "scale", f"deployment/{deployment}", f"--replicas={max(0, int(replicas))}"],
        )


def _set_resources(
    kubeconfig: str | Path,
    namespace: str,
    deployments: list[str],
    operations: list[dict[str, Any]],
    *,
    requests: dict[str, str],
    limits: dict[str, str],
) -> None:
    request_arg = ",".join(f"{key}={value}" for key, value in requests.items())
    limit_arg = ",".join(f"{key}={value}" for key, value in limits.items())
    for deployment in deployments:
        _record_operation(
            kubeconfig,
            operations,
            f"set bounded resources on {deployment}",
            [
                "-n",
                namespace,
                "set",
                "resources",
                f"deployment/{deployment}",
                f"--requests={request_arg}",
                f"--limits={limit_arg}",
            ],
        )


def _rollout_restart(
    kubeconfig: str | Path,
    namespace: str,
    deployments: list[str],
    operations: list[dict[str, Any]],
) -> None:
    for deployment in deployments:
        _record_operation(
            kubeconfig,
            operations,
            f"restart {deployment} to reschedule controlled work",
            ["-n", namespace, "rollout", "restart", f"deployment/{deployment}"],
        )


def execute_live_kubernetes_action(
    action: AgentAction,
    kubeconfig: str | Path,
    *,
    namespace: str = DEFAULT_EXERCISE_NAMESPACE,
) -> dict[str, Any]:
    """Apply a selected Referee action to the live experimental exercise namespace.

    The executor is intentionally narrow: it only touches deployments created by the
    orchestrator exerciser label in the configured namespace. Mirrored baseline
    stimulus is left untouched so HPA/Karpenter and Agent A/B/C remain separate
    controller responses to the same external fault/load injection.
    """

    names, discovery_error = _deployment_names(kubeconfig, namespace)
    operations: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "status": "observed",
        "namespace": namespace,
        "agent": action.agent_name,
        "kind": action.kind.value,
        "target": action.target,
        "payload": dict(action.payload),
        "matched_deployments": names,
        "operations": operations,
    }
    if discovery_error:
        result["status"] = "error"
        result["error"] = discovery_error
        return result
    if not names or action.kind == ActionKind.NOOP:
        result["status"] = "no_targets" if not names else "noop"
        return result

    if action.kind == ActionKind.RESOURCE_CAP:
        targets = _target_deployments(names, prefer_admission=True)
        _set_resources(
            kubeconfig,
            namespace,
            targets,
            operations,
            requests={"cpu": "50m", "memory": "32Mi"},
            limits={"cpu": "100m", "memory": "64Mi"},
        )
        _scale(kubeconfig, namespace, targets, 1, operations)
    elif action.kind == ActionKind.ADMISSION:
        decision = str(action.payload.get("decision", "admit"))
        targets = _target_deployments(names, prefer_admission=True)
        replicas_by_decision = {"reject": 0, "deprioritize": 6, "queue": 12, "admit": 1}
        if decision in replicas_by_decision:
            _scale(kubeconfig, namespace, targets, replicas_by_decision[decision], operations)
        result["admission_decision"] = decision
    elif action.kind == ActionKind.POWER_STATE:
        state = str(action.payload.get("state", "on"))
        if state in {"sleep", "off"}:
            _scale(kubeconfig, namespace, names, 0, operations)
        elif state == "on":
            _scale(kubeconfig, namespace, names, 1, operations)
        result["power_state"] = state
    elif action.kind == ActionKind.DVFS:
        _set_resources(
            kubeconfig,
            namespace,
            names,
            operations,
            requests={"cpu": "250m", "memory": "96Mi"},
            limits={"cpu": "500m", "memory": "192Mi"},
        )
    elif action.kind == ActionKind.MEMORY_BALLOON:
        _set_resources(
            kubeconfig,
            namespace,
            names,
            operations,
            requests={"cpu": "400m", "memory": "48Mi"},
            limits={"cpu": "700m", "memory": "96Mi"},
        )
    elif action.kind == ActionKind.THROTTLE:
        _set_resources(
            kubeconfig,
            namespace,
            names,
            operations,
            requests={"cpu": "250m", "memory": "96Mi"},
            limits={"cpu": "500m", "memory": "192Mi"},
        )
    elif action.kind == ActionKind.MIGRATE:
        _rollout_restart(kubeconfig, namespace, names, operations)
    elif action.kind == ActionKind.REPLICATE:
        _scale(kubeconfig, namespace, names, 2, operations)
        _set_resources(
            kubeconfig,
            namespace,
            names,
            operations,
            requests={"cpu": "200m", "memory": "96Mi"},
            limits={"cpu": "500m", "memory": "192Mi"},
        )
    else:
        result["status"] = "unsupported"
        return result

    failed = [operation for operation in operations if operation.get("returncode") != 0]
    result["status"] = "error" if failed else "applied"
    if failed:
        result["error"] = "; ".join(operation.get("stderr") or operation.get("stdout") or "unknown" for operation in failed)
    return result
