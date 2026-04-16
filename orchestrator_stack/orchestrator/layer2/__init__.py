"""Layer 2: simulator backends and feature extraction."""

from __future__ import annotations

from typing import Any

__all__ = [
    "TrainingMatrices",
    "observation_matrix",
    "trace_rows_to_training_matrices",
    "AIOpsLabBackend",
    "SimulatorBackend",
    "TraceDrivenTwinBackend",
]


def __getattr__(name: str) -> Any:
    if name in {"TrainingMatrices", "observation_matrix", "trace_rows_to_training_matrices"}:
        from orchestrator.layer2 import feature_extractor

        return getattr(feature_extractor, name)
    if name in {"AIOpsLabBackend", "SimulatorBackend", "TraceDrivenTwinBackend"}:
        from orchestrator.layer2 import simulator

        return getattr(simulator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
