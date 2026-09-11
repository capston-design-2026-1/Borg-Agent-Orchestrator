from __future__ import annotations

import json
import math
import os
import hashlib
import re
from pathlib import Path

import numpy as np
import polars as pl
from xgboost import XGBClassifier
from sklearn.metrics import average_precision_score

from src.advanced_xgboost.features import ADVANCED_FEATURE_COLUMNS, MISSINGNESS_FLAG_COLUMNS, target_column_name
from src.advanced_xgboost.settings import model_dir, report_dir


DEFAULT_VALID_FRACTION = 0.2
DEFAULT_MODEL_NAME = "xgboost_failure_risk"
DEFAULT_MAX_TRAIN_ROWS = 8_000_000
DEFAULT_MAX_VALID_ROWS = 2_000_000
SAMPLING_BUCKETS = 1_000_000
MODEL_FEATURE_COLUMNS = ADVANCED_FEATURE_COLUMNS + MISSINGNESS_FLAG_COLUMNS


def validation_fraction() -> float:
    raw = os.environ.get("BORG_VALID_FRACTION")
    if not raw:
        return DEFAULT_VALID_FRACTION
    return float(raw)


def temporal_splits(frame: pl.LazyFrame, target_column: str, valid_fraction: float | None = None):
    """Reserve the final interval before tuning and purge overlapping label horizons."""
    match = re.fullmatch(r"target_failure_([1-9][0-9]*)m", target_column)
    if not match:
        raise ValueError("Target must encode a positive failure horizon in minutes")
    required = {"causal_schema_version", "event_observation_end_time"}
    if required - set(frame.collect_schema().names()):
        raise ValueError("Rebuild feature data using causal schema v2 before training")
    versions = frame.select("causal_schema_version").unique().collect().to_series().to_list()
    if versions != [2]:
        raise ValueError("Only causal schema v2 feature data can be trained")
    valid_fraction = validation_fraction() if valid_fraction is None else valid_fraction
    test_fraction = float(os.environ.get("BORG_TEST_FRACTION", "0.2"))
    if not (0 < valid_fraction < 1 and 0 < test_fraction < 1 and valid_fraction + test_fraction < 1):
        raise ValueError("Validation and test fractions must be positive and sum to less than one")
    valid_start = split_time_for_scan(frame, valid_fraction + test_fraction)
    test_start = split_time_for_scan(frame, test_fraction)
    if valid_start >= test_start:
        raise ValueError("Not enough distinct timestamps for train/validation/test intervals")
    horizon_us = int(match[1]) * 60 * 1_000_000
    labeled = frame.filter(pl.col(target_column).is_not_null()
                           & (pl.col("end_time") + horizon_us <= pl.col("event_observation_end_time")))
    train = labeled.filter(pl.col("end_time") + horizon_us < valid_start)
    valid = labeled.filter((pl.col("end_time") >= valid_start)
                           & (pl.col("end_time") + horizon_us < test_start))
    test = labeled.filter(pl.col("end_time") >= test_start)
    return train, valid, test, {"validation_start": valid_start, "test_start": test_start,
                                "horizon_us": horizon_us, "causal_schema_version": 2}


def model_name() -> str:
    return (
        os.environ.get("BORG_XGBOOST_MODEL_NAME")
        or os.environ.get("BORG_XGB_MODEL_NAME")
        or DEFAULT_MODEL_NAME
    ).strip()


def model_name_for_target(target_column: str) -> str:
    return f"{model_name()}_{target_column}"


def model_params() -> dict[str, float | int | str]:
    params: dict[str, float | int | str] = {
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
    raw_early_stopping = os.environ.get("BORG_XGB_EARLY_STOPPING_ROUNDS")
    if raw_early_stopping:
        params["early_stopping_rounds"] = int(raw_early_stopping)
    return params


def verbose_eval() -> int | bool:
    raw = os.environ.get("BORG_XGB_VERBOSE_EVAL")
    if not raw:
        return False
    if raw.lower() in {"true", "yes", "on"}:
        return True
    return max(1, int(raw))


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


def max_train_rows() -> int:
    raw = os.environ.get("BORG_XGB_MAX_TRAIN_ROWS")
    if not raw:
        return DEFAULT_MAX_TRAIN_ROWS
    return max(1, int(raw))


def max_valid_rows() -> int:
    raw = os.environ.get("BORG_XGB_MAX_VALID_ROWS")
    if not raw:
        return DEFAULT_MAX_VALID_ROWS
    return max(1, int(raw))


def sampling_seed() -> int:
    raw = os.environ.get("BORG_XGB_SAMPLING_SEED")
    if not raw:
        return int(os.environ.get("BORG_XGB_RANDOM_STATE", "42"))
    return int(raw)


def split_time_for_scan(frame: pl.LazyFrame, valid_fraction: float) -> int:
    split_time = (
        frame
        .select(pl.col("end_time").quantile(1.0 - valid_fraction).alias("split_time"))
        .collect()
        .item()
    )
    return int(split_time)


def prepare_matrix(frame: pl.DataFrame, target_column: str) -> tuple[list[list[float]], list[int]]:
    matrix_frame = frame.with_columns(
        [
            (
                pl.col(column)
                .cast(pl.Float64, strict=False)
                .fill_null(float("nan"))
                .alias(column)
            )
            for column in MODEL_FEATURE_COLUMNS
        ]
    )
    x = matrix_frame.select(list(MODEL_FEATURE_COLUMNS)).to_numpy()
    x = np.asarray(x, dtype=np.float32)
    y = matrix_frame.get_column(target_column).cast(pl.Int64).to_list()
    return x, y


def average_precision(prediction_frame: pl.DataFrame, target_column: str) -> float | None:
    if prediction_frame.is_empty() or not prediction_frame.get_column(target_column).any():
        return None
    # Threshold-based AP handles tied scores without depending on row order.
    return float(average_precision_score(prediction_frame.get_column(target_column).to_numpy(),
                                         prediction_frame.get_column("risk_score").to_numpy()))


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


def row_id_expr() -> pl.Expr:
    return pl.struct(["cluster_id", "collection_id", "instance_index", "start_time", "end_time"]).hash(
        seed=sampling_seed()
    )


def sampled_negative_filter(keep_fraction: float) -> pl.Expr:
    if keep_fraction <= 0.0:
        return pl.lit(False)
    if keep_fraction >= 1.0:
        return pl.lit(True)
    keep_threshold = max(1, int(keep_fraction * SAMPLING_BUCKETS))
    return row_id_expr().mod(SAMPLING_BUCKETS) < keep_threshold


def split_stats(frame: pl.LazyFrame, target_column: str) -> dict[str, int]:
    stats = frame.select(
        [
            pl.len().alias("rows"),
            pl.col(target_column).cast(pl.Int64).sum().fill_null(0).alias("positives"),
        ]
    ).collect().to_dicts()[0]
    rows = int(stats["rows"])
    positives = int(stats["positives"])
    return {
        "rows": rows,
        "positives": positives,
        "negatives": rows - positives,
    }


def negative_keep_fraction(rows: int, positives: int, max_rows: int) -> float:
    negatives = rows - positives
    if negatives <= 0:
        return 1.0
    remaining_budget = max_rows - positives
    if remaining_budget <= 0:
        return 0.0
    return min(1.0, remaining_budget / negatives)


def sample_split(
    frame: pl.LazyFrame,
    target_column: str,
    max_rows: int,
) -> tuple[pl.DataFrame, dict[str, int | float]]:
    stats = split_stats(frame, target_column)
    keep_fraction = negative_keep_fraction(stats["rows"], stats["positives"], max_rows)
    sampled = (
        frame
        .filter(pl.col(target_column) | sampled_negative_filter(keep_fraction))
        .collect(engine="streaming")
    )
    sampled_stats = {
        "rows": sampled.height,
        "positives": sampled.filter(pl.col(target_column)).height,
        "negatives": sampled.filter(~pl.col(target_column)).height,
        "negative_keep_fraction": keep_fraction,
    }
    sampled_stats.update(
        {
            "source_rows": stats["rows"],
            "source_positives": stats["positives"],
            "source_negatives": stats["negatives"],
        }
    )
    return sampled, sampled_stats


def sample_natural_split(frame: pl.LazyFrame, target_column: str, max_rows: int):
    """Bound memory without selecting on the outcome label."""
    stats = split_stats(frame, target_column)
    sampled = frame
    if stats["rows"] > max_rows:
        sampled = frame.with_columns(row_id_expr().alias("_sample_key")).sort(
            ["_sample_key", "cluster_id", "collection_id", "instance_index", "start_time", "end_time"]
        ).head(max_rows).drop("_sample_key")
    result = sampled.collect(engine="streaming")
    positives = result.filter(pl.col(target_column)).height
    negatives = result.height - positives
    return result, {
        "rows": result.height, "positives": positives, "negatives": negatives,
        "source_rows": stats["rows"], "source_positives": stats["positives"],
        "source_negatives": stats["negatives"],
        "negative_keep_fraction": negatives / stats["negatives"] if stats["negatives"] else 1.0,
        "sampling_method": "all_rows" if stats["rows"] <= max_rows else "label_independent_hash",
    }


def dataset_fingerprint(frame: pl.LazyFrame, target_column: str) -> str:
    """Order-independent dataset identity for detecting accidental changes, not authentication."""
    columns = ["cluster_id", "collection_id", "instance_index", "start_time", "end_time",
               "causal_schema_version", "event_observation_end_time", *MODEL_FEATURE_COLUMNS, target_column]
    identity = frame.select(
        pl.len().alias("rows"),
        *[pl.struct(columns).hash(seed=seed).sum().alias(f"content_{seed}") for seed in (42, 1234)],
    ).collect().to_dicts()[0]
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def train_and_evaluate(feature_scan: pl.LazyFrame, target_column: str) -> dict[str, int | float | str]:
    if (model_output_dir(target_column) / "holdout_metrics.json").exists():
        raise FileExistsError("This model has consumed its final test; preserve it and choose a new study/test set")
    train_scan, valid_scan, _, split_contract = temporal_splits(feature_scan, target_column)
    split_time = split_contract["validation_start"]
    selected_columns = [
        "cluster_id",
        "collection_id",
        "instance_index",
        "machine_id",
        "start_time",
        "end_time",
        *MODEL_FEATURE_COLUMNS,
        target_column,
    ]
    train_scan = train_scan.select(selected_columns).with_columns(pl.col(target_column).cast(pl.Boolean))
    valid_scan = valid_scan.select(selected_columns).with_columns(pl.col(target_column).cast(pl.Boolean))
    train_df, train_stats = sample_split(train_scan, target_column, max_train_rows())
    valid_df, valid_stats = sample_natural_split(valid_scan, target_column, max_valid_rows())
    if train_df.is_empty() or valid_df.is_empty():
        raise ValueError("Insufficient mature labels after temporal purging; verify coverage and time span")
    if train_stats["positives"] == 0 or train_stats["negatives"] == 0:
        raise ValueError("Training requires both failure and nonfailure examples")
    train_x, train_y = prepare_matrix(train_df, target_column)
    valid_x, valid_y = prepare_matrix(valid_df, target_column)

    params = model_params()
    params["scale_pos_weight"] = compute_scale_pos_weight(train_y)

    model = XGBClassifier(**params)
    fit_kwargs: dict[str, object] = {}
    if "early_stopping_rounds" in params:
        fit_kwargs["eval_set"] = [(valid_x, valid_y)]
        fit_kwargs["verbose"] = verbose_eval()
    model.fit(train_x, train_y, **fit_kwargs)
    model.get_booster().save_model(model_path(target_column))
    contract = {**split_contract, "target_column": target_column,
                "feature_columns": list(MODEL_FEATURE_COLUMNS), "sampling_seed": sampling_seed(),
                "dataset_fingerprint": dataset_fingerprint(feature_scan, target_column),
                "model_sha256": hashlib.sha256(model_path(target_column).read_bytes()).hexdigest()}
    (model_output_dir(target_column) / "evaluation_contract.json").write_text(json.dumps(contract, indent=2))
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
            zip(MODEL_FEATURE_COLUMNS, model.feature_importances_, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
    feature_importance_path(target_column).write_text(json.dumps(importances, indent=2))
    config_path(target_column).write_text(json.dumps(params, indent=2))

    one_percent = max(1, math.ceil(prediction_frame.height * 0.01))
    point_one_percent = max(1, math.ceil(prediction_frame.height * 0.001))
    metrics = {
        "status": "evaluated" if valid_stats["positives"] else "insufficient_positive_evidence",
        "evaluation_partition": "development_validation",
        "final_test_evaluated": False,
        "split_contract": split_contract,
        "validation_sampling_method": valid_stats["sampling_method"],
        "causal_schema_version": 2,
        "model_name": model_name(),
        "target_column": target_column,
        "source_train_rows": train_stats["source_rows"],
        "source_validation_rows": valid_stats["source_rows"],
        "sampled_train_rows": train_df.height,
        "sampled_validation_rows": valid_df.height,
        "train_rows": train_df.height,
        "validation_rows": valid_df.height,
        "validation_positive_rows": prediction_frame.filter(pl.col(target_column)).height,
        "validation_positive_rate": (
            prediction_frame.filter(pl.col(target_column)).height / prediction_frame.height
            if prediction_frame.height else 0.0
        ),
        "train_positive_rows": sum(train_y),
        "sampled_train_positive_rows": train_stats["positives"],
        "sampled_validation_positive_rows": valid_stats["positives"],
        "train_negative_keep_fraction": train_stats["negative_keep_fraction"],
        "validation_negative_keep_fraction": valid_stats["negative_keep_fraction"],
        "best_iteration": getattr(model, "best_iteration", None),
        "best_score": (
            float(model.best_score)
            if getattr(model, "best_score", None) is not None
            else None
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


def evaluate_frozen_holdout(feature_scan: pl.LazyFrame, target_column: str) -> dict:
    """Evaluate an already selected model once; never fit or select it on test outcomes."""
    output = model_output_dir(target_column)
    contract = json.loads((output / "evaluation_contract.json").read_text())
    if contract["target_column"] != target_column or contract["feature_columns"] != list(MODEL_FEATURE_COLUMNS):
        raise ValueError("Frozen model feature contract mismatch")
    if hashlib.sha256(model_path(target_column).read_bytes()).hexdigest() != contract["model_sha256"]:
        raise ValueError("Model changed after its evaluation contract was frozen")
    if (output / "holdout_metrics.json").exists():
        raise FileExistsError("Holdout already evaluated; preserve its result and use a new independent test set")
    if "causal_schema_version" not in feature_scan.collect_schema().names():
        raise ValueError("Holdout requires causal schema v2")
    if feature_scan.select("causal_schema_version").unique().collect().to_series().to_list() != [2]:
        raise ValueError("Holdout causal schema mismatch")
    if dataset_fingerprint(feature_scan, target_column) != contract["dataset_fingerprint"]:
        raise ValueError("Dataset changed after the evaluation contract was frozen")
    test_scan = feature_scan.filter((pl.col("end_time") >= contract["test_start"])
        & (pl.col("end_time") + contract["horizon_us"] <= pl.col("event_observation_end_time"))
        & pl.col(target_column).is_not_null())
    count = test_scan.select(pl.len()).collect().item()
    limit = int(os.environ.get("BORG_XGB_MAX_TEST_ROWS", str(DEFAULT_MAX_VALID_ROWS)))
    if not 0 < count <= limit:
        raise ValueError(f"Holdout has {count} rows; require mature data and BORG_XGB_MAX_TEST_ROWS >= {count}")
    frame = test_scan.collect(engine="streaming")
    model = XGBClassifier()
    model.load_model(model_path(target_column))
    x, _ = prepare_matrix(frame, target_column)
    predictions = frame.select("cluster_id", "collection_id", "instance_index", "start_time", "end_time",
                               target_column).with_columns(pl.Series("risk_score", model.predict_proba(x)[:, 1]))
    ap = average_precision(predictions, target_column)
    result = {"status": "evaluated" if ap is not None else "insufficient_positive_evidence",
              "evaluation_partition": "frozen_test", "rows": count,
              "positive_rows": predictions.filter(pl.col(target_column)).height,
              "average_precision": ap, "contract": contract, "sampling_method": "all_rows"}
    with (output / "holdout_metrics.json").open("x") as handle:
        json.dump(result, handle, indent=2)
    predictions.write_parquet(output / "holdout_predictions.parquet")
    return result
