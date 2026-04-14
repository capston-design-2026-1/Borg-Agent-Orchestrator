# Autonomy GitHub Flow Upgrade (2026-04-14 KST)

## Summary

Upgraded `codex_autonomy/` to support organized multi-engineer style GitHub collaboration flow:

- task-linked issue metadata (`issue_number`, `issue_url`)
- task-linked PR metadata (`pr_number`, `pr_url`)
- auto issue creation (optional)
- auto PR creation (optional)
- review stage status (`review`) when PR exists but not merged
- auto-merge loop for review tasks when enabled
- queue status now shows issue/PR linkage

## New Module

- `codex_autonomy/codex_autonomy/github_flow.py`
  - `ensure_issue`
  - `ensure_pr`
  - `try_merge_pr`
  - graceful fallback when `gh` is unavailable

## Config Additions

`codex_autonomy/config/autonomy.example.yaml` now includes `github:` block:

- `enabled`
- `repo`
- `auto_create_issue`
- `auto_create_pr`
- `auto_merge`
- `merge_method`
- `draft_pr`
- `auto_issue_on_health`
- `reviewers`
- `assignees`
- label settings

## Behavior Changes

- Worker links tasks to issue/PR and updates task YAML with URLs/numbers.
- Completed tasks with unmerged PR become `review` status.
- Manager attempts to merge `review` tasks when auto-merge is enabled.
- Health-generated tasks can skip auto-issue based on `auto_issue_on_health`.

## Validation

- compile check passed for updated autonomy modules
- daemon smoke run with `github.enabled=false` passed
- queue/status output includes issue/PR columns
