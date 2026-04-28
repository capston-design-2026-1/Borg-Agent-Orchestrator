"""Layer 3: predictive models (risk + demand)."""

from orchestrator.layer3.diagnostics import calibration_bins, diagnose_xgboost_model, optimize_binary_threshold
from orchestrator.layer3.predictors import (
    PredictorBackedBackend,
    ResourceDemandForecast,
    SafetyRiskForecast,
    enrich_observation_with_predictions,
    train_demand_model,
    train_models_from_trace,
    train_safety_model,
)

__all__ = [
    "PredictorBackedBackend",
    "ResourceDemandForecast",
    "SafetyRiskForecast",
    "calibration_bins",
    "diagnose_xgboost_model",
    "enrich_observation_with_predictions",
    "optimize_binary_threshold",
    "train_demand_model",
    "train_models_from_trace",
    "train_safety_model",
]
