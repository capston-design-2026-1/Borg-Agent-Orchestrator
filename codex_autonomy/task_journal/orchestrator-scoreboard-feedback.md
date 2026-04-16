# Task Journal: orchestrator-scoreboard-feedback

- Title: Orchestrator: global scoreboard and feedback loop
- Task type: feature
- Issue: https://github.com/capston-design-2026-1/Borg-Agent-Orchestrator/issues/38
- Scope: orchestrator_stack/, reports/, README.md, NEXT_STEPS.md

## 2026-04-16T01:17:29Z | Session 1 | session_started

- supervisor started session 1 of 6
- prompt file: /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/codex_autonomy/runtime/logs/orchestrator-scoreboard-feedback/session_001.prompt.txt
- supervisor will publish heartbeat trace commits during execution
## 2026-04-16T01:17:38Z | Session 1 | heartbeat

- elapsed_seconds: 8
- stdout_chars: 0
- stderr_chars: 8372
- excerpt: reports/tuning/202604142305_optuna_orchestrator_policy_and_rewards.md
reports/tuning/202604142305_optuna_orchestrator_reward_weights.md
- worktree_status:
-   ?? .venv
## 2026-04-16T01:17:54Z | Session 1 | heartbeat

- elapsed_seconds: 24
- stdout_chars: 0
- stderr_chars: 19649
- excerpt: till assume a valid repo-root virtualenv.
12. Extend `status` output to show active-queue vs deferred-cooldown counts so operators can distinguish blocked cooldown work from runnable work at a glance.
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:03Z | Session 1 | heartbeat

- elapsed_seconds: 32
- stdout_chars: 0
- stderr_chars: 25181
- excerpt: succeeded in 422ms:
# Orchestrator Simulator + Feature Integration (Session 5, 2026-04-16 KST)
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:11Z | Session 1 | heartbeat

- elapsed_seconds: 40
- stdout_chars: 0
- stderr_chars: 44052
- excerpt: on for this slice yet in the journal itself. The next step is reading the code hits for `scoreboard`, `feedback`, `referee`, and `reward` so I can map the missing state flow end to end before editing.
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:27Z | Session 1 | heartbeat

- elapsed_seconds: 56
- stdout_chars: 0
- stderr_chars: 65254
- excerpt: scoreboard.update({"AgentA": 10.0, "AgentB": 5.0, "AgentC": 2.0})
    assert round(scoreboard.total(), 3) == 14.6
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:35Z | Session 1 | heartbeat

- elapsed_seconds: 65
- stdout_chars: 0
- stderr_chars: 85202
- excerpt: priority=self.priority,
        )
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:43Z | Session 1 | heartbeat

- elapsed_seconds: 73
- stdout_chars: 0
- stderr_chars: 94150
- excerpt: assert action.agent_name == "AgentA"
    assert action.kind == ActionKind.MIGRATE
- worktree_status:
-   ?? .venv
## 2026-04-16T01:18:59Z | Session 1 | heartbeat

- elapsed_seconds: 89
- stdout_chars: 0
- stderr_chars: 95008
- excerpt: d implement Layer 6 feedback signal API and tests
  • Integrate feedback into referee/env/main/tuning flows and add tests
  • Run validation, update docs/report/next steps, then commit and push slices
- worktree_status:
-   ?? .venv
## 2026-04-16T01:19:24Z | Session 1 | heartbeat

- elapsed_seconds: 113
- stdout_chars: 0
- stderr_chars: 95266
- excerpt: ge is: `Scoreboard.update()` will return both the weighted global score and a bounded feedback signal, and Layer 4 will consume that feedback on the next decision instead of ignoring Layer 6 entirely.
- worktree_status:
-   ?? .venv
## 2026-04-16T01:19:32Z | Session 1 | heartbeat

- elapsed_seconds: 121
- stdout_chars: 0
- stderr_chars: 97135
- excerpt: +    score: GlobalScore
+    feedback: ScoreFeedback
- worktree_status:
-   M orchestrator_stack/orchestrator/types.py
-   ?? .venv
## 2026-04-16T01:19:56Z | Session 1 | heartbeat

- elapsed_seconds: 146
- stdout_chars: 0
- stderr_chars: 110772
- excerpt: +    score: GlobalScore
+    feedback: ScoreFeedback
- worktree_status:
-   M orchestrator_stack/orchestrator/layer6/scoreboard.py
-   M orchestrator_stack/orchestrator/types.py
-   ?? .venv
## 2026-04-16T01:20:12Z | Session 1 | heartbeat

- elapsed_seconds: 162
- stdout_chars: 0
- stderr_chars: 127833
- excerpt: lf and added unit coverage for feedback shaping and reset behavior. Next I’m threading that feedback into decision resolution and the episode/training loops so the new state actually affects behavior.
- worktree_status:
-   M orchestrator_stack/orchestrator/layer6/scoreboard.py
-   M orchestrator_stack/orchestrator/types.py
-   M orchestrator_stack/tests/test_scoreboard.py
-   ?? .venv
## 2026-04-16T01:20:21Z | Session 1 | heartbeat

- elapsed_seconds: 170
- stdout_chars: 0
- stderr_chars: 147463
- excerpt: +    assert scoreboard.adjusted_total() == 0.0
+    assert scoreboard.latest_feedback() is None
- worktree_status:
-   M orchestrator_stack/orchestrator/layer4/referee.py
-   M orchestrator_stack/orchestrator/layer6/scoreboard.py
-   M orchestrator_stack/orchestrator/types.py
-   M orchestrator_stack/tests/test_scoreboard.py
-   ?? .venv
