"""Tests for the Beta-Bernoulli trust model."""

import pytest

from src.trust.beta_trust_model import BetaTrustModel


@pytest.mark.parametrize(
    ("comparison_result", "expected_alpha", "expected_beta"),
    [
        (1, 3.0, 2.0),
        (4, 3.0, 2.0),
        (-1, 2.0, 3.0),
        (-4, 2.0, 3.0),
        (0, 2.0, 2.0),
    ],
)
def test_update_applies_win_loss_or_tie(
    comparison_result: int,
    expected_alpha: float,
    expected_beta: float,
) -> None:
    """Verify trust updates treat positive, negative, and tied comparisons correctly."""
    model = BetaTrustModel()

    model.update(comparison_result)

    assert model.alpha == expected_alpha
    assert model.beta == expected_beta


def test_trust_score_and_variance_match_beta_distribution() -> None:
    """Verify trust mean and variance follow the Beta distribution formulas."""
    model = BetaTrustModel(alpha=3.0, beta=2.0)

    assert model.get_trust_score() == pytest.approx(0.6)
    assert model.get_variance() == pytest.approx(0.04)


@pytest.mark.parametrize(
    ("ai_utility", "baseline_utility", "expected"),
    [(11, 10, 1), (9, 10, -1), (10, 10, 0)],
)
def test_compare_utilities(
    ai_utility: int,
    baseline_utility: int,
    expected: int,
) -> None:
    """Verify utility comparisons distinguish AI wins, losses, and ties."""
    assert BetaTrustModel().compare_utilities(ai_utility, baseline_utility) == expected
