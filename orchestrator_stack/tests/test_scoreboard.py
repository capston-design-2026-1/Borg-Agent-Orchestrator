from orchestrator.layer6.scoreboard import Scoreboard


def test_scoreboard_total():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8)
    update = scoreboard.update({"AgentA": 10.0, "AgentB": 5.0, "AgentC": 2.0})
    assert round(scoreboard.total(), 3) == 14.6
    assert round(update.score.total, 3) == 14.6
    assert round(update.feedback.global_score, 3) == 14.6


def test_scoreboard_feedback_boosts_lagging_agents():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8, feedback_gain=0.3, team_spirit=0.1)
    scoreboard.update({"AgentA": 12.0, "AgentB": 0.0, "AgentC": 0.0})
    update = scoreboard.update({"AgentA": 1.0, "AgentB": 2.0, "AgentC": 2.0})

    assert update.feedback.agent_weights["AgentA"] < 1.0
    assert update.feedback.agent_weights["AgentB"] > 1.0
    assert update.feedback.agent_weights["AgentC"] > 1.0
    assert scoreboard.snapshot()["balance_gap"] > 0.0


def test_scoreboard_reset_clears_feedback_history():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8)
    scoreboard.update({"AgentA": 3.0, "AgentB": 1.0, "AgentC": 0.0})
    scoreboard.reset()

    assert scoreboard.total() == 0.0
    assert scoreboard.adjusted_total() == 0.0
    assert scoreboard.latest_feedback() is None


def test_scoreboard_current_feedback_is_neutral_before_first_step():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8)

    feedback = scoreboard.current_feedback()

    assert feedback.global_score == 0.0
    assert feedback.agent_weights == {"AgentA": 1.0, "AgentB": 1.0, "AgentC": 1.0}
    assert scoreboard.observation_features("AgentA") == (0.5, 0.0, 0.5, 0.5)


def test_scoreboard_observation_features_reflect_agent_imbalance():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8, feedback_gain=0.3)
    scoreboard.update({"AgentA": 12.0, "AgentB": 0.0, "AgentC": 0.0})

    agent_a = scoreboard.observation_features("AgentA")
    agent_b = scoreboard.observation_features("AgentB")

    assert agent_a[2] < 0.5
    assert agent_b[2] > 0.5
    assert agent_a[3] < 0.5
    assert agent_b[3] > 0.5
