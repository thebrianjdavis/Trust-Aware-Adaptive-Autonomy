"""Beta-Bernoulli trust model for estimating AI helpfulness over time."""

from dataclasses import dataclass


@dataclass
class BetaTrustModel:
    #: Alpha parameter of the Beta posterior.
    """Stores the trust posterior parameters and exposes derived quantities."""
    alpha: float = 2.0

    #: Beta parameter of the Beta posterior.
    beta: float = 2.0

    def update(self, comparison_result: int) -> None:
        """Update the trust posterior from one comparison outcome.

        Args:
            comparison_result: 1 if AI won, -1 if baseline won, 0 if tie.
        """
        if comparison_result > 0:
            self.alpha += 1.0
        elif comparison_result < 0:
            self.beta += 1.0

    def get_trust_score(self) -> float:
        """Return the posterior mean trust estimate.

        Returns:
            Posterior mean of the Beta distribution.
        """
        trust_score = self.alpha / (self.alpha + self.beta)
        return trust_score

    def get_variance(self) -> float:
        """Return the posterior variance.

        Returns:
            Variance of the Beta distribution.
        """
        numerator = self.alpha * self.beta
        denominator = (self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1.0)
        variance = numerator / denominator
        return variance

    def compare_utilities(self, ai_utility: int, baseline_utility: int) -> int:
        """Compare AI and baseline utility.

        Args:
            ai_utility: Realized AI utility.
            baseline_utility: Realized baseline utility.

        Returns:
            1 if AI utility exceeds baseline, -1 if baseline exceeds AI, otherwise 0.
        """
        comparison_result = 0

        if ai_utility > baseline_utility:
            comparison_result = 1
        elif ai_utility < baseline_utility:
            comparison_result = -1

        return comparison_result
    