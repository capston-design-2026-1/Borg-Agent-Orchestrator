# Orchestrator Simulator + Feature Extraction (Session 1, 2026-04-17 KST)

## Scope Completed

- Hardened the Layer 2 AIOpsLab adapter path so initialized session/problem objects are used before the top-level orchestrator object.
- Fixed Layer 2 observation normalization so missing node score fields do not erase future-state feature targets.
- Restored direct Layer 2 smoke/test execution in this worktree's fallback `python3` runtime even without `numpy`.

## Implementation Summary

1. `orchestrator_stack/orchestrator/layer2/simulator.py`
- Added adapter-result unwrapping for tuple/list `step()` responses and state-wrapper payloads.
- Made `AIOpsLabBackend` probe initialized session objects before the orchestrator object for reset/step state recovery.
- Stopped injecting zero-valued per-node risk/demand entries when upstream payloads omit those fields, preserving the feature extractor's future-state fallback behavior.

2. `orchestrator_stack/orchestrator/layer2/feature_extractor.py`
- Added a minimal array compatibility wrapper so `observation_matrix()` and `trace_rows_to_training_matrices()` still expose `.shape` and `.tolist()` in runtimes without `numpy`.
- Kept the existing `FEATURE_COUNT=8` contract and future-state label semantics intact.

3. Tests
- Added a focused simulator test covering session-first adapter stepping and tuple result unwrapping.
- Updated feature tests so expected risk/demand labels match the current future-state contract for grouped, nested, and flat metric rows.

## Validation

- `PYTHONPATH=orchestrator_stack python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/tests/test_simulator.py orchestrator_stack/tests/test_feature_extractor.py`
  - Result: success
- `PYTHONPATH=orchestrator_stack python3` direct execution of all functions in `orchestrator_stack/tests/test_simulator.py` and `orchestrator_stack/tests/test_feature_extractor.py`
  - Result: success (`layer2-focused-tests-ok`)

## Remaining Gap

- Validate the adapter against the real upstream AIOpsLab package/session API in an environment where `aiopslab` is installed and `pytest` is available, then replace the current compatibility probing with a confirmed contract.
