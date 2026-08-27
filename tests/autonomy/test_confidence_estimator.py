"""Tests for AI plan confidence estimation."""

import pytest

from src.autonomy.confidence_estimator import (
    build_asset_lookup,
    build_incident_lookup,
    clamp_confidence,
    compute_assignment_confidence,
    estimate_plan_confidence,
)
from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment


def test_lookup_builders_index_episode_objects(sample_episode: Episode) -> None:
    incident_lookup = build_incident_lookup(sample_episode)
    asset_lookup = build_asset_lookup(sample_episode)

    assert incident_lookup == {
        incident.incident_id: incident for incident in sample_episode.incidents
    }
    assert asset_lookup == {asset.asset_id: asset for asset in sample_episode.assets}


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-0.1, 0.0), (0.6, 0.6), (1.1, 1.0)],
)
def test_clamp_confidence(value: float, expected: float) -> None:
    assert clamp_confidence(value) == expected


def test_medical_specialist_receives_bonus(
    medical_incident: Incident,
    medical_asset: Asset,
    medical_assignment: PlanAssignment,
) -> None:
    assert compute_assignment_confidence(
        medical_incident,
        medical_asset,
        medical_assignment,
    ) == pytest.approx(0.8)


def test_logistics_specialist_receives_bonus() -> None:
    incident = Incident("I2", 10, 1, 0, 3, 0.6, "logistics")
    asset = Asset("A2", {"logistics"}, {0, 1, 2})
    assignment = PlanAssignment("I2", "A2", 0, 1)

    assert compute_assignment_confidence(incident, asset, assignment) == pytest.approx(
        0.7
    )


def test_flexible_asset_gets_no_bonus_and_late_start_penalty(
    medical_incident: Incident,
    flexible_asset: Asset,
) -> None:
    assignment = PlanAssignment("I1", "A3", 4, 6)

    assert compute_assignment_confidence(
        medical_incident,
        flexible_asset,
        assignment,
    ) == pytest.approx(0.6)


def test_zero_slack_skips_delay_penalty() -> None:
    incident = Incident("I1", 10, 2, 1, 3, 0.4, "other")
    asset = Asset("X", {"other"}, {1, 2})
    assignment = PlanAssignment("I1", "X", 1, 3)

    assert compute_assignment_confidence(incident, asset, assignment) == 0.4


def test_assignment_confidence_is_clamped() -> None:
    high_incident = Incident("high", 10, 1, 0, 1, 0.99, "medical")
    high_asset = Asset("A1", {"medical"}, {0})
    high_assignment = PlanAssignment("high", "A1", 0, 1)
    low_incident = Incident("low", 10, 1, 0, 2, 0.01, "other")
    low_asset = Asset("X", {"other"}, {0, 1})
    low_assignment = PlanAssignment("low", "X", 1, 2)

    assert compute_assignment_confidence(
        high_incident,
        high_asset,
        high_assignment,
    ) == 1.0
    assert compute_assignment_confidence(low_incident, low_asset, low_assignment) == 0.0


def test_empty_plan_has_zero_confidence(sample_episode: Episode) -> None:
    assert estimate_plan_confidence(sample_episode, Plan("empty")) == 0.0


def test_plan_confidence_is_assignment_mean(sample_episode: Episode) -> None:
    plan = Plan(
        "ai",
        [
            PlanAssignment("I1", "A1", 1, 3),
            PlanAssignment("I2", "A2", 3, 4),
        ],
    )

    # I1: 0.7 + 0.1 bonus. I2: 0.5 + 0.1 bonus - 0.1 late penalty.
    assert estimate_plan_confidence(sample_episode, plan) == pytest.approx(0.65)
