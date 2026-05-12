# Energy Watts Model

This repository currently reports watts as a calibrated utilization-derived estimate, not as a direct hardware wattmeter, IPMI, RAPL, or cloud-provider power reading.

The value is still useful for relative orchestration experiments because the same model is applied consistently across live Kubernetes traces, Agent B rewards, and the local dual-cluster comparison dashboard. It should not be described as measured physical power unless the calibration source is replaced with a real measurement source.

## Where Watts Appear

| Field or widget | Meaning | Source |
|---|---|---|
| `energy_watts` | Estimated total node power for the live experimental cluster snapshot. | `orchestrator_stack/orchestrator/layer1/kubernetes_trace.py` |
| `power_calibration` | Metadata stored beside `energy_watts`, including coefficients and source label. | live trace rows |
| Agent B reward power | Experimental `energy_watts` used by the efficiency reward path. | live orchestration state |
| Comparison `controlled_resource_totals.estimated_power_watts` | Estimated dynamic power for controlled namespaces only, excluding idle/control-plane noise. | `orchestrator_stack/orchestrator/comparison_dashboard_server.py` |
| Comparison dashboard `Efficiency Energy` | Experimental vs baseline controlled dynamic watts over the recent dashboard window. | comparison dashboard API |

## Default Node Estimate

For each node, the default model is:

```text
node_estimated_watts =
  idle_watts
  + cpu_full_scale_watts * bounded_cpu_util
  + mem_full_scale_watts * bounded_mem_util
```

Default coefficients:

```text
idle_watts = 80.0
cpu_full_scale_watts = 120.0
mem_full_scale_watts = 60.0
```

So a node at `cpu_util=0.10` and `mem_util=0.20` is estimated as:

```text
80 + 120*0.10 + 60*0.20 = 104W
```

Cluster `energy_watts` is the sum of this estimate across nodes.

```text
cluster_energy_watts = sum(node_estimated_watts for every observed node)
```

All utilization ratios are bounded into `[0.0, 1.0]` before the formula is applied.

## What Utilization Means

There are two live trace paths:

| Path | CPU/MEM utilization source | Interpretation |
|---|---|---|
| Kubernetes API only | pod resource requests divided by node allocatable resources | request-pressure estimate, not actual usage |
| Kubernetes API plus Prometheus/node-exporter | Prometheus node CPU and memory utilization samples | observed utilization estimate |

When Prometheus is available, `capture_kubernetes_trace_row(...)` first builds a Kubernetes snapshot and then `enrich_trace_row_with_prometheus(...)` replaces node CPU/MEM utilization with Prometheus samples. The trace row records `telemetry_sources` so the dashboard can show whether the value came from Kubernetes only or from Prometheus enrichment.

## Controlled Dynamic Watts In The Comparison Dashboard

The comparison dashboard has a second energy-like metric:

```text
controlled_dynamic_watts =
  120.0 * controlled_namespace_cpu_used / cluster_allocatable_cpu
  + 60.0 * controlled_namespace_memory_used / cluster_allocatable_memory
```

This value intentionally does not add `idle_watts`.

Reason: the comparison dashboard is trying to compare the controller-relevant work in the mirrored namespaces, not the fixed idle cost of two local Kind clusters, Prometheus, control-plane pods, CoreDNS, and other infrastructure noise.

Controlled namespaces:

```text
borg-comparison-workload
borg-orchestrator-exercise
```

This metric is best read as relative dynamic load pressure, not physical wall power.

## Agent B Reward Usage

Agent B receives an efficiency bonus from live telemetry when `energy_watts` exists:

```text
AgentB telemetry bonus = max(0, (500 - energy_watts) / 100)
```

Lower estimated watts therefore increase Agent B reward, but the reward is still based on the calibrated estimate. If the estimate is wrong, the reward signal is also biased.

## Calibration

The default calibration file is:

```text
orchestrator_stack/config/kind_power_calibration.example.json
```

Example:

```json
{
  "idle_watts": 80.0,
  "cpu_full_scale_watts": 120.0,
  "mem_full_scale_watts": 60.0,
  "source": "default_utilization_model; replace with measured node calibration when available"
}
```

The live launcher accepts:

```bash
POWER_CALIBRATION=orchestrator_stack/config/kind_power_calibration.example.json ./orchestrator_stack/scripts/launch_orchestration.sh
```

For thesis-grade power claims, replace the default coefficients with measured calibration from a wattmeter, RAPL, IPMI, smart-PDU, or another real power exporter, and set `source` to describe that measurement path.

## How To Phrase It In Reports

Use:

```text
estimated watts
calibrated utilization-derived watts
controlled dynamic watts
relative energy-efficiency signal
```

Avoid unless direct measurement is added:

```text
measured watts
actual physical power
real energy consumption
hardware power draw
```

## Code References

| Concern | File |
|---|---|
| calibration dataclass and default coefficients | `orchestrator_stack/orchestrator/layer1/kubernetes_trace.py` |
| node estimate formula | `estimate_node_power_watts(...)` in `orchestrator_stack/orchestrator/layer1/kubernetes_trace.py` |
| Prometheus enrichment | `enrich_trace_row_with_prometheus(...)` in `orchestrator_stack/orchestrator/layer1/kubernetes_trace.py` |
| comparison controlled dynamic watts | `_controlled_resource_totals(...)` in `orchestrator_stack/orchestrator/comparison_dashboard_server.py` |
| example calibration file | `orchestrator_stack/config/kind_power_calibration.example.json` |
