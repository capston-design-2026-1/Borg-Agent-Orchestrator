"""Layer 4: agents, policy spaces, referee, and RL wrappers."""

from orchestrator.layer4.agents import AgentARiskMitigator, AgentBEfficiencyOptimizer, AgentCGatekeeper
from orchestrator.layer4.policy import POLICY_SPACES, decode_agent_action, default_policy_actions
from orchestrator.layer4.referee import resolve

try:  # pragma: no cover - optional training/runtime dependencies
    from orchestrator.layer4.ppo_trainer import evaluate_heuristic_policy, train_multiagent_ppo
    from orchestrator.layer4.rllib_env import OrchestratorMultiAgentEnv
except Exception:  # pragma: no cover
    evaluate_heuristic_policy = None  # type: ignore[assignment]
    train_multiagent_ppo = None  # type: ignore[assignment]
    OrchestratorMultiAgentEnv = None  # type: ignore[assignment]

__all__ = [
    "AgentARiskMitigator",
    "AgentBEfficiencyOptimizer",
    "AgentCGatekeeper",
    "POLICY_SPACES",
    "decode_agent_action",
    "default_policy_actions",
    "evaluate_heuristic_policy",
    "train_multiagent_ppo",
    "resolve",
    "OrchestratorMultiAgentEnv",
]
