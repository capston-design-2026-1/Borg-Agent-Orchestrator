from pathlib import Path

from orchestrator.layer4.ppo_trainer import _pin_ray_storage_path


def test_pin_ray_storage_path_redirects_ray_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("RAY_AIR_LOCAL_CACHE_DIR", raising=False)

    storage = _pin_ray_storage_path(tmp_path)

    assert storage == str(tmp_path.resolve())
    assert storage == str(Path(storage))
    assert storage == str(Path(storage).resolve())

    import ray.train.constants as train_constants
    from ray._private import ray_constants
    from ray.tune.trainable import trainable as tune_trainable

    assert ray_constants.RAY_ENABLE_UV_RUN_RUNTIME_ENV is False
    assert train_constants.DEFAULT_STORAGE_PATH == storage
    assert tune_trainable.DEFAULT_STORAGE_PATH == storage
