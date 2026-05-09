## @file beta_trust_model.py
## @brief Beta-Bernoulli trust model for estimating AI helpfulness over time.

from dataclasses import dataclass


## @brief Stores the trust posterior parameters and exposes derived quantities.
@dataclass
class BetaTrustModel:
    ## @brief Alpha parameter of the Beta posterior.
    alpha: float = 2.0

    ## @brief Beta parameter of the Beta posterior.
    beta: float = 2.0

    ## @brief Update the trust posterior from one comparison outcome.
    ## @param comparison_result 1 if AI won, -1 if baseline won, 0 if tie.
    def update(self, comparison_result: int) -> None:
        if comparison_result > 0:
            self.alpha += 1.0
        elif comparison_result < 0:
            self.beta += 1.0

    ## @brief Return the posterior mean trust estimate.
    ## @return Posterior mean of the Beta distribution.
    def get_trust_score(self) -> float:
        trust_score = self.alpha / (self.alpha + self.beta)
        return trust_score

    ## @brief Return the posterior variance.
    ## @return Variance of the Beta distribution.
    def get_variance(self) -> float:
        numerator = self.alpha * self.beta
        denominator = (self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1.0)
        variance = numerator / denominator
        return variance

    ## @brief Compare AI and baseline utility.
    ## @param ai_utility Realized AI utility.
    ## @param baseline_utility Realized baseline utility.
    ## @return 1 if AI utility exceeds baseline, -1 if baseline exceeds AI, otherwise 0.
    def compare_utilities(self, ai_utility: int, baseline_utility: int) -> int:
        comparison_result = 0

        if ai_utility > baseline_utility:
            comparison_result = 1
        elif ai_utility < baseline_utility:
            comparison_result = -1

        return comparison_result
    