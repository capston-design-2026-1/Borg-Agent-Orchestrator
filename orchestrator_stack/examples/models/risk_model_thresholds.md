# Risk Model Thresholds

- Model artifact: `orchestrator_stack/examples/models/risk_model.json`
- Diagnostics report: `reports/evaluations/202604281534_orchestrator_risk_model_diagnostics.json`
- Selected threshold: `0.05`
- Selection metric: F1
- Validation F1: `0.45818692902319047`
- Validation precision: `0.7293064876957495`
- Validation recall: `0.33401639344262296`
- Status: diagnostic only, not production ready

The threshold is recorded from `diagnose-brain` output for reproducibility. The low validation F1 means the synthetic/example booster should not be promoted without retraining or calibration on representative traces.
