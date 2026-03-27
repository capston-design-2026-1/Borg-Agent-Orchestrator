from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import polars as pl
from xgboost import XGBClassifier

from src.advanced_xgboost.features import ADVANCED_FEATURE_COLUMNS, MISSINGNESS_FLAG_COLUMNS, target_column_name
from src.advanced_xgboost.settings import model_dir, report_dir


DEFAULT_VALID_FRACTION = 0.2
DEFAULT_MODEL_NAME = "xgboost_failure_risk"


def validation_fraction() -> float:
    raw = os.environ.get("BORG_VALID_FRACTION")
    if not raw:
        return DEFAULT_VALID_FRACTION
    return float(raw)


def model_name() -> str:
    return os.environ.get("BORG_XGBOOST_MODEL_NAME", DEFAULT_MODEL_NAME).strip()


def model_name_for_target(target_column: str) -> str:
    return f"{model_name()}_{target_column}"


def model_params() -> dict[str, float | int | str]:
    return {
        "n_estimators": int(os.environ.get("BORG_XGB_N_ESTIMATORS", "400")),
        "max_depth": int(os.environ.get("BORG_XGB_MAX_DEPTH", "8")),
        "learning_rate": float(os.environ.get("BORG_XGB_LEARNING_RATE", "0.05")),
        "subsample": float(os.environ.get("BORG_XGB_SUBSAMPLE", "0.8")),
        "colsample_bytree": float(os.environ.get("BORG_XGB_COLSAMPLE_BYTREE", "0.8")),
        "min_child_weight": float(os.environ.get("BORG_XGB_MIN_CHILD_WEIGHT", "5")),
        "reg_alpha": float(os.environ.get("BORG_XGB_REG_ALPHA", "0.0")),
        "reg_lambda": float(os.environ.get("BORG_XGB_REG_LAMBDA", "1.0")),
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": os.environ.get("BORG_XGB_TREE_METHOD", "hist"),
        "random_state": int(os.environ.get("BORG_XGB_RANDOM_STATE", "42")),
        "n_jobs": int(os.environ.get("BORG_XGB_N_JOBS", "8")),
    }


def model_output_dir(target_column: str) -> Path:
    path = model_dir() / model_name_for_target(target_column)
    path.mkdir(parents=True, exist_ok=True)
    return path


def metrics_path(target_column: str) -> Path:
    return model_output_dir(target_column) / "metrics.json"


def feature_importance_path(target_column: str) -> Path:
    return model_output_dir(target_column) / "feature_importance.json"


def prediction_path(target_column: str) -> Path:
    return model_output_dir(target_column) / "validation_predictions.parquet"


def config_path(target_column: str) -> Path:
    return model_output_dir(target_column) / "model_config.json"


def model_path(target_column: str) -> Path:
    return model_output_dir(target_column) / "model.json"


def summary_report_path(target_column: str) -> Path:
    report_dir().mkdir(parents=True, exist_ok=True)
    return report_dir() / f"advanced_xgboost_training_summary_{target_column}.json"


def split_by_time(frame: pl.DataFrame, valid_fraction: float) -> tuple[pl.DataFrame, pl.DataFrame, int]:
    split_time = (
        frame
        .select(pl.col("end_time").quantile(1.0 - valid_fraction).alias("split_time"))
        .item()
    )
    train_df = frame.filter(pl.col("end_time") < split_time)
    valid_df = frame.filter(pl.col("end_time") >= split_time)
    return train_df, valid_df, int(split_time)


def prepare_matrix(frame: pl.DataFrame, target_column: str) -> tuple[list[list[float]], list[int]]:
    matrix_frame = frame.with_columns(
        [
            (
                pl.col(column)
                .cast(pl.Float64, strict=False)
                .fill_null(float("nan"))
                .alias(column)
            )
            for column in ADVANCED_FEATURE_COLUMNS + MISSINGNESS_FLAG_COLUMNS
        ]
    )
    x = matrix_frame.select(list(ADVANCED_FEATURE_COLUMNS + MISSINGNESS_FLAG_COLUMNS)).to_numpy()
    x = np.asarray(x, dtype=np.float32)
    y = matrix_frame.get_column(target_column).cast(pl.Int64).to_list()
    return x, y


def average_precision(prediction_frame: pl.DataFrame, target_column: str) -> float:
    ranked = (
        prediction_frame
        .sort("risk_score", descending=True)
        .with_row_index("rank", offset=1)
        .with_columns(
            [
                pl.col(target_column).cast(pl.Int64).cum_sum().alias("true_positives"),
                (pl.col(target_column).cast(pl.Int64).cum_sum() / pl.col("rank")).alias("precision_at_rank"),
            ]
        )
    )
    positives_total = ranked.filter(pl.col(target_column)).height
    if positives_total == 0:
        return 0.0
    ap_sum = ranked.filter(pl.col(target_column)).select(pl.col("precision_at_rank").sum()).item()
    return float(ap_sum) / positives_total if ap_sum is not None else 0.0


def precision_at_k(frame: pl.DataFrame, k: int, target_column: str) -> float:
    top_k = frame.sort("risk_score", descending=True).head(max(1, k))
    positives = top_k.filter(pl.col(target_column)).height
    return positives / top_k.height if top_k.height else 0.0


def recall_at_k(frame: pl.DataFrame, k: int, target_column: str) -> float:
    positives_total = frame.filter(pl.col(target_column)).height
    if positives_total == 0:
        return 0.0
    top_k = frame.sort("risk_score", descending=True).head(max(1, k))
    positives = top_k.filter(pl.col(target_column)).height
    return positives / positives_total


def compute_scale_pos_weight(y: list[int]) -> float:
    positives = sum(y)
    negatives = len(y) - positives
    if positives <= 0:
        return 1.0
    return max(1.0, negatives / positives)


def train_and_evaluate(feature_frame: pl.DataFrame, target_column: str) -> dict[str, int | float | str]:
    train_df, valid_df, split_time = split_by_time(feature_frame, validation_fraction())
    train_x, train_y = prepare_matrix(train_df, target_column)
    valid_x, valid_y = prepare_matrix(valid_df, target_column)

    params = model_params()
    params["scale_pos_weight"] = compute_scale_pos_weight(train_y)

    model = XGBClassifier(**params)
    model.fit(train_x, train_y)
    model.save_model(model_path(target_column))
    valid_scores = model.predict_proba(valid_x)[:, 1].tolist()

    prediction_frame = valid_df.select(
        [
            pl.col("cluster_id"),
            pl.col("collection_id"),
            pl.col("instance_index"),
            pl.col("machine_id"),
            pl.col("start_time"),
            pl.col("end_time"),
            pl.col(target_column),
        ]
    ).with_columns(pl.Series("risk_score", valid_scores))

    prediction_frame.write_parquet(prediction_path(target_column))

    importances = [
        {
            "feature": feature,
            "importance": float(importance),
        }
        for feature, importance in sorted(
            zip(ADVANCED_FEATURE_COLUMNS, model.feature_importances_, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
    feature_importance_path(target_column).write_text(json.dumps(importances, indent=2))
    config_path(target_column).write_text(json.dumps(params, indent=2))

    one_percent = max(1, math.ceil(prediction_frame.height * 0.01))
    point_one_percent = max(1, math.ceil(prediction_frame.height * 0.001))
    metrics = {
        "model_name": model_name(),
        "target_column": target_column,
        "train_rows": train_df.height,
        "validation_rows": valid_df.height,
        "validation_positive_rows": prediction_frame.filter(pl.col(target_column)).height,
        "validation_positive_rate": (
            prediction_frame.filter(pl.col(target_column)).height / prediction_frame.height
            if prediction_frame.height else 0.0
        ),
        "split_time": split_time,
        "average_precision": average_precision(prediction_frame, target_column),
        "precision_at_0_1_percent": precision_at_k(prediction_frame, point_one_percent, target_column),
        "recall_at_0_1_percent": recall_at_k(prediction_frame, point_one_percent, target_column),
        "precision_at_1_percent": precision_at_k(prediction_frame, one_percent, target_column),
        "recall_at_1_percent": recall_at_k(prediction_frame, one_percent, target_column),
    }
    metrics_path(target_column).write_text(json.dumps(metrics, indent=2))
    summary_report_path(target_column).write_text(json.dumps(metrics, indent=2))
    return metrics
