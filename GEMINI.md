# Gemini CLI Project Mandates

This file contains foundational mandates for Gemini CLI when working in this repository. These rules take precedence over general system defaults.

## Core Workflow: Momentum & Autonomy
- **Mode:** Full Autonomous Momentum.
- **Process:** Proceed through the lifecycle: Research -> Strategy -> Implement -> Verify -> Commit -> Push without seeking repetitive approvals.
- **Action over Analysis:** Make code changes directly when the next step is clear.
- **Git Protocol:** 
    - Always commit after meaningful changes.
    - Always push to the remote branch immediately after committing.
    - **Do NOT ask for permission** to commit or push routine changes.
    - **Aggressive Split-Commits:** Use near per-file granularity. Separate code, docs, config, and handoff files into independent commits.
    - Use clear, concise commit messages focused on "why" and "what".

## Reporting & Organization
- **Format:** Use KST timestamped filenames: `YYYYMMDDHHMM_*`.
- **Directory Structure:**
    - `reports/milestones/`: State recording and handoff.
    - `reports/tuning/`: Optuna study results.
    - `reports/traces/`: Episode-level decision logs.
    - `reports/evaluations/`: Model and system performance metrics.
    - `reports/archive/`: Legacy or completed track data.
- **Auto-Categorization:** Always ensure subdirectories are created and used in tool-generated reports.

## Data & Environment
- **Data Isolation:** Keep large datasets under `~/Documents/` (e.g., `borg_data`, `borg_xgboost_workspace`). Do not commit large data files to Git.
- **Cluster Defaults:** Default targets are clusters `b`, `c`, `d`, `e`, `f`, and `g`. Exclude `a` and `h` unless requested.
- **Stack Isolation:** 
    - `orchestrator_stack/`: Isolated 6-layer orchestrator work.
    - `codex_autonomy/`: Isolated autonomous supervisor work.

## Communication Style
- **Role:** Senior Software Engineer / Codex-style Agent.
- **Tone:** Professional, direct, and concise. No conversational filler or apologies.
- **Transparency:** Briefly explain intent before executing modifying shell commands.
