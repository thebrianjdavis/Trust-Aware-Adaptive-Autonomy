"""Tests for assignment-sensitive outcome simulation."""

from unittest.mock import Mock, call

import pytest

from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment
from src.simulation import outcome_simulator


def test_lookup_builders_index_episode_objects(sample_episode: Episode) -> None:
    assert outcome_simulator.build_incident_lookup(sample_episode) == {
        incident.incident_id: incident for incident in sample_episode.incidents
    }
    assert outcome_simulator.build_asset_lookup(sample_episode) == {
        asset.asset_id: asset for asset in sample_episode.assets
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-1.0, 0.0), (0.4, 0.4), (2.0, 1.0)],
)
def test_clamp_probability(value: float, expected: float) -> None:
    assert outcome_simulator.clamp_probability(value) == expected


def test_medical_specialist_probability_bonus(
    medical_incident: Incident,
    medical_asset: Asset,
    medical_assignment: PlanAssignment,
) -> None:
    assert outcome_simulator.compute_adjusted_success_probability(
        medical_incident,
        medical_asset,
        medical_assignment,
    ) == pytest.approx(0.8)


def test_logistics_specialist_probability_bonus() -> None:
    incident = Incident("I2", 10, 1, 0, 3, 0.6, "logistics")
    asset = Asset("A2", {"logistics"}, {0, 1, 2})
    assignment = PlanAssignment("I2", "A2", 0, 1)

    assert outcome_simulator.compute_adjusted_success_probability(
        incident,
        asset,
        assignment,
    ) == pytest.approx(0.7)


def test_flexible_asset_has_no_bonus_and_late_penalty(
    medical_incident: Incident,
    flexible_asset: Asset,
) -> None:
    assignment = PlanAssignment("I1", "A3", 4, 6)

    assert outcome_simulator.compute_adjusted_success_probability(
        medical_incident,
        flexible_asset,
        assignment,
    ) == pytest.approx(0.6)


def test_zero_slack_skips_probability_penalty() -> None:
    incident = Incident("I1", 10, 2, 1, 3, 0.4, "other")
    asset = Asset("X", {"other"}, {1, 2})
    assignment = PlanAssignment("I1", "X", 1, 3)

    assert outcome_simulator.compute_adjusted_success_probability(
        incident,
        asset,
        assignment,
    ) == 0.4


def test_adjusted_probability_is_clamped() -> None:
    high_incident = Incident("high", 10, 1, 0, 1, 0.99, "medical")
    high_asset = Asset("A1", {"medical"}, {0})
    high_assignment = PlanAssignment("high", "A1", 0, 1)
    low_incident = Incident("low", 10, 1, 0, 2, 0.01, "other")
    low_asset = Asset("X", {"other"}, {0, 1})
    low_assignment = PlanAssignment("low", "X", 1, 2)

    assert outcome_simulator.compute_adjusted_success_probability(
        high_incident,
        high_asset,
        high_assignment,
    ) == 1.0
    assert outcome_simulator.compute_adjusted_success_probability(
        low_incident,
        low_asset,
        low_assignment,
    ) == 0.0


def test_evaluate_plan_records_successes_failures_and_utility() -> None:
    successful = Incident("success", 15, 1, 0, 1, 1.0, "medical")
    failed = Incident("failure", 20, 1, 0, 1, 0.0, "logistics")
    assets = [
        Asset("A1", {"medical"}, {0}),
        Asset("A2", {"logistics"}, {0}),
    ]
    episode = Episode([successful, failed], assets, 1)
    plan = Plan(
        "test",
        [
            PlanAssignment("success", "A1", 0, 1),
            PlanAssignment("failure", "A2", 0, 1),
        ],
    )

    evaluation = outcome_simulator.evaluate_plan(episode, plan, seed=7)

    assert evaluation.plan_name == "test"
    assert evaluation.total_utility == 15
    assert evaluation.successful_incident_ids == ["success"]
    assert evaluation.failed_incident_ids == ["failure"]


def test_evaluate_plan_is_reproducible(sample_episode: Episode) -> None:
    plan = Plan(
        "ai",
        [
            PlanAssignment("I1", "A1", 1, 3),
            PlanAssignment("I2", "A2", 0, 1),
        ],
    )

    assert outcome_simulator.evaluate_plan(
        sample_episode,
        plan,
        123,
    ) == outcome_simulator.evaluate_plan(sample_episode, plan, 123)


def test_shared_outcome_evaluation_derives_distinct_seeds(
    monkeypatch: pytest.MonkeyPatch,
    sample_episode: Episode,
) -> None:
    baseline_plan = Plan("baseline")
    ai_plan = Plan("ai")
    baseline_result = Mock()
    ai_result = Mock()
    evaluate_mock = Mock(side_effect=[baseline_result, ai_result])
    monkeypatch.setattr(outcome_simulator, "evaluate_plan", evaluate_mock)

    result = outcome_simulator.evaluate_plans_under_shared_outcomes(
        sample_episode,
        baseline_plan,
        ai_plan,
        seed=100,
    )

    assert result == (baseline_result, ai_result)
    assert evaluate_mock.call_args_list == [
        call(episode=sample_episode, plan=baseline_plan, seed=101),
        call(episode=sample_episode, plan=ai_plan, seed=102),
    ]
