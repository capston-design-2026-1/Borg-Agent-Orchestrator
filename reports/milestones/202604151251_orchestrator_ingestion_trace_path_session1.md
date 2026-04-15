# Orchestrator Ingestion + Trace Path Hardening (Session 1, 2026-04-15 KST)

## Scope Completed

- Hardened Layer 1 ingestion reliability and data contracts under `orchestrator_stack/`.
- Added contract-focused tests for collector and trace ingestor.
- Added concise artifact/schema notes beside generated trace artifacts.

## Implementation Summary

1. `orchestrator/layer1/collector.py`
- Added row-indexed schema validation across all rows.
- Added detection for mixed flat/grouped input row shapes.
- Added stricter top-level payload validation and parse error messages in `build_trace_file`.
- Added guardrails for int/float contract fields and safer queue-priority normalization.

2. `orchestrator/layer1/trace_ingestor.py`
- Added strict trace contract validation for both `.json` and `.jsonl` inputs.
- Added required-key checks for trace rows (`timestamp`, `nodes`, `tasks`), node entries, and task entries.
- Added line-aware JSONL parse error reporting and unsupported extension checks.

3. Tests
- Updated `tests/test_collector.py` with late-row schema drift and non-list payload checks.
- Added `tests/test_trace_ingestor.py` for required-key validation, JSONL parse path, and line-specific JSONL decode failures.

4. Artifact Notes
- Updated `orchestrator_stack/examples/README.md` with Layer 1 input/output schema contract.
- Added `reports/traces/README.md` documenting episode trace log naming and record format.

## Validation Run

- `PYTHONPATH=orchestrator_stack python3` smoke check for:
  - `validate_prometheus_schema`
  - `prometheus_rows_to_trace`
  - `build_trace_file`
  - `load_trace_rows`
- `python3 -m compileall orchestrator_stack/orchestrator/layer1 orchestrator_stack/tests`

## Validation Gap

- `pytest` execution could not be run in this worktree because available interpreters do not currently have `pytest` installed.

## Suggested Session 2 Start

- Install/activate a runtime with `pytest` and run:
  - `python -m pytest orchestrator_stack/tests/test_collector.py orchestrator_stack/tests/test_trace_ingestor.py`
- If green, continue with AIOpsLab state mapping (`layer2/simulator.py::_to_observation`).
