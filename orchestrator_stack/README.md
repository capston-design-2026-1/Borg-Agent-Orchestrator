# Full Orchestrator Stack (Isolated Workspace)

This directory implements the full 6-layer orchestrator process end-to-end:

1. Local source ingestion (`Prometheus/JSON` -> trace file)
2. AIOpsLab-style simulator backend + feature extraction
3. XGBoost safety-risk and demand predictors
4. MARL policy layer (PPO-compatible action interface) + referee
5. Optuna trial manager for reward and policy hyperparameters
6. Scoreboard feedback loop into policy/trial evaluation

Architecture diagrams: [ARCHITECTURE.md](ARCHITECTURE.md) | [Visual (mmd)](architecture.mmd)

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

## Getting Started from Scratch

Follow these steps to initialize the environment and run the full orchestrator stack.

### 1. Prerequisites
- **Python 3.10 to 3.13** (Note: Ray does not yet support 3.14+)
- **Git**

### 2. Initialize Virtual Environment
From the repository root, create and activate the virtual environment. **Note:** Use Python 3.10-3.13 (e.g., `python3.13`) as Ray does not yet support 3.14.

**Important:** If you previously created a `.venv` with a different Python version, you must remove it first: `rm -rf .venv`

```bash
python3.13 -m venv .venv  # Recommended
...
python3.12 -m venv .venv
# THEN
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r orchestrator_stack/requirements.txt
```

### 4. Generate Initial Assets (Synthetic Data & Models)
Before running the orchestrator, you must generate the synthetic trace and training datasets:
```bash
# Generate metrics, traces, and datasets
./.venv/bin/python orchestrator_stack/examples/generate_synthetic_assets.py
```

Layer 1 ingestion now enforces strict contracts for `.json` and `.jsonl` trace sources:

- rejects mixed flat/grouped metrics row shapes during trace build
- rejects malformed JSON/JSONL with file/line context
- validates required trace keys (`timestamp`, `nodes`, `tasks`) before Layer 2/3 usage

See `orchestrator_stack/examples/README.md` for the concise schema contract.

Layer 2 now normalizes AIOpsLab-style nested payloads into the shared `Observation` contract before simulator replay and feature extraction. Supported adapter-friendly shapes include nested wrappers such as `snapshot/state/observation`, dict-backed `machines`/`pods`, and alternate score fields such as `risk_scores` and `demand_scores`.

### 5. Train the Predictor Models (Layer 3)
Train the XGBoost safety-risk and resource-demand models from the generated trace:
```bash
./.venv/bin/python orchestrator_stack/run.py train-brains \
  --trace orchestrator_stack/examples/sample_trace.json \
  --risk-out orchestrator_stack/examples/models/risk_model.json \
  --demand-out orchestrator_stack/examples/models/demand_model.json
```

## Testing the Architecture

You can test the full 6-layer orchestrator stack using the provided CLI:

### 1. Build and Train Everything (Full Process)
This runs Layer 1 through Layer 6 in one go using the project virtual environment:
```bash
./.venv/bin/python orchestrator_stack/run.py full-process \
  --config orchestrator_stack/config/orchestrator.example.json \
  --trials 3
```
After completion, check `reports/` for a KST-timestamped Optuna report (e.g., `202604142115_optuna_*.md`).

### 2. Run a Manual Episode (Sim Loop)
```bash
./.venv/bin/python orchestrator_stack/run.py run --config orchestrator_stack/config/orchestrator.example.json
```

### 3. Run Optuna Tuning Only
```bash
./.venv/bin/python orchestrator_stack/run.py tune \
  --config orchestrator_stack/config/orchestrator.example.json \
  --trials 20
```

### 4. Unit Tests
```bash
./.venv/bin/pytest orchestrator_stack/tests/
```

## Viewing Logs and Decision Traces

The orchestrator now provides verbose step-by-step logging of agent decisions. When running the `run` or `full-process` commands, look for the following output in your terminal:

- **Proposals:** The raw actions suggested by the Risk, Efficiency, and Admission agents.
- **Referee:** The final action chosen after conflict resolution.
- **Rewards:** The score impact for each agent (e.g., `AgentA:+11.0` indicates a successful preemptive migration).

To see more training logs from Ray RLlib, increase the `"rllib_train_iters"` value in your `.json` config.

## Notes

- The default config uses `rllib_train_iters=1` for fast local smoke tests.
- Optuna studies are persisted at `orchestrator_stack/runtime/optuna/orchestrator.db`.
- PPO checkpoints are written under `orchestrator_stack/runtime/rllib`.
