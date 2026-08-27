"""Tests for the uncertainty-aware AI planner."""

import pytest

from src.environment.models import Asset, Episode, Incident
from src.planners import ai_planner


def test_build_asset_occupancy_map(
    medical_asset: Asset,
    logistics_asset: Asset,
) -> None:
    """Verify that every asset receives an independent occupancy set."""
    occupancy = ai_planner.build_asset_occupancy_map(
        [medical_asset, logistics_asset]
    )

    assert occupancy == {"A1": set(), "A2": set()}
    assert occupancy["A1"] is not occupancy["A2"]


def test_get_candidate_start_times(medical_incident: Incident) -> None:
    """Verify candidate starts span the incident's feasible window."""
    assert ai_planner.get_candidate_start_times(medical_incident) == [1, 2, 3, 4]


def test_assignment_is_feasible(
    medical_incident: Incident,
    medical_asset: Asset,
) -> None:
    """Verify acceptance of a compatible assignment with open time slots."""
    assert ai_planner.is_assignment_feasible(
        medical_incident,
        medical_asset,
        1,
        {"A1": set()},
    )


def test_assignment_rejects_incompatible_asset(
    medical_incident: Incident,
    logistics_asset: Asset,
) -> None:
    """Verify rejection of an asset without the required capability."""
    assert not ai_planner.is_assignment_feasible(
        medical_incident,
        logistics_asset,
        1,
        {"A2": set()},
    )


def test_assignment_rejects_unavailable_slots(medical_incident: Incident) -> None:
    """Verify rejection when the asset is unavailable during the assignment."""
    asset = Asset("A1", {"medical"}, {1})

    assert not ai_planner.is_assignment_feasible(
        medical_incident,
        asset,
        1,
        {"A1": set()},
    )


def test_assignment_rejects_occupied_slots(
    medical_incident: Incident,
    medical_asset: Asset,
) -> None:
    """Verify rejection when the assignment overlaps occupied slots."""
    assert not ai_planner.is_assignment_feasible(
        medical_incident,
        medical_asset,
        1,
        {"A1": {2}},
    )


def test_compute_incident_score(medical_incident: Incident) -> None:
    """Verify the priority, probability, and duration scoring formula."""
    assert ai_planner.compute_incident_score(medical_incident) == pytest.approx(4.2)


def test_count_compatible_assets(
    medical_incident: Incident,
    medical_asset: Asset,
    logistics_asset: Asset,
    flexible_asset: Asset,
) -> None:
    """Verify counting assets that satisfy an incident's capability."""
    assert (
        ai_planner.count_compatible_assets(
            medical_incident,
            [medical_asset, logistics_asset, flexible_asset],
        )
        == 2
    )


def test_compute_assignment_rank_prefers_less_flexible_assets(
    medical_asset: Asset,
    flexible_asset: Asset,
) -> None:
    """Verify ranking favors specialist assets before flexible ones."""
    occupancy = {"A1": {0, 1}, "A3": set()}

    specialist_rank = ai_planner.compute_assignment_rank(medical_asset, 2, occupancy)
    flexible_rank = ai_planner.compute_assignment_rank(flexible_asset, 1, occupancy)

    assert specialist_rank == (1, 2, 2)
    assert flexible_rank == (2, 1, 0)
    assert specialist_rank < flexible_rank


def test_find_best_assignment_uses_rank_not_asset_order(
    medical_incident: Incident,
    medical_asset: Asset,
    flexible_asset: Asset,
) -> None:
    """Verify best-assignment selection uses rank instead of input order."""
    occupancy = {"A1": {1}, "A3": set()}

    assignment = ai_planner.find_best_feasible_assignment(
        medical_incident,
        [flexible_asset, medical_asset],
        occupancy,
    )

    assert assignment == ("A1", 2)


def test_find_best_assignment_returns_none_when_infeasible(
    medical_incident: Incident,
    logistics_asset: Asset,
) -> None:
    """Verify that assignment search returns ``None`` when no option works."""
    assert (
        ai_planner.find_best_feasible_assignment(
            medical_incident,
            [logistics_asset],
            {"A2": set()},
        )
        is None
    )


def test_plan_orders_by_score_and_skips_infeasible_incidents(
    medical_asset: Asset,
    flexible_asset: Asset,
) -> None:
    """Verify score ordering and omission of infeasible incidents."""
    high_density = Incident("high", 10, 1, 0, 1, 1.0, "medical")
    lower_density = Incident("lower", 12, 2, 0, 2, 0.5, "medical")
    impossible = Incident("impossible", 100, 1, 0, 1, 1.0, "unknown")
    episode = Episode(
        [lower_density, high_density, impossible],
        [flexible_asset, medical_asset],
        10,
    )

    plan = ai_planner.create_ai_plan(episode)

    assert plan.plan_name == "ai"
    assert [assignment.incident_id for assignment in plan.assignments] == [
        "high",
        "lower",
    ]
    assert [assignment.asset_id for assignment in plan.assignments] == ["A1", "A3"]
