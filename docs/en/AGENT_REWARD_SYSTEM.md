# Agent Reward System For Non-ML Developers

This document explains the "agent after model training" idea from the March 31 capstone meeting in plain engineering terms.

The short version is:

- `CatBoost` is the prediction model.
- The agent is the decision-maker that acts on the prediction.
- The reward system is how we evaluate whether that action was good or bad over time.

## 1. The Core Misunderstanding To Avoid

It is easy to think that once the model is trained, the project is finished:

1. collect telemetry
2. train `CatBoost`
3. predict failures

That is only the prediction layer.

The professor's feedback is asking for the next layer:

1. observe the system
2. predict what is likely to happen
3. choose an action
4. measure the result of that action
5. improve future actions using a reward signal

In other words, the model says "this machine or task looks risky," and the agent says "given that risk, what should the system do now?"

## 2. What Changes After CatBoost Training

After training, `CatBoost` should be treated as one component inside a larger control loop.

Example:

- Input: recent CPU, memory, task history, machine state
- `CatBoost` output: `failure_risk_15m = 0.87`
- Agent input: that `0.87` risk plus the current cluster state
- Agent output: choose an action such as:
  - do nothing
  - move a task
  - delay a placement
  - reduce overcommit on a node
  - evict a low-priority task
  - raise an alert for an operator

So the model predicts. The agent decides.

## 3. What The Reward System Actually Means

The reward system is not the same thing as the normal ML loss used to train `CatBoost`.

`CatBoost` training usually uses supervised-learning objectives such as:

- log loss
- AUC
- PR-AUC / average precision

Those metrics answer:

- "Did the model rank risky cases correctly?"
- "Did the model predict failures accurately?"

The reward system answers a different question:

- "Was the action taken by the agent beneficial for the real system?"

That is why the reward belongs to the action layer, not mainly to the prediction layer.

## 4. Simple Mental Model

A practical way to think about the pipeline is:

```text
System state -> CatBoost risk prediction -> Agent action -> System outcome -> Reward
```

Example:

1. The system sees a node with rising memory pressure.
2. `CatBoost` predicts high failure risk in the next 15 minutes.
3. The agent chooses to migrate one low-priority workload away from that node.
4. The node stays stable and no SLA-critical task is affected.
5. The agent receives a positive reward.

If the agent instead migrates too many workloads and causes unnecessary overhead, it should receive a lower reward or a penalty.

## 5. Why Prediction Alone Is Not Enough

Prediction alone only tells us that a problem may happen.

It does not answer:

- what action to take
- when to take it
- whether the action cost was worth it
- whether one action is better than another in repeated operation

For a systems project, that missing piece matters. A good cluster controller must make tradeoffs, not just forecasts.

## 6. What "Continuous" Means In This Project

The professor said the agent should be continuous.

In practice that means the controller should run as an ongoing loop instead of a one-time classifier:

1. observe current workload and node state
2. score risk with the trained model
3. choose an action
4. wait for the next state
5. compute reward from the observed outcome
6. repeat

This is the control-system view of the project.

The important idea is not that we must implement a full production reinforcement learning stack immediately. The important idea is that the system should be framed as repeated decision-making over time.

## 7. What The Professor Likely Means By "Reward"

A reward is a numeric score for the quality of an action.

Positive examples:

- avoided a node failure
- prevented an SLO or SLA violation
- reduced resource waste
- improved energy efficiency
- kept latency stable

Negative examples:

- caused unnecessary migration
- increased scheduling delay
- evicted an important task
- reduced throughput
- used too much control overhead to gain little benefit

The reward should reflect the actual project goal, not just prediction accuracy.

## 8. Example Reward Formula

For a failure-prevention scenario, a simple reward could be:

```text
reward
= + 10 * failure_avoided
-   3 * migration_cost
-   4 * latency_penalty
-   8 * sla_violation
-   2 * unnecessary_action
```

This is only an example, but it shows the structure:

- reward good outcomes
- penalize harmful side effects
- penalize wasteful interventions

## 9. Where Multi-Agent Fits

The professor also mentioned that agents should work with as little direct conversation as possible.

That usually means:

- agents share the same environment state
- agents infer what matters from common signals
- agents coordinate through system state rather than explicit message passing

In this project, that can look like:

- Predictor agent: produces failure-risk scores
- Placement agent: uses current cluster state plus risk scores to place workloads
- Recovery or eviction agent: acts only when pressure crosses a threshold

These agents do not need a chat channel. They can coordinate through shared observations such as:

- machine utilization
- predicted failure risk
- recent placement decisions
- priority and SLA level

## 10. A Good Capstone Framing

For a non-ML audience, the cleanest project explanation is:

### Layer 1. Prediction

`CatBoost` predicts near-term failure or overload risk from time-series and resource features.

### Layer 2. Decision

An agent chooses what action to take when risk is high.

### Layer 3. Evaluation

A reward function measures whether that action helped the system overall.

This framing is easier to defend than saying "the agent is just the model."

## 11. Suggested Object Definition

The meeting notes say the object must be more concrete.

A strong object definition would be something like:

- "Prevent near-term workload failure on shared compute nodes while minimizing intervention cost."

or:

- "Reduce overload-related failures in a cluster while preserving latency and scheduling efficiency."

This is better than saying only:

- "Predict failure."

Prediction is a tool. The system objective is operational improvement.

## 12. Concrete Example In This Repository

A repository-aligned example would be:

- Observation:
  - per-task CPU and memory history
  - node utilization
  - priority
  - scheduling class
- Predictor:
  - `CatBoost` outputs probability of failure within `5m`, `15m`, `30m`, `45m`, or `60m`
- Agent action:
  - no-op
  - avoid placing a new workload on a hot node
  - move a low-priority workload
  - evict a low-priority workload if the node is near collapse
- Reward:
  - positive if failure is prevented with low overhead
  - negative if the action causes more cost than benefit

## 13. What To Tell A Reviewer

If someone asks, "Why do you need agents after training CatBoost?", the short answer is:

`CatBoost` tells us what may happen. The agent decides what to do about it. The reward system tells us whether that decision improved the cluster in repeated operation.

## 14. Scope Control

For the capstone, it is reasonable to implement this in stages:

1. train the predictor
2. define a small action space
3. define a measurable reward
4. simulate or replay decisions on historical data
5. compare actions by system-level outcomes, not only by prediction metrics

That is enough to show the full idea without overcommitting to a large RL implementation too early.
