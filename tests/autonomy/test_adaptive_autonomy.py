"""Tests for adaptive-autonomy intervention scoring."""

import pytest

from src.autonomy.adaptive_autonomy import (
    AdaptiveAutonomyConfig,
    clamp_behavior_signal,
    clamp_score,
    compute_intervention_score,
    compute_intervention_score_for_mode,
    compute_override_behavior_signal,
    compute_override_rate,
    get_fixed_recommendation_strength,
    get_recommendation_strength,
    normalize_autonomy_mode,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-0.1, 0.0), (0.4, 0.4), (1.1, 1.0)],
)
def test_clamp_score(value: float, expected: float) -> None:
    assert clamp_score(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-2.0, -1.0), (-0.4, -0.4), (2.0, 1.0)],
)
def test_clamp_behavior_signal(value: float, expected: float) -> None:
    assert clamp_behavior_signal(value) == expected


def test_override_rate_uses_prior_counts() -> None:
    config = AdaptiveAutonomyConfig()

    assert compute_override_rate(0, 0, config) == 0.5
    assert compute_override_rate(6, 2, config) == pytest.approx(1 / 3)


@pytest.mark.parametrize(
    ("override_rate", "expected"),
    [(0.0, -1.0), (0.5, 0.0), (1.0, 1.0), (2.0, 1.0)],
)
def test_override_behavior_signal_is_centered_and_clamped(
    override_rate: float,
    expected: float,
) -> None:
    config = AdaptiveAutonomyConfig()

    assert compute_override_behavior_signal(override_rate, config) == expected


def test_override_behavior_signal_handles_asymmetric_target() -> None:
    config = AdaptiveAutonomyConfig(target_override_rate=0.25)

    assert compute_override_behavior_signal(1.0, config) == 1.0
    assert compute_override_behavior_signal(0.0, config) == pytest.approx(-1 / 3)


def test_intervention_score_combines_inputs_and_clamps() -> None:
    config = AdaptiveAutonomyConfig()

    assert compute_intervention_score(0.8, 0.5, 0.75, config) == pytest.approx(0.65)

    high_weights = AdaptiveAutonomyConfig(
        confidence_weight=2.0,
        trust_weight=2.0,
        override_weight=2.0,
    )
    assert compute_intervention_score(1.0, 1.0, 1.0, high_weights) == 1.0


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("fixed", 0.8),
        ("confidence_trust", 0.5),
        ("behavior_only", 0.65),
        ("adaptive", 0.65),
        ("adaptive_full", 0.65),
    ],
)
def test_intervention_score_modes(mode: str, expected: float) -> None:
    config = AdaptiveAutonomyConfig()

    score = compute_intervention_score_for_mode(
        ai_confidence=0.8,
        trust_score=0.5,
        override_rate=0.75,
        autonomy_mode=mode,
        config=config,
    )

    assert score == pytest.approx(expected)


def test_intervention_score_mode_clamps_result() -> None:
    config = AdaptiveAutonomyConfig(confidence_weight=5.0, trust_weight=5.0)

    assert (
        compute_intervention_score_for_mode(1.0, 1.0, 0.5, "confidence_trust", config)
        == 1.0
    )


def test_unsupported_intervention_mode_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported autonomy mode: unknown"):
        compute_intervention_score_for_mode(
            0.5,
            0.5,
            0.5,
            "unknown",
            AdaptiveAutonomyConfig(),
        )


def test_normalize_autonomy_mode() -> None:
    assert normalize_autonomy_mode("adaptive_full") == "adaptive"
    assert normalize_autonomy_mode("fixed") == "fixed"


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "weak"),
        (0.449, "weak"),
        (0.45, "normal"),
        (0.649, "normal"),
        (0.65, "strong"),
        (1.0, "strong"),
    ],
)
def test_recommendation_strength_boundaries(score: float, expected: str) -> None:
    assert get_recommendation_strength(score, AdaptiveAutonomyConfig()) == expected


def test_fixed_recommendation_is_normal() -> None:
    assert get_fixed_recommendation_strength() == "normal"
