# Full Orchestrator Stack (Isolated Workspace)

This directory implements the full architecture you specified as a clean, independent track:

1. Local source ingestion (Prometheus/JSON trace)
2. Digital twin simulator backend (trace twin + AIOpsLab adapter shell)
3. Dual XGBoost models (safety risk + resource demand)
4. Multi-agent decision layer (A/B/C + safety-first referee)
5. Optuna meta-optimizer for reward weights
6. Global scoreboard and feedback loop

## Directory Layout

```text
orchestrator_stack/
├── AGENTS.md
├── NEXT_STEPS.md
├── README.md
├── config/
│   └── orchestrator.example.json
├── examples/
│   └── ... synthetic assets
├── orchestrator/
│   ├── cli.py
│   ├── config.py
│   ├── main.py
│   ├── types.py
│   ├── layer1/
│   ├── layer2/
│   ├── layer3/
│   ├── layer4/
│   ├── layer5/
│   └── layer6/
├── requirements.txt
└── tests/
```

## Open-Source Upstream Snapshot (checked on 2026-04-14)

- Ray RLlib latest release tag: `Ray-2.54.1`
- Optuna latest release tag: `v4.8.0`
- XGBoost latest release tag: `v3.2.0`
- Prometheus latest release tag: `v3.11.2`
- Microsoft AIOpsLab: active repository, no formal GitHub release tags

Use these as version anchors when wiring production dependencies.

## Quick Start

1. Install requirements:

```bash
python3 -m pip install -r orchestrator_stack/requirements.txt
```

2. Train sample risk/demand models from synthetic datasets:

```bash
./.venv/bin/python orchestrator_stack/examples/generate_synthetic_assets.py

./.venv/bin/python orchestrator_stack/run.py train-risk \
  --dataset orchestrator_stack/examples/risk_train.npz \
  --out orchestrator_stack/examples/models/risk_model.json

./.venv/bin/python orchestrator_stack/run.py train-demand \
  --dataset orchestrator_stack/examples/demand_train.npz \
  --out orchestrator_stack/examples/models/demand_model.json
```

3. Run one end-to-end episode:

```bash
./.venv/bin/python orchestrator_stack/run.py run --config orchestrator_stack/config/orchestrator.example.json
```

4. Tune reward weights (`alpha`, `beta`, `gamma`):

```bash
./.venv/bin/python orchestrator_stack/run.py tune --config orchestrator_stack/config/orchestrator.example.json --trials 20
```

## Milestone Journey

See [`orchestrator_stack/MILESTONE_JOURNEY.md`](/Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/orchestrator_stack/MILESTONE_JOURNEY.md) for staged delivery from adapter integration to production-grade training.
