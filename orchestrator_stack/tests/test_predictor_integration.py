from orchestrator.layer2.simulator import PredictorAttachedBackend
from orchestrator.types import ActionKind, AgentAction, NodeState, Observation, StepResult, TaskState


class _FixedPredictor:
    def __init__(self, value: float):
        self.value = value

    def predict(self, obs: Observation) -> dict[str, float]:
        return {node.node_id: self.value for node in obs.nodes}


class _TinyBackend:
    def __init__(self):
        self._step = 0

    def reset(self) -> Observation:
        self._step = 0
        return _make_obs(timestamp=100)

    def step(self, action: AgentAction) -> StepResult:
        self._step += 1
        return StepResult(
            next_observation=_make_obs(timestamp=100 + self._step),
            reward_by_agent={"AgentA": 1.0, "AgentB": 1.0, "AgentC": 1.0},
            done=self._step >= 1,
            info={"agent": action.agent_name},
        )


def _make_obs(timestamp: int) -> Observation:
    return Observation(
        timestamp=timestamp,
        nodes=[NodeState(node_id="n1", cpu_util=0.5, mem_util=0.4, disk_util=0.3, net_util=0.2)],
        tasks=[TaskState(task_id="t1", node_id="n1", urgency=0.6, queue_priority=2)],
        p_fail_scores={},
        demand_projection={},
        queue_length=1,
        energy_price=0.1,
    )


def test_predictor_attached_backend_enriches_reset_and_step_observation():
    backend = PredictorAttachedBackend(
        backend=_TinyBackend(),
        risk_model=_FixedPredictor(0.73),
        demand_model=_FixedPredictor(0.27),
    )

    reset_obs = backend.reset()
    assert reset_obs.p_fail_scores == {"n1": 0.73}
    assert reset_obs.demand_projection == {"n1": 0.27}

    step_result = backend.step(AgentAction(agent_name="AgentA", kind=ActionKind.NOOP))
    assert step_result.next_observation.p_fail_scores == {"n1": 0.73}
    assert step_result.next_observation.demand_projection == {"n1": 0.27}
