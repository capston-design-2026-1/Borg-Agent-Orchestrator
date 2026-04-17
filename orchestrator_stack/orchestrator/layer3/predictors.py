from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover
    from orchestrator import array_compat as np

try:
    import xgboost as xgb
except Exception:  # pragma: no cover
    xgb = None

from orchestrator.layer2.feature_extractor import observation_matrix, trace_rows_to_training_matrices
from orchestrator.types import Observation


class SafetyRiskForecast:
    def __init__(self, predictor: Any):
        self.predictor = predictor

    @classmethod
    def load(cls, path: str | Path) -> "SafetyRiskForecast":
        if xgb is not None:
            booster = xgb.Booster()
            booster.load_model(str(path))
            return cls(booster)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(_FallbackRiskModel.from_payload(payload))

    def predict(self, obs: Observation) -> dict[str, float]:
        x, node_ids = observation_matrix(obs)
        preds = _predict_values(self.predictor, x)
        return {node_id: float(pred) for node_id, pred in zip(node_ids, preds, strict=False)}


class ResourceDemandForecast:
    def __init__(self, predictor: Any):
        self.predictor = predictor

    @classmethod
    def load(cls, path: str | Path) -> "ResourceDemandForecast":
        if xgb is not None:
            booster = xgb.Booster()
            booster.load_model(str(path))
            return cls(booster)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(_FallbackDemandModel.from_payload(payload))

    def predict(self, obs: Observation) -> dict[str, float]:
        x, node_ids = observation_matrix(obs)
        preds = _predict_values(self.predictor, x)
        return {node_id: max(0.0, float(pred)) for node_id, pred in zip(node_ids, preds, strict=False)}


def train_safety_model(x: np.ndarray, y: np.ndarray, out_path: str | Path) -> Path:
    if xgb is None:
        return _train_fallback_risk_model(x, y, out_path)

    dtrain = xgb.DMatrix(x, label=y)
    params = {
        "max_depth": 6,
        "eta": 0.06,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
    }
    booster = xgb.train(params=params, dtrain=dtrain, num_boost_round=300)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out))
    return out


def train_demand_model(x: np.ndarray, y: np.ndarray, out_path: str | Path) -> Path:
    if xgb is None:
        return _train_fallback_demand_model(x, y, out_path)

    dtrain = xgb.DMatrix(x, label=y)
    params = {
        "max_depth": 6,
        "eta": 0.06,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "reg:squarederror",
        "tree_method": "hist",
    }
    booster = xgb.train(params=params, dtrain=dtrain, num_boost_round=300)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out))
    return out


def train_models_from_trace(rows: list[dict], risk_out: str | Path, demand_out: str | Path) -> tuple[Path, Path]:
    matrices = trace_rows_to_training_matrices(rows)
    risk_path = train_safety_model(matrices.x, matrices.y_risk, risk_out)
    demand_path = train_demand_model(matrices.x, matrices.y_demand, demand_out)
    return risk_path, demand_path


def _predict_values(model: Any, rows: Any) -> list[float]:
    if xgb is not None and hasattr(model, "predict"):
        dmat = xgb.DMatrix(rows)
        return [float(value) for value in model.predict(dmat)]
    normalized_rows = rows.tolist() if hasattr(rows, "tolist") else rows
    return [float(model.predict_row(row)) for row in normalized_rows]


class _FallbackRiskModel:
    def __init__(self, threshold: float, margin: float):
        self.threshold = threshold
        self.margin = max(0.05, margin)

    def predict_row(self, row: list[float]) -> float:
        score = _risk_score(row)
        return max(0.0, min(1.0, 0.5 + ((score - self.threshold) / self.margin) * 0.5))

    def to_payload(self) -> dict[str, float | str]:
        return {"model_type": "fallback_risk", "threshold": self.threshold, "margin": self.margin}

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_FallbackRiskModel":
        return cls(float(payload.get("threshold", 0.5)), float(payload.get("margin", 0.1)))


class _FallbackDemandModel:
    def __init__(self, scale: float, bias: float):
        self.scale = scale
        self.bias = bias

    def predict_row(self, row: list[float]) -> float:
        score = _demand_score(row)
        return max(0.0, min(1.0, self.bias + (score * self.scale)))

    def to_payload(self) -> dict[str, float | str]:
        return {"model_type": "fallback_demand", "scale": self.scale, "bias": self.bias}

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_FallbackDemandModel":
        return cls(float(payload.get("scale", 1.0)), float(payload.get("bias", 0.0)))


def _train_fallback_risk_model(x: Any, y: Any, out_path: str | Path) -> Path:
    rows = x.tolist() if hasattr(x, "tolist") else x
    labels = y.tolist() if hasattr(y, "tolist") else y
    positives = [_risk_score(row) for row, label in zip(rows, labels, strict=False) if int(label) == 1]
    negatives = [_risk_score(row) for row, label in zip(rows, labels, strict=False) if int(label) == 0]
    if positives and negatives:
        threshold = (sum(positives) / len(positives) + sum(negatives) / len(negatives)) / 2.0
        margin = abs((sum(positives) / len(positives)) - (sum(negatives) / len(negatives))) or 0.1
    elif positives:
        threshold = sum(positives) / len(positives)
        margin = 0.1
    else:
        threshold = 0.5
        margin = 0.1
    model = _FallbackRiskModel(threshold=threshold, margin=margin)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model.to_payload(), indent=2), encoding="utf-8")
    return out


def _train_fallback_demand_model(x: Any, y: Any, out_path: str | Path) -> Path:
    rows = x.tolist() if hasattr(x, "tolist") else x
    targets = y.tolist() if hasattr(y, "tolist") else y
    scores = [_demand_score(row) for row in rows]
    avg_score = sum(scores) / max(1, len(scores))
    avg_target = sum(float(value) for value in targets) / max(1, len(targets))
    scale = 1.0 if avg_score <= 0 else avg_target / avg_score
    model = _FallbackDemandModel(scale=scale, bias=0.0)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model.to_payload(), indent=2), encoding="utf-8")
    return out


def _risk_score(row: list[float]) -> float:
    cpu, mem, _disk, _net, task_pressure, queue_pressure, _energy, power_on = row
    return (0.4 * float(cpu)) + (0.4 * float(mem)) + (0.1 * float(task_pressure)) + (0.1 * float(queue_pressure)) + (
        0.05 * (1.0 - float(power_on))
    )


def _demand_score(row: list[float]) -> float:
    cpu, mem, _disk, _net, task_pressure, queue_pressure, _energy, _power_on = row
    return (0.45 * float(cpu)) + (0.35 * float(mem)) + (0.1 * float(task_pressure)) + (0.1 * float(queue_pressure))
