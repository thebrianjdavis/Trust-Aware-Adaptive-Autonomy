"""Tests for repeated-experiment orchestration and summaries."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from config import SimulationConfig
from data.calibration.fema_distribution import FemaCalibrationData
from src.environment.models import Episode, Plan, PlanEvaluation
from src.simulation import experiment_runner


@pytest.fixture
def calibration_data() -> FemaCalibrationData:
    """Provide a deterministic one-category calibration distribution."""
    return FemaCalibrationData(["Fire"], [1.0], [1])


@pytest.mark.parametrize(
    ("requested_mode", "expected_mode"),
    [
        ("undertrust", "undertrust"),
        ("overtrust", "overtrust"),
        ("calibrated", "calibrated"),
        ("unrecognized", "calibrated"),
    ],
)
def test_zero_episode_summary_selects_policy_and_uses_zero_means(
    requested_mode: str,
    expected_mode: str,
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify empty runs select a valid policy and report zero-valued means."""
    summary = experiment_runner.run_trust_experiment(
        config=SimulationConfig(),
        num_episodes=0,
        supervisor_mode=requested_mode,
        calibration_data=calibration_data,
        verbose=False,
    )

    assert summary.supervisor_mode == expected_mode
    assert summary.num_episodes == 0
    assert summary.ai_wins == summary.baseline_wins == summary.ties == 0
    assert summary.ai_accepted == summary.ai_overridden == 0
    assert summary.mean_executed_utility == 0.0
    assert summary.mean_ai_confidence == 0.0
    assert summary.mean_override_rate == 0.0
    assert summary.mean_intervention_score == 0.0
    assert summary.final_trust == 0.5
    assert summary.trust_history == []


def test_calibration_data_is_loaded_when_not_supplied(
    monkeypatch: pytest.MonkeyPatch,
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify calibration data is loaded when the caller does not provide it."""
    loader = Mock(return_value=calibration_data)
    monkeypatch.setattr(experiment_runner, "load_fema_calibration_data", loader)

    experiment_runner.run_trust_experiment(
        SimulationConfig(),
        num_episodes=0,
        calibration_data=None,
        verbose=False,
    )

    loader.assert_called_once_with(Path("data/raw/us_disaster_declarations.csv"))


def test_adaptive_experiment_tracks_all_outcomes_and_strengths(
    monkeypatch: pytest.MonkeyPatch,
    calibration_data: FemaCalibrationData,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify adaptive runs summarize wins, choices, strengths, and output."""
    episode = Episode([], [], 0)
    baseline_plan = Plan("baseline")
    ai_plan = Plan("ai")
    monkeypatch.setattr(experiment_runner, "generate_episode", Mock(return_value=episode))
    monkeypatch.setattr(
        experiment_runner,
        "create_baseline_plan",
        Mock(return_value=baseline_plan),
    )
    monkeypatch.setattr(
        experiment_runner,
        "create_ai_plan",
        Mock(return_value=ai_plan),
    )
    evaluations = [
        PlanEvaluation("baseline", 10, [], []),
        PlanEvaluation("ai", 20, [], []),
        PlanEvaluation("baseline", 20, [], []),
        PlanEvaluation("ai", 10, [], []),
        PlanEvaluation("baseline", 10, [], []),
        PlanEvaluation("ai", 10, [], []),
    ]
    evaluate_mock = Mock(side_effect=evaluations)
    monkeypatch.setattr(experiment_runner, "evaluate_plan", evaluate_mock)
    monkeypatch.setattr(
        experiment_runner,
        "estimate_plan_confidence",
        Mock(side_effect=[0.1, 0.6, 1.0]),
    )
    decisions = iter([False, False, True])

    def accept_in_sequence(self: object, **kwargs: object) -> bool:
        """Return the next deterministic supervisor decision."""
        return next(decisions)

    monkeypatch.setattr(
        experiment_runner.CalibratedSupervisorPolicy,
        "accept_ai_plan",
        accept_in_sequence,
    )

    summary = experiment_runner.run_trust_experiment(
        config=SimulationConfig(seed=7),
        num_episodes=3,
        supervisor_mode="calibrated",
        autonomy_mode="adaptive",
        calibration_data=calibration_data,
        verbose=True,
    )

    assert summary.ai_wins == 1
    assert summary.baseline_wins == 1
    assert summary.ties == 1
    assert summary.ai_accepted == 1
    assert summary.ai_overridden == 2
    assert summary.weak_recommendations == 1
    assert summary.normal_recommendations == 1
    assert summary.strong_recommendations == 1
    assert summary.mean_executed_utility == pytest.approx(40 / 3)
    assert summary.mean_ai_confidence == pytest.approx(1.7 / 3)
    assert summary.mean_override_rate == pytest.approx((0.5 + 0.6 + 2 / 3) / 3)
    assert summary.final_trust == 0.5
    assert summary.trust_history == [0.6, 0.5, 0.5]
    assert evaluate_mock.call_count == 6

    output = capsys.readouterr().out
    assert "Episode 1:" in output
    assert "comparison=AI_WIN" in output
    assert "comparison=BASELINE_WIN" in output
    assert "comparison=TIE" in output
    assert "=== SUMMARY ===" in output
    assert "Strong recommendations: 1" in output


def test_fixed_experiment_always_logs_normal_recommendation(
    monkeypatch: pytest.MonkeyPatch,
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify fixed runs record only normal-strength recommendations."""
    episode = Episode([], [], 0)
    monkeypatch.setattr(experiment_runner, "generate_episode", Mock(return_value=episode))
    monkeypatch.setattr(
        experiment_runner,
        "create_baseline_plan",
        Mock(return_value=Plan("baseline")),
    )
    monkeypatch.setattr(
        experiment_runner,
        "create_ai_plan",
        Mock(return_value=Plan("ai")),
    )
    monkeypatch.setattr(
        experiment_runner,
        "evaluate_plan",
        Mock(
            side_effect=[
                PlanEvaluation("baseline", 5, [], []),
                PlanEvaluation("ai", 10, [], []),
            ]
        ),
    )
    monkeypatch.setattr(
        experiment_runner,
        "estimate_plan_confidence",
        Mock(return_value=0.8),
    )
    monkeypatch.setattr(
        experiment_runner.CalibratedSupervisorPolicy,
        "accept_ai_plan",
        lambda self, **kwargs: True,
    )

    summary = experiment_runner.run_trust_experiment(
        SimulationConfig(),
        num_episodes=1,
        autonomy_mode="fixed",
        calibration_data=calibration_data,
        verbose=False,
    )

    assert summary.normal_recommendations == 1
    assert summary.weak_recommendations == 0
    assert summary.strong_recommendations == 0
    assert summary.ai_accepted == 1
    assert summary.mean_executed_utility == 10.0
    assert summary.mean_intervention_score == 0.8
