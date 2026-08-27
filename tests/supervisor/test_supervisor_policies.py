"""Tests for simulated supervisor acceptance policies."""

from unittest.mock import Mock

import pytest

from src.supervisor.supervisor_policies import (
    CalibratedSupervisorPolicy,
    OvertrustSupervisorPolicy,
    SupervisorPolicy,
    UndertrustSupervisorPolicy,
    clamp_probability,
    get_strength_modifier,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-0.5, 0.0), (0.5, 0.5), (1.5, 1.0)],
)
def test_clamp_probability(value: float, expected: float) -> None:
    """Verify that supervisor probabilities stay within the unit interval."""
    assert clamp_probability(value) == expected


@pytest.mark.parametrize(
    ("strength", "expected"),
    [("weak", -0.3), ("normal", 0.0), ("strong", 0.2), ("unknown", 0.0)],
)
def test_strength_modifier(strength: str, expected: float) -> None:
    """Verify probability adjustments for every recommendation strength."""
    assert get_strength_modifier(strength) == expected


def test_base_policy_requires_implementation() -> None:
    """Verify that the base supervisor policy cannot make decisions directly."""
    policy = SupervisorPolicy(policy_name="base")

    with pytest.raises(NotImplementedError, match="Subclasses must implement"):
        policy.accept_ai_plan(0.5, 0.5, "normal", Mock())


@pytest.mark.parametrize(
    ("policy", "expected_name"),
    [
        (UndertrustSupervisorPolicy(), "undertrust"),
        (CalibratedSupervisorPolicy(), "calibrated"),
        (OvertrustSupervisorPolicy(), "overtrust"),
    ],
)
def test_policy_names(policy: SupervisorPolicy, expected_name: str) -> None:
    """Verify each concrete policy exposes its canonical name."""
    assert policy.policy_name == expected_name


@pytest.mark.parametrize(
    ("confidence", "expected_probability"),
    [(0.70, 0.10), (0.80, 0.275), (0.90, 0.50)],
)
def test_undertrust_probability_bands(
    confidence: float,
    expected_probability: float,
) -> None:
    """Verify undertrust acceptance probabilities across confidence bands."""
    rng = Mock()
    rng.random.return_value = expected_probability + 0.001

    accepted = UndertrustSupervisorPolicy().accept_ai_plan(
        confidence,
        0.5,
        "normal",
        rng,
    )

    assert accepted is False
    rng.random.assert_called_once_with()


@pytest.mark.parametrize(
    ("confidence", "expected_probability"),
    [(0.60, 0.15), (0.75, 0.35), (0.85, 0.55), (0.95, 0.775)],
)
def test_calibrated_probability_bands(
    confidence: float,
    expected_probability: float,
) -> None:
    """Verify calibrated acceptance probabilities across confidence bands."""
    rng = Mock()
    rng.random.return_value = expected_probability - 0.001

    assert CalibratedSupervisorPolicy().accept_ai_plan(
        confidence,
        0.5,
        "normal",
        rng,
    )


@pytest.mark.parametrize(
    ("confidence", "expected_probability"),
    [(0.60, 0.70), (0.75, 0.85), (0.90, 0.945)],
)
def test_overtrust_probability_bands(
    confidence: float,
    expected_probability: float,
) -> None:
    """Verify overtrust acceptance probabilities across confidence bands."""
    rng = Mock()
    rng.random.return_value = expected_probability + 0.001

    assert not OvertrustSupervisorPolicy().accept_ai_plan(
        confidence,
        0.5,
        "normal",
        rng,
    )


def test_strength_modifiers_are_applied_and_clamped() -> None:
    """Verify recommendation strength changes and clamps acceptance probability."""
    reject_rng = Mock()
    reject_rng.random.return_value = 0.0
    assert not UndertrustSupervisorPolicy().accept_ai_plan(
        0.0,
        0.0,
        "weak",
        reject_rng,
    )

    accept_rng = Mock()
    accept_rng.random.return_value = 0.999
    assert OvertrustSupervisorPolicy().accept_ai_plan(
        1.0,
        1.0,
        "strong",
        accept_rng,
    )
