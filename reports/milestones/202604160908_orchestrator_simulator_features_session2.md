# Orchestrator Simulator + Feature Extraction (Session 2, 2026-04-16 KST)

## Scope Completed

- Implemented Layer 2 simulator normalization and AIOpsLab-style adapter stepping under `orchestrator_stack/`.
- Integrated Layer 2 feature extraction with the shared observation normalization path.
- Added focused simulator and feature tests plus continuity updates.

## Implementation Summary

1. `orchestrator_stack/orchestrator/layer2/simulator.py`
- Expanded `state_to_observation()` to normalize nested wrapper payloads, dict-backed node/task collections, queued tasks, alternate metric names, and score maps into the internal `Observation` model.
- Extended `AIOpsLabBackend` so it can use an injected orchestrator adapter and probe common live methods (`get_current_state`, `execute`, `step`, `act`) before falling back to the local simulator.
- Kept local mock/twin behavior intact for runtimes without `aiopslab`.

2. `orchestrator_stack/orchestrator/layer2/feature_extractor.py`
- Kept the Layer 2 feature width on the shared `FEATURE_COUNT=8` contract.
- Routed training-matrix construction through normalized observations so canonical trace rows, flat Prometheus-derived rows, and AIOpsLab-style nested payloads use the same feature semantics.
- Preserved future-state demand/risk target behavior while aligning labels with normalized node/task states.

3. Tests and support files
- Added `orchestrator_stack/tests/test_simulator.py` for nested state normalization and injected-adapter stepping.
- Extended `orchestrator_stack/tests/test_feature_extractor.py` for AIOpsLab-style payloads and future-state targets.
- Updated synthetic asset generation and lazy Layer 2 exports to stay consistent with the shared feature width and avoid unnecessary import failures in simulator-only runs.

## Validation

Executed in-session:

- `python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/tests`
  - Result: success
- `PYTHONPATH=orchestrator_stack python3` simulator smoke for `state_to_observation()` and injected `AIOpsLabBackend`
  - Result: success (`layer2-simulator-smoke-ok`)

## Validation Gaps

- `python3 -m pytest ...`
  - Result: failed because this worktree `python3` does not have `pytest`
- Full feature-extractor runtime smoke under `python3`
  - Result: blocked because this worktree `python3` does not have `numpy`

## Next Recommended Step

- Validate the live AIOpsLab adapter against the actual upstream package/session API in a runtime that has both orchestrator dependencies and the `aiopslab` package installed.
