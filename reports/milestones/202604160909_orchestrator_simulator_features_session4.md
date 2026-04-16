# Orchestrator Simulator + Feature Extraction Integration (Session 4, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 2 simulator and feature extraction only.
- Immediate Layer 2 tests/fixes plus continuity updates under `README.md`, `NEXT_STEPS.md`, and `reports/`.

## Implemented

1. Shared AIOpsLab-style state normalization
- `orchestrator_stack/orchestrator/layer2/simulator.py`
- Expanded `state_to_observation()` to normalize nested wrapper payloads and alternate node/task field shapes used by AIOpsLab-style state snapshots.
- Added support for dict-backed node/task collections, nested resource containers, queued-task placement, alternate metric names, and embedded score maps.
- `AIOpsLabBackend` now supports injected orchestrator adapters and attempts generic reset/step method surfaces before falling back to local twin simulation.

2. Trace-driven simulator behavior
- `TraceDrivenTwinBackend.step()` now converts the current row into an `Observation`, applies the selected action through the simulator transition logic, and merges the action delta into the next trace row instead of ignoring the action effect.
- Reward evaluation now reads normalized observations instead of raw trace dictionaries.

3. Feature extraction integration
- `orchestrator_stack/orchestrator/layer2/feature_extractor.py`
- Training matrices now derive features from the same normalized `Observation` contract used at inference time.
- Added support for flat metrics rows by normalizing them through `prometheus_rows_to_trace()` before feature generation.
- Kept Layer 2 feature width stable at `FEATURE_COUNT=8` and updated synthetic asset generation to derive training shapes from that shared constant.

4. Tests
- Added `orchestrator_stack/tests/test_simulator.py` for nested AIOpsLab payload normalization and action-aware trace replay.
- Extended `orchestrator_stack/tests/test_feature_extractor.py` for:
  - task-pressure/power-state features
  - future-state risk/demand targets
  - AIOpsLab-style nested state rows
  - flat metrics row normalization

## Validation

Executed in-session:

- `python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/examples/generate_synthetic_assets.py orchestrator_stack/tests/test_feature_extractor.py orchestrator_stack/tests/test_simulator.py`
  - Result: success.
- `PYTHONPATH=orchestrator_stack python3` smoke script for `state_to_observation()` and injected `AIOpsLabBackend`
  - Result: success (`layer2-simulator-smoke-ok`).

Validation gaps in this worktree runtime:

- `PYTHONPATH=orchestrator_stack python3 -m pytest orchestrator_stack/tests/test_feature_extractor.py orchestrator_stack/tests/test_simulator.py`
  - Result: failed because `pytest` is not installed.
- Full feature-extractor smoke execution through `python3`
  - Result: blocked because `numpy` is not installed in the available runtime.

## Continuity Notes

- Root `README.md` and `NEXT_STEPS.md` now mention the Layer 2 shared observation contract.
- `orchestrator_stack/NEXT_STEPS.md` now points the next session at validating the live AIOpsLab adapter against the actual upstream package API instead of continuing generic state mapping work.
