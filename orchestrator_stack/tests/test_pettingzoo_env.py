from orchestrator.layer4.pettingzoo_env import OrchestratorParallelEnv
from orchestrator.types import ActionKind, AgentAction, NodeState, Observation, StepResult, TaskState


class StubBackend:
    def reset(self) -> Observation:
        return Observation(
            timestamp=1,
            nodes=[
                NodeState("node-1", 0.9, 0.8, 0.2, 0.1),
                NodeState("node-2", 0.2, 0.2, 0.1, 0.1),
            ],
            tasks=[TaskState("task-1", "node-1", urgency=0.9, queue_priority=2, alive=True)],
            p_fail_scores={"node-1": 0.92, "node-2": 0.1},
            demand_projection={"node-1": 0.8, "node-2": 0.2},
            queue_length=20,
            energy_price=0.1,
        )

    def step(self, action: AgentAction) -> StepResult:
        assert action.agent_name == "AgentA"
        assert action.kind == ActionKind.MIGRATE
        return StepResult(
            next_observation=self.reset(),
            reward_by_agent={"AgentA": 10.0, "AgentB": 1.0, "AgentC": 1.0},
            done=True,
            info={"status": "stubbed"},
        )


def test_parallel_env_wraps_multi_agent_step_without_all_key():
    env = OrchestratorParallelEnv({"backend": StubBackend(), "alpha": 1.0, "beta": 0.6, "gamma": 0.8})
    observations, infos = env.reset()

    assert set(observations) == {"AgentA", "AgentB", "AgentC"}
    assert infos == {}

    _, rewards, terminations, truncations, infos = env.step({"AgentA": 1, "AgentB": 0, "AgentC": 0})

    assert rewards["AgentA"] == 10.0
    assert terminations == {"AgentA": True, "AgentB": True, "AgentC": True}
    assert truncations == {"AgentA": False, "AgentB": False, "AgentC": False}
    assert "__all__" not in terminations
    assert env.agents == []
    assert infos["AgentA"]["resolved_action"]["kind"] == "migrate"
