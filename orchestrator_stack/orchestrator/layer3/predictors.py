from __future__ import annotations

from pathlib import Path

import numpy as np
import xgboost as xgb

from orchestrator.layer2.feature_extractor import observation_matrix, trace_rows_to_training_matrices
from orchestrator.types import Observation


class SafetyRiskForecast:
    def __init__(self, booster: xgb.Booster):
        self.booster = booster

    @classmethod
    def load(cls, path: str | Path) -> "SafetyRiskForecast":
        booster = xgb.Booster()
        booster.load_model(str(path))
        return cls(booster)

    def predict(self, obs: Observation) -> dict[str, float]:
        x, node_ids = observation_matrix(obs)
        dmat = xgb.DMatrix(x)
        preds = self.booster.predict(dmat)
        return {node_id: float(pred) for node_id, pred in zip(node_ids, preds, strict=False)}


class ResourceDemandForecast:
    def __init__(self, booster: xgb.Booster):
        self.booster = booster

    @classmethod
    def load(cls, path: str | Path) -> "ResourceDemandForecast":
        booster = xgb.Booster()
        booster.load_model(str(path))
        return cls(booster)

    def predict(self, obs: Observation) -> dict[str, float]:
        x, node_ids = observation_matrix(obs)
        dmat = xgb.DMatrix(x)
        preds = self.booster.predict(dmat)
        return {node_id: max(0.0, float(pred)) for node_id, pred in zip(node_ids, preds, strict=False)}


def train_safety_model(x: np.ndarray, y: np.ndarray, out_path: str | Path) -> Path:
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
