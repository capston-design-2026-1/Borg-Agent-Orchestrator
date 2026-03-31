# Baseline vs XGBoost: Why The Reported Precision Looks So Different

Timestamp: `2026-03-31 15:03 KST`

## Short Answer

The large gap is mostly explained by **what population was evaluated**, not just by model quality.

- The earlier baseline report was evaluated on a **full validation set** with extreme class imbalance.
- The current XGBoost report was evaluated on a **sampled validation set** where:
  - all positive rows were kept
  - many negative rows were removed

Because precision is "how many selected rows are truly positive," removing a large share of negatives makes precision look much higher even if the ranking model itself is only moderately better.

This means:

- the formulas for precision and recall are basically correct in both pipelines
- but the two reports are **not directly comparable as-is**

## What "Positives Kept, Negatives Not Kept" Means

For a non-ML reader, think about an inbox with spam detection:

- `positive` means "this is an important message we care about finding"
- `negative` means "this is a normal message"

Now imagine two different evaluation methods:

### Method A: Full inbox

You test the model on all messages:

- 10 important messages
- 99,990 normal messages

This is the real-world distribution.

### Method B: Reduced inbox

You keep all 10 important messages, but instead of keeping all 99,990 normal messages, you keep only 2,500 of them.

Now the test set has:

- 10 important messages
- 2,500 normal messages

The task becomes much easier to look good on, because there are far fewer negatives left to compete with.

That is what happened in the XGBoost trainer:

- all positive validation rows were preserved
- only a fraction of negative validation rows were kept

This makes the validation set much denser in positives than the original raw data.

## Why Precision Changes So Much

Precision answers:

> Of the rows the model selected as highest risk, how many were truly positive?

If your evaluation set contains fewer negative rows, then the top-ranked slice will naturally contain a larger fraction of positives.

So even if the model ranking is good, the absolute precision value becomes more optimistic.

That is why the XGBoost report can show values like:

- `precision@1% ≈ 0.995`

while the earlier baseline showed:

- `precision@1% ≈ 0.007`

Those numbers are not living in the same evaluation world.

## Concrete Numbers From Your Repository

### Earlier baseline report

From [`reports/202603191915_forecaster_evaluation.md`](/Users/theokim/Documents/github/kyunghee/Borg-Agent-Orchestrator/reports/202603191915_forecaster_evaluation.md):

- validation rows: `4,810,777`
- validation positives: `1,448`
- validation positive rate: `0.0301%`
- precision@1%: `0.0070676`
- recall@1%: `0.2348066`

This means:

- the validation set was overwhelmingly negative
- only about `0.03%` of rows were positive
- that is why precision remained very low in absolute terms

### XGBoost 15-minute report

From `~/Documents/borg_xgboost_workspace/models/xgboost/xgboost_failure_risk_target_failure_15m/metrics.json`:

- source validation rows: `76,991,970`
- sampled validation rows: `2,000,815`
- validation positives: `61,707`
- validation negative keep fraction: `0.025195...`
- precision@1%: `0.995102...`
- recall@1%: `0.322670...`

Important interpretation:

- the original validation set had about `77M` rows
- only about `2.5%` of negatives were kept
- all positives were kept

So the reported validation population is not the same as the original full raw validation population.

## Are The Formulas Wrong?

### Baseline

The baseline metric implementation is mathematically normal for ranking metrics:

- precision@k:
  - sort by `risk_score`
  - take top `k`
  - compute positives / selected rows
- recall@k:
  - sort by `risk_score`
  - take top `k`
  - compute recovered positives / all positives in validation
- average precision:
  - standard rank-based average precision

### XGBoost

The XGBoost metric formulas are also basically normal:

- precision@k uses the sampled validation frame
- recall@k uses the sampled validation frame
- average precision uses the sampled validation frame

So the math is not the main problem.

## Then What Is The Real Problem?

The main problem is **evaluation population mismatch**.

The baseline metrics and the XGBoost metrics are answering two different questions:

### Baseline question

> If I rank the full validation population, how precise is the top 1% slice?

### XGBoost question

> If I rank a validation population where almost all positives are kept but most negatives are removed, how precise is the top 1% slice?

Those are not the same experiment.

## Why Recall Also Changes

Recall is less sensitive than precision to negative downsampling, but it is still affected.

Reason:

- recall@k depends on how many positives are recovered in the top slice
- the top slice size itself is based on the sampled validation size

If the validation set becomes much smaller because negatives were removed, then:

- the top `1%` slice contains far fewer total rows
- but the positive density of the sampled set is much higher

So recall is not directly comparable either unless both systems are evaluated on the same population.

## What Is Still Legitimately Better About XGBoost

Even after correcting for the comparison issue, XGBoost can still genuinely be better.

Why:

- it is a much stronger model class than the earlier linear-style baseline
- it uses many more interaction patterns
- it uses temporal features and missingness indicators more flexibly
- the large training corpus is richer than the small earlier baseline setup

So "the model is probably better" and "the reported precision is inflated by validation sampling" can both be true at the same time.

## Best Interpretation Right Now

The safest interpretation is:

1. The XGBoost model is probably learning a better ranking than the old baseline.
2. The current XGBoost precision and average precision values are **optimistic** because evaluation is happening on a sampled validation set.
3. You should not compare `0.7% precision` from the old report directly against `99% precision` from the new report and conclude the model improved by two orders of magnitude.

## What Should Be Done Next

To make the comparison fair:

1. Keep sampled negatives during training if needed for memory/runtime.
2. But evaluate the trained XGBoost model on a **full unsampled validation set**.
3. Recompute:
   - precision@0.1%
   - recall@0.1%
   - precision@1%
   - recall@1%
   - PR-AUC / average precision
   - ROC-AUC if desired
4. Then compare baseline vs XGBoost on the same validation population.

That will answer the real product question:

> Is XGBoost actually better under the full real-world class imbalance?

## Remaining Risks

- Current XGBoost metrics are not apples-to-apples against the old baseline report.
- Clusters `e`, `f`, and `g` currently contribute zero positives in the fixed-shard advanced slice.
- The sampled validation design is useful for tractable training, but it should not be mistaken for final deployment-quality evaluation.
- The bilingual evaluation reports already present the XGBoost results clearly, but they should eventually be updated once full-population evaluation is added.

## Bottom Line

The earlier low precision was not necessarily because the old model was "broken."

It was largely because:

- the validation population was extremely imbalanced
- metrics were computed on the full raw distribution

The new XGBoost precision is not necessarily "wrong," but it is not directly comparable because:

- positives were all kept
- many negatives were removed before evaluation

So the likely answer is:

- neither implementation is mainly wrong in formula
- the current comparison is misleading because the evaluation populations are different
