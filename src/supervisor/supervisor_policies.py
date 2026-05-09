## @file supervisor_policies.py
## @brief Simulated supervisor policies for HMT experiments.

import random
from dataclasses import dataclass


## @brief Clamp a probability to the valid interval [0, 1].
## @param probability_value Probability value to clamp.
## @return Clamped probability value.
def clamp_probability(probability_value: float) -> float:
    clamped_probability = max(0.0, min(1.0, probability_value))
    return clamped_probability


## @brief Convert recommendation strength to an additive acceptance modifier.
## @param recommendation_strength Recommendation strength label.
## @return Acceptance probability modifier.
def get_strength_modifier(recommendation_strength: str) -> float:
    strength_modifier = 0.0

    if recommendation_strength == "weak":
        strength_modifier = -0.30
    elif recommendation_strength == "strong":
        strength_modifier = 0.20

    return strength_modifier


## @brief Base class for supervisor policies.
@dataclass(frozen=True)
class SupervisorPolicy:
    ## @brief Human-readable policy name.
    policy_name: str

    ## @brief Decide whether to accept the AI recommendation.
    ## @param ai_confidence Confidence score for the AI plan.
    ## @param trust_score Current machine trust estimate.
    ## @param recommendation_strength Recommendation strength label.
    ## @param rng Random number generator.
    ## @return True if AI plan is accepted, otherwise False.
    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        raise NotImplementedError("Subclasses must implement accept_ai_plan().")


## @brief Supervisor policy representing undertrust behavior.
@dataclass(frozen=True)
class UndertrustSupervisorPolicy(SupervisorPolicy):
    ## @brief Initialize the undertrust policy name.
    def __init__(self) -> None:
        object.__setattr__(self, "policy_name", "undertrust")

    ## @brief Decide whether to accept the AI recommendation.
    ## @param ai_confidence Confidence score for the AI plan.
    ## @param trust_score Current machine trust estimate.
    ## @param recommendation_strength Recommendation strength label.
    ## @param rng Random number generator.
    ## @return True if AI plan is accepted, otherwise False.
    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        if ai_confidence < 0.75:
            accept_probability = 0.05 + 0.10 * trust_score
        elif ai_confidence < 0.85:
            accept_probability = 0.20 + 0.15 * trust_score
        else:
            accept_probability = 0.40 + 0.20 * trust_score

        accept_probability += get_strength_modifier(recommendation_strength)
        accept_probability = clamp_probability(accept_probability)
        return rng.random() < accept_probability


## @brief Supervisor policy representing calibrated behavior.
@dataclass(frozen=True)
class CalibratedSupervisorPolicy(SupervisorPolicy):
    ## @brief Initialize the calibrated policy name.
    def __init__(self) -> None:
        object.__setattr__(self, "policy_name", "calibrated")

    ## @brief Decide whether to accept the AI recommendation.
    ## @param ai_confidence Confidence score for the AI plan.
    ## @param trust_score Current machine trust estimate.
    ## @param recommendation_strength Recommendation strength label.
    ## @param rng Random number generator.
    ## @return True if AI plan is accepted, otherwise False.
    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        if ai_confidence < 0.70:
            accept_probability = 0.10 + 0.10 * trust_score
        elif ai_confidence < 0.80:
            accept_probability = 0.25 + 0.20 * trust_score
        elif ai_confidence < 0.90:
            accept_probability = 0.45 + 0.20 * trust_score
        else:
            accept_probability = 0.70 + 0.15 * trust_score

        accept_probability += get_strength_modifier(recommendation_strength)
        accept_probability = clamp_probability(accept_probability)
        return rng.random() < accept_probability


## @brief Supervisor policy representing overtrust behavior.
@dataclass(frozen=True)
class OvertrustSupervisorPolicy(SupervisorPolicy):
    ## @brief Initialize the overtrust policy name.
    def __init__(self) -> None:
        object.__setattr__(self, "policy_name", "overtrust")

    ## @brief Decide whether to accept the AI recommendation.
    ## @param ai_confidence Confidence score for the AI plan.
    ## @param trust_score Current machine trust estimate.
    ## @param recommendation_strength Recommendation strength label.
    ## @param rng Random number generator.
    ## @return True if AI plan is accepted, otherwise False.
    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        if ai_confidence < 0.70:
            accept_probability = 0.65 + 0.10 * trust_score
        elif ai_confidence < 0.85:
            accept_probability = 0.80 + 0.10 * trust_score
        else:
            accept_probability = 0.92 + 0.05 * trust_score

        accept_probability += get_strength_modifier(recommendation_strength)
        accept_probability = clamp_probability(accept_probability)
        return rng.random() < accept_probability
    