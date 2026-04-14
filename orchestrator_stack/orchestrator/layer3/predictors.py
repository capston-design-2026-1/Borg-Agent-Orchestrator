from __future__ import annotations

from pathlib import Path

import numpy as np
import xgboost as xgb

from orchestrator.types import Observation


def _obs_to_matrix(obs: Observation) -> np.ndarray:
    rows = [[node.cpu_util, node.mem_util, node.disk_util, node.net_util] for node in obs.nodes]
    if not rows:
        rows = [[0.0, 0.0, 0.0, 0.0]]
    return np.asarray(rows, dtype=np.float32)


class SafetyRiskForecast:
    def __init__(self, booster: xgb.Booster):
        self.booster = booster

    @classmethod
    def load(cls, path: str | Path) -> "SafetyRiskForecast":
        booster = xgb.Booster()
        booster.load_model(str(path))
        return cls(booster)

    def predict(self, obs: Observation) -> dict[str, float]:
        x = _obs_to_matrix(obs)
        dmat = xgb.DMatrix(x)
        preds = self.booster.predict(dmat)
        return {node.node_id: float(pred) for node, pred in zip(obs.nodes, preds, strict=False)}


class ResourceDemandForecast:
    def __init__(self, booster: xgb.Booster):
        self.booster = booster

    @classmethod
    def load(cls, path: str | Path) -> "ResourceDemandForecast":
        booster = xgb.Booster()
        booster.load_model(str(path))
        return cls(booster)

    def predict(self, obs: Observation) -> dict[str, float]:
        x = _obs_to_matrix(obs)
        dmat = xgb.DMatrix(x)
        preds = self.booster.predict(dmat)
        return {node.node_id: max(0.0, float(pred)) for node, pred in zip(obs.nodes, preds, strict=False)}


def train_safety_model(x: np.ndarray, y: np.ndarray, out_path: str | Path) -> None:
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
    booster.save_model(str(out_path))


def train_demand_model(x: np.ndarray, y: np.ndarray, out_path: str | Path) -> None:
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
    booster.save_model(str(out_path))
