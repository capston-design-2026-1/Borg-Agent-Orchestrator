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

## Testing the Architecture

You can test the full 6-layer orchestrator stack using the provided CLI:

### 1. Build and Train Everything (Full Process)
This runs Layer 1 through Layer 6 in one go, including trace generation, XGBoost training, PPO smoke-training, and Optuna tuning:
```bash
python orchestrator_stack/run.py full-process \
  --config orchestrator_stack/config/orchestrator.example.json \
  --trials 3
```
After completion, check `reports/` for a KST-timestamped Optuna report (e.g., `202604142115_optuna_*.md`).

### 2. Run a Manual Episode (Sim Loop)
This runs the Layers 2-4-6 loop with heuristic agents to verify the simulator and reward feedback:
```bash
python orchestrator_stack/run.py run --config orchestrator_stack/config/orchestrator.example.json
```

### 3. Run Optuna Tuning Only
```bash
python orchestrator_stack/run.py tune \
  --config orchestrator_stack/config/orchestrator.example.json \
  --trials 20
```

### 4. Unit Tests
```bash
pytest orchestrator_stack/tests/
```

## Notes

- The default config uses `rllib_train_iters=1` for fast local smoke tests.
- Optuna studies are persisted at `orchestrator_stack/runtime/optuna/orchestrator.db`.
- PPO checkpoints are written under `orchestrator_stack/runtime/rllib`.
