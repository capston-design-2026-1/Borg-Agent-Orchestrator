from orchestrator.layer4 import ppo_trainer


def test_train_curriculum_ppo_runs_each_stage_with_fresh_backend(monkeypatch, tmp_path):
    calls = []

    def backend_factory():
        return {"backend": len(calls)}

    def fake_train_multiagent_ppo(backend, **kwargs):
        calls.append({"backend": backend, **kwargs})
        return {"status": "trained", "episode_reward_mean": 1.0, "checkpoint": str(kwargs["output_dir"])}

    monkeypatch.setattr(ppo_trainer, "train_multiagent_ppo", fake_train_multiagent_ppo)

    result = ppo_trainer.train_curriculum_ppo(
        backend_factory,
        alpha=1.0,
        beta=0.6,
        gamma=0.8,
        stages=[
            {
                "train_iters": 1,
                "learning_rate": 3e-4,
                "train_batch_size": 32,
                "minibatch_size": 16,
                "num_epochs": 1,
                "rollout_fragment_length": 8,
            },
            {
                "train_iters": 2,
                "learning_rate": 2e-4,
                "train_batch_size": 64,
                "minibatch_size": 32,
                "num_epochs": 2,
                "rollout_fragment_length": 16,
            },
        ],
        output_dir=tmp_path,
    )

    assert result["status"] == "trained"
    assert result["stage_count"] == 2
    assert len(calls) == 2
    assert calls[0]["train_iters"] == 1
    assert calls[1]["train_batch_size"] == 64
