from pathlib import Path

from orchestrator.config import OrchestratorConfig
from orchestrator.main import ensure_brain_models_exist


def test_ensure_brain_models_exist_trains_missing_models(tmp_path: Path):
    cfg = OrchestratorConfig(
        trace_path=Path("orchestrator_stack/examples/sample_trace.json"),
        risk_model_path=tmp_path / "risk_model.json",
        demand_model_path=tmp_path / "demand_model.json",
    )

    result = ensure_brain_models_exist(cfg)

    assert cfg.risk_model_path.exists()
    assert cfg.demand_model_path.exists()
    assert result["risk_model"] == str(cfg.risk_model_path)
    assert result["demand_model"] == str(cfg.demand_model_path)
