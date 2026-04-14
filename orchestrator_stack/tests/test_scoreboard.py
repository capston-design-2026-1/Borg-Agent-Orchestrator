from orchestrator.layer6.scoreboard import Scoreboard


def test_scoreboard_total():
    scoreboard = Scoreboard(alpha=1.0, beta=0.6, gamma=0.8)
    scoreboard.update({"AgentA": 10.0, "AgentB": 5.0, "AgentC": 2.0})
    assert round(scoreboard.total(), 3) == 14.6
