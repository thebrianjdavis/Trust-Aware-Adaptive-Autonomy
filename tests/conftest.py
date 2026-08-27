"""Shared fixtures for unit tests."""

import pytest

from src.environment.models import Asset, Episode, Incident, PlanAssignment


@pytest.fixture
def medical_incident() -> Incident:
    """Return a medical incident with a multi-slot scheduling window."""
    return Incident(
        incident_id="I1",
        priority=12,
        duration=2,
        earliest_start=1,
        latest_finish=6,
        success_probability=0.7,
        required_capability="medical",
    )


@pytest.fixture
def medical_asset() -> Asset:
    """Return an always-available specialist medical asset."""
    return Asset(
        asset_id="A1",
        capabilities={"medical"},
        available_time_slots=set(range(10)),
    )


@pytest.fixture
def logistics_asset() -> Asset:
    """Return an always-available specialist logistics asset."""
    return Asset(
        asset_id="A2",
        capabilities={"logistics"},
        available_time_slots=set(range(10)),
    )


@pytest.fixture
def flexible_asset() -> Asset:
    """Return an always-available multi-capability asset."""
    return Asset(
        asset_id="A3",
        capabilities={"medical", "logistics"},
        available_time_slots=set(range(10)),
    )


@pytest.fixture
def medical_assignment() -> PlanAssignment:
    """Return an early assignment for the standard medical incident."""
    return PlanAssignment(
        incident_id="I1",
        asset_id="A1",
        start_time=1,
        end_time=3,
    )


@pytest.fixture
def sample_episode(
    medical_incident: Incident,
    medical_asset: Asset,
    logistics_asset: Asset,
    flexible_asset: Asset,
) -> Episode:
    """Return a small episode suitable for lookup and planning tests."""
    logistics_incident = Incident(
        incident_id="I2",
        priority=8,
        duration=1,
        earliest_start=0,
        latest_finish=4,
        success_probability=0.5,
        required_capability="logistics",
    )
    return Episode(
        incidents=[medical_incident, logistics_incident],
        assets=[medical_asset, logistics_asset, flexible_asset],
        num_time_slots=10,
    )
