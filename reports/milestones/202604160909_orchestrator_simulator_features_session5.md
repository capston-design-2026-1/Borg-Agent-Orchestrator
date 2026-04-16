# Orchestrator Simulator + Feature Integration (Session 5, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 2 simulator and feature extraction only.
- Immediate Layer 2 tests/fixes needed to keep this PR coherent.

## Completed

1. Shared observation normalization
- Hardened `state_to_observation()` for nested AIOpsLab-style payloads, dict-backed node/task collections, queue placement, alternate field names, and Prometheus-style list inputs.
- Fixed ratio normalization so slight values above `1.0` now clamp instead of being misread as percentages.

2. Simulator behavior
- Restored shared action-transition behavior between `TraceDrivenTwinBackend` and `AIOpsLabBackend` by moving the local twin transition logic onto a common helper.
- Kept the trace backend action deltas merged onto the next trace frame so replay stays trace-driven while still reflecting the chosen action.
- Decoupled `orchestrator.layer2` package imports so simulator-only usage no longer eagerly requires `numpy`.

3. Feature extraction
- Kept Layer 2 feature width at `FEATURE_COUNT=8`.
- Updated training-label generation to use the next normalized observation for risk and demand targets instead of relying on ad hoc raw-dict access.
- Aligned synthetic asset generation with the shared feature-count constant.

4. Tests
- Added/extended Layer 2 tests for nested simulator payloads, trace-backend migration application, future-state feature targets, and AIOpsLab-style payload normalization.

## Validation

- `PYTHONPATH=orchestrator_stack python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/examples orchestrator_stack/tests`
  - Result: success
- `PYTHONPATH=orchestrator_stack python3` smoke for `orchestrator_stack/tests/test_simulator.py`
  - Result: success (`simulator-smoke-ok`)

## Validation Gaps

- Full feature-extractor execution could not be run in this worktree because the available `python3` lacks `numpy`.
- `pytest` is still unavailable in this worktree runtime.
- The requested follow-up YAML could not be written to `/Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/codex_autonomy/runtime/logs/orchestrator-simulator-features/session_005.followups.yaml` because that path is outside this worktree's writable sandbox.

## Suggested Session 6 Start

1. Run Layer 2 tests in an environment with `numpy` and `pytest`.
2. Validate the live AIOpsLab adapter path against the actual upstream API and remove remaining inference-based fallback behavior where possible.
