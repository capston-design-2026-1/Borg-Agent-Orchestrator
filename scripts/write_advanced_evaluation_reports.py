from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports"
MODEL_ROOT = Path.home() / "Documents" / "borg_xgboost_workspace" / "models" / "xgboost"
HORIZONS = (5, 15, 30, 45, 60)


def model_dir(minutes: int) -> Path:
    return MODEL_ROOT / f"xgboost_failure_risk_target_failure_{minutes}m"


def metrics(minutes: int) -> dict:
    return json.loads((model_dir(minutes) / "metrics.json").read_text())


def feature_importance(minutes: int) -> list[dict]:
    return json.loads((model_dir(minutes) / "feature_importance.json").read_text())


def top_feature_counter(limit: int = 10) -> Counter[str]:
    counter: Counter[str] = Counter()
    for minutes in HORIZONS:
        for item in feature_importance(minutes)[:limit]:
            counter[item["feature"]] += 1
    return counter


def metrics_rows() -> list[dict]:
    rows = []
    for minutes in HORIZONS:
        row = metrics(minutes)
        row["minutes"] = minutes
        rows.append(row)
    return rows


def render_table(rows: list[dict]) -> str:
    header = "| Horizon | AP | Precision@0.1% | Recall@0.1% | Precision@1% | Recall@1% | Valid Positives | Sampled Valid Rows |"
    separator = "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    body = [
        (
            f"| {row['minutes']}m | {row['average_precision']:.6f} | "
            f"{row['precision_at_0_1_percent']:.6f} | {row['recall_at_0_1_percent']:.6f} | "
            f"{row['precision_at_1_percent']:.6f} | {row['recall_at_1_percent']:.6f} | "
            f"{row['validation_positive_rows']:,} | {row['validation_rows']:,} |"
        )
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def english_report(rows: list[dict]) -> str:
    common_features = top_feature_counter()
    feature_lines = "\n".join(
        f"- `{feature}` appeared in the top-10 list for `{count}` horizon(s)"
        for feature, count in common_features.most_common(12)
    )

    best_ap = max(rows, key=lambda item: item["average_precision"])
    best_recall = max(rows, key=lambda item: item["recall_at_1_percent"])
    worst_ap = min(rows, key=lambda item: item["average_precision"])

    return f"""# Advanced XGBoost Evaluation Report (English)

Generated at `2026-03-31 {datetime.now().strftime('%H:%M')} KST`

## Executive Summary

- All five production horizons (`5m`, `15m`, `30m`, `45m`, `60m`) completed successfully.
- The strongest average precision is at `{best_ap['minutes']}m` with `{best_ap['average_precision']:.6f}`.
- The strongest recall at the operational `1%` alert budget is also at `{best_recall['minutes']}m` with `{best_recall['recall_at_1_percent']:.6f}`.
- Metric quality declines gradually as the prediction window gets longer, which is expected because longer horizons are harder and include more ambiguous pre-failure states.
- Even at `60m`, the model still keeps `precision@1%` above `0.996`, but recall falls from `0.391` at `5m` to `0.233` at `60m`.

## Horizon Comparison

{render_table(rows)}

## Interpretation

- `5m` is the cleanest detection setting. The signal is closest to the terminal event, so separation is strongest and both AP and recall are best.
- `15m` and `30m` remain strong. Precision stays almost unchanged, but recall drops as more uncertain windows enter the positive set.
- `45m` and `60m` show the expected degradation pattern: AP falls and recall drops further, but the model still ranks the highest-risk windows very effectively.
- The ranking quality is unusually strong for every horizon. That is partly a real signal win, but it is also helped by the sampled training/evaluation design keeping all positives while deterministically downsampling negatives.

## Sampling And Evaluation Method

- Source train rows per horizon: about `307.8M`
- Source validation rows per horizon: about `77.0M`
- Sampled train rows per horizon: about `8.0M`
- Sampled validation rows per horizon: about `2.0M`
- All positive rows were retained.
- Negative rows were deterministically sampled by hashed row id.
- Temporal validation was used by splitting on `end_time` rather than random row shuffling.

This design keeps the experiment feasible on a `24 GB` laptop while preserving rare failure examples, but it also means the reported precision values describe a sampled alert population, not the untouched full negative pool.

## Feature Observations

{feature_lines}

The most repeated top features should be treated as the current stable core of the model. In practice these usually reflect a mix of:

- direct resource stress and utilization
- task-local temporal momentum
- local machine aggregation pressure
- recent terminal/failure history
- missingness indicators that mark structurally weak observations

## Remaining Risks

- Clusters `e`, `f`, and `g` produced zero positive labels in the current fixed-shard slice. The current model is therefore learning positive behavior mainly from `b`, `c`, and `d`.
- The evaluation is temporally split, which is good, but it is still drawn from the same shard-selection policy. Generalization to deeper or different shard windows is not yet proven.
- Because negatives are sampled, the current precision values should not be read as the exact production precision under the full raw event stream.
- Longer horizons may be more vulnerable to overfitting if model capacity is increased without stronger regularization or earlier stopping.
- The current report does not yet include calibration curves or cluster-held-out testing, so score calibration and cross-cluster portability are still open questions.

## Recommended Next Tuning Priorities

- Continue the ongoing hyperparameter sweep with early stopping and stronger regularization candidates.
- Check whether deeper shard coverage restores positive labels for `e`, `f`, and `g`.
- Add cluster-level holdout comparisons and calibration analysis.
- Compare the current production configuration against the tuning winner before promoting a new default.

## Reference Artifacts

- Models: `~/Documents/borg_xgboost_workspace/models/xgboost`
- Runtime log: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331041159_advanced_train_resumable.log`
- Handoff summary: `reports/202603310423_advanced_training_completed.md`
"""


def korean_report(rows: list[dict]) -> str:
    common_features = top_feature_counter()
    feature_lines = "\n".join(
        f"- `{feature}` 는 `{count}`개 horizon의 top-10 중요도 목록에 반복적으로 등장했습니다."
        for feature, count in common_features.most_common(12)
    )

    best_ap = max(rows, key=lambda item: item["average_precision"])
    best_recall = max(rows, key=lambda item: item["recall_at_1_percent"])

    return f"""# Advanced XGBoost 평가 보고서 (한국어)

생성 시각 `2026-03-31 {datetime.now().strftime('%H:%M')} KST`

## 핵심 요약

- 운영용 horizon `5m`, `15m`, `30m`, `45m`, `60m` 학습이 모두 완료되었습니다.
- 평균 정밀도(AP)가 가장 높은 horizon은 `{best_ap['minutes']}m` 이며 값은 `{best_ap['average_precision']:.6f}` 입니다.
- 운영 alert budget인 `1%` 기준 재현율이 가장 높은 horizon도 `{best_recall['minutes']}m` 이며 값은 `{best_recall['recall_at_1_percent']:.6f}` 입니다.
- 예측 창이 길어질수록 성능이 점진적으로 하락합니다. 이는 더 긴 horizon일수록 실패 직전 상태와 애매한 중간 상태가 함께 섞이기 때문에 자연스러운 현상입니다.
- 그럼에도 `60m` 에서도 `precision@1%` 는 `0.996` 이상을 유지하고 있습니다.

## Horizon 비교

{render_table(rows)}

## 해석

- `5m` 은 가장 선명한 탐지 구간입니다. 실패 시점과 가장 가까운 구간이므로 분리도가 가장 좋고 AP와 재현율이 모두 최고입니다.
- `15m`, `30m` 구간도 여전히 매우 강합니다. 정밀도는 거의 유지되지만 양성 정의가 넓어지면서 재현율이 점차 낮아집니다.
- `45m`, `60m` 에서는 예상대로 AP와 재현율이 더 떨어집니다. 하지만 상위 위험 순위 구간의 정밀도는 여전히 매우 높습니다.
- 모든 horizon의 ranking 품질이 매우 높게 보이는데, 이는 실제 신호가 강한 부분도 있지만 모든 양성을 유지하고 음성을 결정론적으로 다운샘플링한 평가 설계의 영향도 함께 받습니다.

## 샘플링 및 평가 방식

- horizon별 원본 학습 행 수: 약 `307.8M`
- horizon별 원본 검증 행 수: 약 `77.0M`
- horizon별 샘플링된 학습 행 수: 약 `8.0M`
- horizon별 샘플링된 검증 행 수: 약 `2.0M`
- 양성 데이터는 모두 유지했습니다.
- 음성 데이터는 해시 기반 결정론적 샘플링으로 축소했습니다.
- 검증 분할은 랜덤 셔플이 아니라 `end_time` 기준 시간 분할입니다.

이 방식은 `24 GB` 노트북에서도 학습을 가능하게 만들지만, 현재 precision 수치는 전체 원본 음성 분포를 그대로 통과시킨 운영 환경과 완전히 동일한 의미는 아닙니다.

## 중요 피처 관찰

{feature_lines}

반복적으로 상위에 나타나는 피처들은 현재 모델의 안정적인 핵심 신호로 볼 수 있습니다. 실제로는 보통 다음 범주의 정보가 섞여 있습니다.

- 직접적인 자원 사용량과 utilization
- 태스크 단위의 시간적 변화량
- 머신 단위 집계 부하
- 최근 실패/종료 이력
- 구조적으로 취약한 관측치를 표시하는 missingness indicator

## 남아 있는 리스크

- 현재 fixed-shard slice에서는 `e`, `f`, `g` 클러스터에서 양성 라벨이 전혀 생성되지 않았습니다. 따라서 현재 양성 학습 신호는 사실상 `b`, `c`, `d` 에서만 옵니다.
- 시간 분할 검증은 적절하지만, 여전히 같은 shard 선택 정책 안에서의 평가입니다. 더 깊은 shard 구간이나 다른 기간에 대한 일반화는 아직 검증되지 않았습니다.
- 음성 샘플링이 들어가 있으므로 현재 precision 값은 전체 운영 이벤트 스트림에서의 절대 정밀도로 바로 해석하면 안 됩니다.
- 더 긴 horizon에서는 모델 복잡도를 무리하게 올릴 경우 과적합 위험이 커질 수 있습니다.
- 현재 보고서는 calibration curve, cluster holdout, 완전한 교차-클러스터 일반화 검증까지는 포함하지 않습니다.

## 다음 권장 작업

- 현재 진행 중인 early stopping 기반 하이퍼파라미터 탐색을 계속 진행합니다.
- `e`, `f`, `g` 에서 양성이 0개가 된 원인을 shard depth 확대나 다른 shard 선택으로 확인합니다.
- 클러스터별 holdout 비교와 calibration 분석을 추가합니다.
- 튜닝 승자 설정과 현재 운영 설정을 비교한 뒤 기본 파라미터를 승격합니다.

## 참고 아티팩트

- 모델 경로: `~/Documents/borg_xgboost_workspace/models/xgboost`
- 학습 로그: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331041159_advanced_train_resumable.log`
- 현재 핸드오프: `reports/202603310423_advanced_training_completed.md`
"""


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = metrics_rows()
    stamp = datetime.now().strftime("%Y%m%d%H%M")
    en_path = REPORT_DIR / f"{stamp}_advanced_training_evaluation_en.md"
    ko_path = REPORT_DIR / f"{stamp}_advanced_training_evaluation_ko.md"
    en_path.write_text(english_report(rows), encoding="utf-8")
    ko_path.write_text(korean_report(rows), encoding="utf-8")
    print(f"Wrote {en_path}")
    print(f"Wrote {ko_path}")


if __name__ == "__main__":
    main()
