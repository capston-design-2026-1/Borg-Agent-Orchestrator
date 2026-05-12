# Live Remediation And Comparison Handoff

Timestamp: 2026-05-12 16:23 KST

## Purpose

This report preserves the current state for the next Codex session after the live dual-cluster comparison and Kubernetes remediation work. It should be read with:

- `Agents.md`
- `NEXT_STEPS.md`
- `orchestrator_stack/AGENTS.md`
- `orchestrator_stack/NEXT_STEPS.md`
- `docs/LOCAL_CLUSTER_COMPARISON.md`
- `docs/LOCAL_DUAL_CLUSTER_RUNBOOK.md`
- `docs/en/DASHBOARD_GUIDE.md`
- `docs/ko/DASHBOARD_GUIDE.md`

## Latest Commit Landmark

Latest pushed commit at handoff:

```text
5673ed2 Document experimental QoS cap boundary
```

Important commits in this slice:

```text
0fa11c6 Add live Kubernetes action executor
823e3d0 Make exercise load consume real CPU
1b68735 Execute live Kubernetes decisions
d3b74a6 Compare controlled namespace efficiency
82e0b60 Show controlled efficiency metrics
0d572b8 Test live Kubernetes action executor
2f96306 Assert live action execution state
36d252f Assert controlled comparison signals
0705476 Document live action execution
f9ef310 Document live action execution in Korean
3b33983 Document controlled comparison metrics
c8d29a6 Cap experimental load generator QoS
5ef0efb Assert load generator QoS cap
4f7e9c6 Document load generator QoS cap
90b3e2e Document load generator QoS cap in Korean
5673ed2 Document experimental QoS cap boundary
```

## What Was Fixed

The user expected experimental metrics to beat the HPA/local-Karpenter baseline. The root issue was that selected Agent A/B/C actions were not direct Kubernetes remediations. They were mostly evaluated in the twin/reward path, while the comparison dashboard was reading real cluster metrics.

The fix adds a live Kubernetes executor:

- File: `orchestrator_stack/orchestrator/layer1/kubernetes_actions.py`
- Integrated in: `orchestrator_stack/orchestrator/visualization.py`
- Tests:
  - `orchestrator_stack/tests/test_kubernetes_actions.py`
  - `orchestrator_stack/tests/test_visualization_runtime.py`
  - `orchestrator_stack/tests/test_local_cluster_comparison.py`

The executor applies only bounded experimental-side actions:

- scales or caps exerciser Deployments in `borg-orchestrator-exercise`
- applies a bounded QoS envelope to experimental `borg-comparison-workload/comparison-load-generator`
- leaves mirrored baseline stimulus untouched
- records exact commands under `decision.kubernetes_execution`

## Workload Realism Change

Schedulable exercise phases now use bounded BusyBox CPU-burner containers instead of only `pause` pods. This makes CPU and dynamic-power effects visible through Metrics Server.

Admission/backlog phases still use `pause` pods because they intentionally test queue and scheduler pressure rather than active CPU burn.

## Dashboard And Metric Semantics

The comparison dashboard now distinguishes raw cluster totals from controller-relevant controlled metrics.

Primary comparison metric path:

```text
controlled_resource_totals
```

Controlled namespaces:

```text
borg-comparison-workload
borg-orchestrator-exercise
```

Why this matters:

- raw cluster totals can be dominated by control-plane, Prometheus, and Metrics Server noise
- controlled totals represent the namespaces that the experimental architecture and mirrored stimulus actually manipulate
- controlled dynamic watts are model-derived, not hardware wattmeter measurements

## Current Live Runtime

At handoff, the dual-cluster stack was running in detached `screen` sessions:

```text
borg-experimental-orchestrator
borg-exp-dashboard
borg-comparison-dashboard
borg-local-karpenter
borg-exp-prom
borg-base-prom
```

URLs:

```text
experimental dashboard: http://127.0.0.1:8765
comparison dashboard:   http://127.0.0.1:8876
experimental Prometheus: http://127.0.0.1:19090
baseline Prometheus:     http://127.0.0.1:19091
```

Kubeconfigs:

```text
experimental: ~/Documents/borg_orchestrator_clusters/kubeconfig-experimental
baseline:     ~/Documents/borg_orchestrator_clusters/kubeconfig-baseline
```

Latest observed live state before this handoff:

- `state.json` active stage: `live_kubernetes_loop`
- latest example decision: `AgentA:replicate`
- latest example execution: `kubernetes_execution.status=applied`
- example operations:
  - scale/cap `borg-orchestrator-exercise/admission-cap`
  - cap `borg-comparison-workload/comparison-load-generator`
- Optuna completed trials in persistent study: `42`

## Commands To Inspect Runtime

List detached sessions:

```bash
screen -ls
```

Watch experimental orchestrator log:

```bash
tail -f orchestrator_stack/runtime/local-dual-cluster/experimental.log
```

Inspect latest experimental state:

```bash
python3 -m json.tool orchestrator_stack/runtime/visualization-experimental/state.json | head -n 120
```

Inspect comparison API:

```bash
curl -fsS http://127.0.0.1:8876/api/comparison | python3 -m json.tool | head -n 160
```

k9s:

```bash
KUBECONFIG=~/Documents/borg_orchestrator_clusters/kubeconfig-experimental k9s
KUBECONFIG=~/Documents/borg_orchestrator_clusters/kubeconfig-baseline k9s
```

Stop everything:

```bash
cd /Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator && ./orchestrator_stack/scripts/stop_local_dual_cluster_stack.sh
```

## Validation

Passed:

```bash
PYTHONPATH=orchestrator_stack ./.venv/bin/python -m pytest orchestrator_stack/tests -q
```

Result:

```text
121 passed
```

Whitespace check:

```bash
git diff --check
```

Result: clean.

## Known Caveats

- A single dashboard sample is not thesis-grade evidence.
- Metrics Server is delayed and low-resolution, so CPU/memory values can wobble after each mutation.
- Exerciser phases rotate, so the baseline and experimental clusters can briefly be in different settling states after a new phase and an Agent remediation.
- `energy_watts` and controlled dynamic watts remain calibrated utilization-derived estimates, not direct wattmeter readings.
- The comparison launcher lifecycle still deserves hardening. Manual detached `screen` sessions were used to keep the current runtime stable after child processes from one-shot shell execution exited.

## Next Jobs

1. Add a fixed-sequence dual-cluster experiment runner that records per-stimulus windows, not just live dashboard state.
2. Persist comparison dashboard history to JSON/CSV so evidence survives browser refresh and can be cited in a thesis.
3. Harden lifecycle scripts to start/stop the live orchestrator, dashboards, local Karpenter, and Prometheus port-forwards as durable detached processes without manual `screen` work.
4. Add windowed objective summaries for experimental vs baseline:
   - controlled CPU
   - controlled memory
   - controlled dynamic watts
   - pending pods
   - request pressure
   - reward
   - max risk
   - selected actions
5. Add direct node power telemetry if a local exporter such as Kepler/RAPL becomes available.
