"""Tests for deterministic episode generation."""

import random
from unittest.mock import Mock

import pytest

from config import SimulationConfig
from data.calibration.fema_distribution import FemaCalibrationData
from src.environment import generator


@pytest.fixture
def calibration_data() -> FemaCalibrationData:
    """Provide a compact calibration distribution for generator tests."""
    return FemaCalibrationData(
        incident_types=["Fire", "Flood"],
        incident_type_weights=[0.5, 0.5],
        duration_slots=[1, 2, 3],
    )


@pytest.mark.parametrize(
    ("num_assets", "expected_ids"),
    [(0, []), (2, ["A1", "A2"]), (4, ["A1", "A2", "A3"])],
)
def test_generate_assets_respects_available_predefined_assets(
    num_assets: int,
    expected_ids: list[str],
) -> None:
    """Verify that asset generation honors the predefined asset limit."""
    config = SimulationConfig(num_assets=num_assets, num_time_slots=4)

    assets = generator.generate_assets(config)

    assert [asset.asset_id for asset in assets] == expected_ids
    assert all(asset.available_time_slots == {0, 1, 2, 3} for asset in assets)


def test_generate_incidents_maps_types_and_clamps_durations(
    monkeypatch: pytest.MonkeyPatch,
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify incident type mapping and configured duration clamping."""
    config = SimulationConfig(
        num_incidents=2,
        num_time_slots=10,
        min_priority=5,
        max_priority=20,
        min_duration=1,
        max_duration=3,
    )
    monkeypatch.setattr(
        generator,
        "sample_incident_type",
        Mock(side_effect=["Fire", "Flood"]),
    )
    monkeypatch.setattr(
        generator,
        "sample_duration_slots",
        Mock(side_effect=[0, 99]),
    )
    rng = Mock(spec=random.Random)
    rng.randint.side_effect = [0, 1, 5, 7, 10, 20]
    rng.betavariate.side_effect = [0.25, 0.75]

    incidents = generator.generate_incidents(config, rng, calibration_data)

    assert [incident.incident_id for incident in incidents] == ["I1", "I2"]
    assert [incident.duration for incident in incidents] == [1, 3]
    assert [incident.required_capability for incident in incidents] == [
        "medical",
        "logistics",
    ]
    assert incidents[0].earliest_start == 0
    assert incidents[0].latest_finish == 1
    assert incidents[0].priority == 5
    assert incidents[0].success_probability == 0.25
    assert incidents[1].earliest_start == 7
    assert incidents[1].latest_finish == 10


def test_generate_episode_is_reproducible_with_default_seed(
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify repeatable episode generation from the configured seed."""
    config = SimulationConfig(num_incidents=3, seed=123)

    first = generator.generate_episode(config, calibration_data)
    second = generator.generate_episode(config, calibration_data)

    assert first == second


def test_generate_episode_uses_supplied_rng(
    monkeypatch: pytest.MonkeyPatch,
    calibration_data: FemaCalibrationData,
) -> None:
    """Verify that a caller-provided random generator is reused."""
    config = SimulationConfig()
    supplied_rng = random.Random(999)
    generated_assets = []
    generated_incidents = []
    assets_mock = Mock(return_value=generated_assets)
    incidents_mock = Mock(return_value=generated_incidents)
    monkeypatch.setattr(generator, "generate_assets", assets_mock)
    monkeypatch.setattr(generator, "generate_incidents", incidents_mock)

    episode = generator.generate_episode(config, calibration_data, supplied_rng)

    assets_mock.assert_called_once_with(config)
    incidents_mock.assert_called_once_with(config, supplied_rng, calibration_data)
    assert episode.assets is generated_assets
    assert episode.incidents is generated_incidents
    assert episode.num_time_slots == config.num_time_slots
