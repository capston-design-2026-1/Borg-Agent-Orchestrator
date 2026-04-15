# Orchestrator Ingestion + Trace Path Hardening (Session 1 Follow-up, 2026-04-15 KST)

## Scope

- `orchestrator_stack/` ingestion + trace contract reliability only.
- `reports/`, `README.md`, and `NEXT_STEPS.md` continuity updates.

## Implemented Hardening

1. `orchestrator_stack/orchestrator/layer1/collector.py`
- Enforced positive `interval_seconds` in `prometheus_rows_to_trace`.
- Enforced non-negative queue values (`queue_length`, `queue_priority`) during validation/normalization.
- Added robust bool-like parsing for `alive` and `task_death` (prevents Python truthiness bugs for string literals like `"false"`).
- Extended grouped-row validation for required task keys (`task_id`, `node_id`) and optional task field contracts.
- Fixed top-level schema check order so non-list empty payloads no longer bypass validation.

2. `orchestrator_stack/orchestrator/layer1/trace_ingestor.py`
- Added non-negative validation for `queue_length` and `queue_priority`.
- Added bool-like contract validation for task `alive` and row `task_death`.
- Added optional task contract validation (`urgency`, `queue_priority`, `alive`).
- Added fail-fast missing-source check with explicit error message.
- Normalized suffix handling through lowercase extension checks.

3. Tests
- Extended collector contract tests for:
  - non-list top-level payload rejection
  - negative queue-length rejection
  - bool-like parsing correctness for `alive/task_death`
  - non-positive interval rejection
- Extended trace-ingestor contract tests for:
  - negative queue-length rejection
  - invalid bool-like literal rejection (`alive`)
  - missing trace source rejection

## Validation

Executed in-session:

- `PYTHONPATH=orchestrator_stack python3 -m pytest orchestrator_stack/tests/test_collector.py orchestrator_stack/tests/test_trace_ingestor.py`
  - Result: failed due to runtime gap (`No module named pytest`).
- `python3 -m compileall orchestrator_stack/orchestrator/layer1 orchestrator_stack/tests`
  - Result: success.
- `PYTHONPATH=orchestrator_stack python3` smoke script for `validate_prometheus_schema`, `prometheus_rows_to_trace`, and `load_trace_rows`
  - Result: success (`layer1-smoke-ok`).

## Continuity Notes

- `orchestrator_stack/NEXT_STEPS.md`, root `NEXT_STEPS.md`, and `README.md` were updated to reflect the stricter ingestion/trace contract behavior.
- `orchestrator_stack/examples/README.md` now documents non-negative and bool-like contract fields.
