from orchestrator.layer3.diagnostics import calibration_bins, optimize_binary_threshold


def test_optimize_binary_threshold_returns_best_f1_cutoff():
    result = optimize_binary_threshold([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])

    assert 0.2 < result["threshold"] <= 0.8
    assert result["f1"] == 1.0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0


def test_calibration_bins_reports_predicted_and_observed_rates():
    bins = calibration_bins([0, 1, 1], [0.1, 0.6, 0.8], bins=2)

    assert bins[0]["count"] == 1
    assert bins[0]["observed_rate"] == 0.0
    assert bins[1]["count"] == 2
    assert bins[1]["observed_rate"] == 1.0
