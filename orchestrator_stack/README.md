# Full Orchestrator Stack (Isolated Workspace)

This directory implements the full 6-layer orchestrator process end-to-end:

1. Local source ingestion (`Prometheus/JSON` -> trace file)
2. AIOpsLab-style simulator backend + feature extraction
3. XGBoost safety-risk and demand predictors
4. MARL policy layer (PPO-compatible action interface) + referee
5. Optuna trial manager for reward and policy hyperparameters
6. Scoreboard feedback loop into policy/trial evaluation

Architecture diagram: [ARCHITECTURE.md](/Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/orchestrator_stack/ARCHITECTURE.md)

## Directory Layout

```text
orchestrator_stack/
├── AGENTS.md
├── ARCHITECTURE.md
├── NEXT_STEPS.md
├── README.md
├── config/
│   └── orchestrator.example.json
├── examples/
│   ├── sample_metrics.json
│   ├── sample_trace.json
│   └── generate_synthetic_assets.py
├── orchestrator/
│   ├── cli.py
│   ├── main.py
│   ├── layer1/  # collector + trace ingestion
│   ├── layer2/  # twin backend + feature extraction
│   ├── layer3/  # XGBoost training/inference
│   ├── layer4/  # policy spaces + referee + RLlib env/trainer
│   ├── layer5/  # Optuna tuners
│   └── layer6/  # scoreboard
└── run.py
```

## Open-Source Upstream Snapshot (checked on 2026-04-14)

- Ray RLlib latest release tag: `Ray-2.54.1`
- Optuna latest release tag: `v4.8.0`
- XGBoost latest release tag: `v3.2.0`
- Prometheus latest release tag: `v3.11.2`
- Microsoft AIOpsLab: active repository, no formal GitHub release tags

## Quick Start

1. Install requirements:

```bash
python3 -m pip install -r orchestrator_stack/requirements.txt
```

2. Generate synthetic example assets:

```bash
./.venv/bin/python orchestrator_stack/examples/generate_synthetic_assets.py
```

3. Layer 1 build (metrics -> trace):

```bash
./.venv/bin/python orchestrator_stack/run.py build-trace \
  --metrics orchestrator_stack/examples/sample_metrics.json \
  --out orchestrator_stack/examples/sample_trace.json
```

4. Layer 3 train predictors from trace features:

```bash
./.venv/bin/python orchestrator_stack/run.py train-brains \
  --trace orchestrator_stack/examples/sample_trace.json \
  --risk-out orchestrator_stack/examples/models/risk_model.json \
  --demand-out orchestrator_stack/examples/models/demand_model.json
```

5. Run orchestrator episode (Layers 2-4-6 loop):

```bash
./.venv/bin/python orchestrator_stack/run.py run --config orchestrator_stack/config/orchestrator.example.json
```

6. Run full process (Layers 1-6 with Optuna tuning + PPO training hook):

```bash
./.venv/bin/python orchestrator_stack/run.py full-process \
  --config orchestrator_stack/config/orchestrator.example.json \
  --trials 3
```

## Notes

- `train-policy` uses RLlib when installed; otherwise it returns a structured `skipped` status.
- `full-process` is still executable without RLlib; tuning and evaluation paths remain active.
