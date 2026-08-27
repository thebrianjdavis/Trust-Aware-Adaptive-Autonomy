"""Tests for the supervisor-only baseline planner."""

from src.environment.models import Asset, Episode, Incident, Plan
from src.planners import baseline_planner


def test_build_asset_occupancy_map(
    medical_asset: Asset,
    logistics_asset: Asset,
) -> None:
    """Verify that every asset receives an independent occupancy set."""
    occupancy = baseline_planner.build_asset_occupancy_map(
        [medical_asset, logistics_asset]
    )

    assert occupancy == {"A1": set(), "A2": set()}
    assert occupancy["A1"] is not occupancy["A2"]


def test_get_candidate_start_times(medical_incident: Incident) -> None:
    """Verify candidate starts span the incident's feasible window."""
    assert baseline_planner.get_candidate_start_times(medical_incident) == [1, 2, 3, 4]


def test_assignment_is_feasible(
    medical_incident: Incident,
    medical_asset: Asset,
) -> None:
    """Verify acceptance of a compatible assignment with open time slots."""
    assert baseline_planner.is_assignment_feasible(
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
    assert not baseline_planner.is_assignment_feasible(
        medical_incident,
        logistics_asset,
        1,
        {"A2": set()},
    )


def test_assignment_rejects_unavailable_slots(medical_incident: Incident) -> None:
    """Verify rejection when the asset is unavailable during the assignment."""
    asset = Asset("A1", {"medical"}, {1})

    assert not baseline_planner.is_assignment_feasible(
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
    assert not baseline_planner.is_assignment_feasible(
        medical_incident,
        medical_asset,
        1,
        {"A1": {2}},
    )


def test_assigns_first_feasible_option(
    medical_incident: Incident,
    medical_asset: Asset,
) -> None:
    """Verify assignment chooses the earliest feasible option."""
    plan = Plan("baseline")
    occupancy = {"A1": {1}}

    assigned = baseline_planner.assign_incident_if_possible(
        medical_incident,
        [medical_asset],
        occupancy,
        plan,
    )

    assert assigned
    assert plan.assignments[0].start_time == 2
    assert plan.assignments[0].end_time == 4
    assert occupancy["A1"] == {1, 2, 3}


def test_leaves_infeasible_incident_unassigned(
    medical_incident: Incident,
    logistics_asset: Asset,
) -> None:
    """Verify an incident remains unassigned when no asset is feasible."""
    plan = Plan("baseline")

    assert not baseline_planner.assign_incident_if_possible(
        medical_incident,
        [logistics_asset],
        {"A2": set()},
        plan,
    )
    assert plan.assignments == []


def test_plan_prioritizes_high_value_incidents(medical_asset: Asset) -> None:
    """Verify that baseline planning schedules higher-value incidents first."""
    low_priority = Incident("low", 5, 2, 0, 2, 1.0, "medical")
    high_priority = Incident("high", 20, 2, 0, 2, 1.0, "medical")
    episode = Episode([low_priority, high_priority], [medical_asset], 10)

    plan = baseline_planner.create_baseline_plan(episode)

    assert plan.plan_name == "baseline"
    assert [assignment.incident_id for assignment in plan.assignments] == ["high"]
