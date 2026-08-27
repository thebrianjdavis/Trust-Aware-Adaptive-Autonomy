"""Tests for the core environment data models."""

from src.environment.models import Plan, PlanAssignment


def test_plan_adds_and_finds_assignment() -> None:
    assignment = PlanAssignment("I1", "A1", 0, 2)
    plan = Plan(plan_name="test")

    plan.add_assignment(assignment)

    assert plan.assignments == [assignment]
    assert plan.get_assignment_for_incident("I1") is assignment


def test_plan_returns_first_matching_assignment() -> None:
    first = PlanAssignment("I1", "A1", 0, 1)
    second = PlanAssignment("I1", "A2", 1, 2)
    plan = Plan(plan_name="test", assignments=[first, second])

    assert plan.get_assignment_for_incident("I1") is first


def test_plan_returns_none_when_incident_is_unassigned() -> None:
    plan = Plan(
        plan_name="test",
        assignments=[PlanAssignment("other", "A1", 0, 1)],
    )

    assert plan.get_assignment_for_incident("missing") is None
