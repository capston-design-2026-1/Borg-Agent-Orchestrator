# 수리된 라벨 재실행 상태

## 요약

- 이전 스크립트를 교체하는 대신 새로운 추가 세부 래퍼로 고급 이벤트 플랫 샤드를 복구했습니다.
- `b`부터 @@PLH0001@@@까지의 클러스터에 대한 조인 키가 완전히 채워진 고급 이벤트 쪽모이 세공을 다시 생성했습니다.
- 복구된 클러스터 `e`, `f` 및 `g`에 대한 고급 조인을 다시 실행합니다.
- 복구된 클러스터 `e`, `f` 및 `g`에 대한 고급 기능 빌드를 다시 실행합니다.
- `e`, `f`, `g`이 더 이상 양성 반응이 0이 아닌 것으로 확인되었습니다.
- 더 이상 사용되지 않는 수리 전 조정 실행에서 수리된 레이블 훈련을 분리하는 새 모델 이름으로 조정된 XGBoost 훈련을 다시 시작했습니다.

## 자세한 로그

- 이벤트 복구 : `~/Documents/borg_xgboost_workspace/runtime/logs/20260331151302_advanced_event_repair_detailed.log`
- 재방송 참여 : `~/Documents/borg_xgboost_workspace/runtime/logs/20260331152055_advanced_join_resumable_detailed.log`
- 특집 재방송 : `~/Documents/borg_xgboost_workspace/runtime/logs/20260331152830_advanced_feature_build_resumable_detailed.log`
- 실시간 훈련 재실행: `~/Documents/borg_xgboost_workspace/runtime/logs/20260331153419_advanced_train_resumable_detailed.log`

## 복구된 조인 결과

- `e`: `58,784,525` 행, `22,553,673` 이벤트 레이블이 지정된 행
- `f`: `71,298,784` 행, `54,306,159` 이벤트 레이블이 지정된 행
- `g`: `61,083,781` 행, `20,708,106` 이벤트 레이블이 지정된 행

## 수리된 기능 라벨 합계

- `b`: `5m=65,537`, `15m=78,359`, `30m=91,387`, `45m=96,116`, `60m=99,303`
- `c`: `5m=152,711`, `15m=182,451`, `30m=200,980`, `45m=212,647`, `60m=222,296`
- `d`: `5m=27,307`, `15m=35,422`, `30m=42,821`, `45m=48,111`, `60m=52,288`
- `e`: `5m=129,553`, `15m=175,699`, `30m=200,677`, `45m=220,331`, `60m=233,409`
- `f`: `5m=48,677`, `15m=93,644`, `30m=148,814`, `45m=194,633`, `60m=240,144`
- `g`: `5m=39,509`, `15m=60,618`, `30m=81,189`, `45m=97,625`, `60m=111,570`

## 훈련 재실행

- 더 이상 사용되지 않는 튜닝 실행: `xgboost_failure_risk_tuned_v1`
  - 이 실행은 `e/f/g` 수리 전에 시작되었으며 최종 조정 후보로 간주되어서는 안 됩니다.
- 현재 튜닝된 실행: `xgboost_failure_risk_tuned_v2_repaired_labels`
- 재시작 시 진행 중인 현재 대상: `target_failure_5m`
- 조정된 매개변수:
  - `n_estimators=1600`
  - `max_depth=6`
  - `learning_rate=0.03`
  - `subsample=0.9`
  - `colsample_bytree=0.7`
  - `min_child_weight=8`
  - `reg_alpha=0.2`
  - `reg_lambda=2.0`
  - `early_stopping_rounds=80`
  - `verbose_eval=25`

## 재실행 중 적용되는 수정 사항

- 세부 조정된 재학습을 자동으로 시작하려는 첫 번째 시도에서는 명시적 하이퍼 매개변수 재정의가 env 파일 기본값으로 다시 설정됩니다.
- 원인: `scripts/run_advanced_train_resumable_detailed.sh` 모델 이름 및 수평선 재정의는 유지되지만 나머지 `BORG_XGB_*` 재정의는 유지되지 않습니다.
- 수정: `advanced_env.sh`을 소싱하기 전에 모든 훈련 관련 런타임 재정의를 보존한 다음 나중에 복원했습니다.
- 커밋: `5f66e48` (`Preserve tuned train overrides in detailed wrapper`)

## 다음 작업

- `xgboost_failure_risk_tuned_v2_repaired_labels`이 모든 지평선을 마무리하게 해주세요.
- 수리된 레이블 조정 지표를 기본 훈련 모델과 비교합니다.
- 수리 라벨 우승자의 영어 및 한국어 평가 보고서를 재생성합니다.