# Orchestrator Simulator + Feature Extraction (Session 6, 2026-04-16 KST)

## Scope

- `orchestrator_stack/` Layer 2 simulator + feature extraction only
- Immediate tests/fixes for the same slice
- Root continuity updates in `README.md` and `NEXT_STEPS.md`

## Implemented

1. Shared Layer 2 normalization
- Added `state_to_observation()` in `orchestrator_stack/orchestrator/layer2/simulator.py`.
- The mapper now normalizes:
  - nested wrappers such as `state`, `cluster`, `observation`, and `snapshot`
  - list-backed or dict-backed node/task collections
  - alternate node/task field names used by AIOpsLab-style payloads
  - queued task placement and string bool parsing
  - `risk_scores` / `demand_scores` aliases into the shared `Observation` contract

2. Simulator behavior
- `TraceDrivenTwinBackend` now uses the shared normalization path instead of its own raw-dict parser.
- `AIOpsLabBackend` no longer returns an empty observation on every fallback step.
- When the upstream `aiopslab` package is unavailable, the backend now advances a local stateful twin-like simulation with action effects, updated demand/risk projections, and per-agent rewards.

3. Feature extraction integration
- Layer 2 feature extraction now uses the same normalized observation path as the simulator.
- Added flat metric-row ingestion support by routing Prometheus-style rows through Layer 1 trace normalization before building training matrices.
- Feature width is now shared through `FEATURE_COUNT=8`, and synthetic asset generation derives its example matrix width from that constant.

4. Tests
- Added `orchestrator_stack/tests/test_simulator.py` for:
  - nested AIOpsLab-style payload normalization
  - string-bool parsing through the trace twin
  - fallback AIOpsLab step transitions
- Extended `orchestrator_stack/tests/test_feature_extractor.py` for:
  - task-pressure/power-state features
  - flat metric-row training-matrix ingestion

## Validation

Executed in-session:

- `python3 -m compileall orchestrator_stack/orchestrator/layer2 orchestrator_stack/tests orchestrator_stack/examples/generate_synthetic_assets.py`
  - Result: success
- `PYTHONPATH=orchestrator_stack python3` custom Layer 2 smoke script covering simulator normalization, fallback AIOpsLab stepping, and grouped/flat feature extraction
  - Result: success (`layer2-smoke-ok`)

Could not execute in-session:

- `pytest`
  - Reason: repo `.venv` in this worktree is a self-referential symlink, and fallback `python3` lacks `numpy` and `pytest`

## Remaining Gap

- Direct validation against the real upstream AIOpsLab package/session API is still open.
- RLlib environment integration is intentionally untouched in this slice.
