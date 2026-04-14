from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from orchestrator.types import Observation


@dataclass(slots=True)
class TrainingMatrices:
    x: np.ndarray
    y_risk: np.ndarray
    y_demand: np.ndarray


def node_feature_vector(obs: Observation, node_id: str) -> list[float]:
    node = next((n for n in obs.nodes if n.node_id == node_id), None)
    if node is None:
        return [0.0, 0.0, 0.0, 0.0, 0.0, float(obs.energy_price)]
    queue_norm = min(1.0, obs.queue_length / max(1.0, len(obs.tasks) + 1.0))
    return [
        float(node.cpu_util),
        float(node.mem_util),
        float(node.disk_util),
        float(node.net_util),
        float(queue_norm),
        float(obs.energy_price),
    ]


def observation_matrix(obs: Observation) -> tuple[np.ndarray, list[str]]:
    node_ids = [n.node_id for n in obs.nodes]
    rows = [node_feature_vector(obs, node_id) for node_id in node_ids]
    if not rows:
        rows = [[0.0, 0.0, 0.0, 0.0, 0.0, float(obs.energy_price)]]
        node_ids = ["unknown-node"]
    return np.asarray(rows, dtype=np.float32), node_ids


def trace_rows_to_training_matrices(rows: list[dict[str, Any]]) -> TrainingMatrices:
    x_rows: list[list[float]] = []
    risk_labels: list[int] = []
    demand_targets: list[float] = []

    for idx, row in enumerate(rows):
        nodes = row.get("nodes", [])
        queue_length = float(row.get("queue_length", 0.0))
        energy_price = float(row.get("energy_price", 0.1))
        next_row = rows[min(idx + 1, len(rows) - 1)]
        next_nodes_by_id = {str(n.get("node_id", "unknown-node")): n for n in next_row.get("nodes", [])}
        p_fail_by_id = row.get("p_fail_scores", {})
        demand_by_id = row.get("demand_projection", {})

        for node in nodes:
            node_id = str(node.get("node_id", "unknown-node"))
            cpu_util = float(node.get("cpu_util", 0.0))
            mem_util = float(node.get("mem_util", 0.0))
            disk_util = float(node.get("disk_util", 0.0))
            net_util = float(node.get("net_util", 0.0))
            queue_norm = min(1.0, queue_length / max(1.0, len(row.get("tasks", [])) + 1.0))
            x_rows.append([cpu_util, mem_util, disk_util, net_util, queue_norm, energy_price])

            fail_signal = float(p_fail_by_id.get(node_id, 0.0))
            death_signal = 1 if row.get("task_death", False) else 0
            overloaded_signal = 1 if (cpu_util > 0.9 or mem_util > 0.9) else 0
            risk_labels.append(int(fail_signal > 0.75 or death_signal or overloaded_signal))

            next_node = next_nodes_by_id.get(node_id, node)
            demand = float(
                demand_by_id.get(
                    node_id,
                    0.5 * float(next_node.get("cpu_util", cpu_util)) + 0.5 * float(next_node.get("mem_util", mem_util)),
                )
            )
            demand_targets.append(max(0.0, min(1.0, demand)))

    if not x_rows:
        x_rows = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.1]]
        risk_labels = [0]
        demand_targets = [0.0]

    return TrainingMatrices(
        x=np.asarray(x_rows, dtype=np.float32),
        y_risk=np.asarray(risk_labels, dtype=np.int32),
        y_demand=np.asarray(demand_targets, dtype=np.float32),
    )
