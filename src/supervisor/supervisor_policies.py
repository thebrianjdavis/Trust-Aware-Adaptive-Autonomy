"""Simulated supervisor policies for HMT experiments."""

import random
from dataclasses import dataclass


def clamp_probability(probability_value: float) -> float:
    """Clamp a probability to the valid interval [0, 1].

    Args:
        probability_value: Probability value to clamp.

    Returns:
        Clamped probability value.
    """
    clamped_probability = max(0.0, min(1.0, probability_value))
    return clamped_probability


def get_strength_modifier(recommendation_strength: str) -> float:
    """Convert recommendation strength to an additive acceptance modifier.

    Args:
        recommendation_strength: Recommendation strength label.

    Returns:
        Acceptance probability modifier.
    """
    strength_modifier = 0.0

    if recommendation_strength == "weak":
        strength_modifier = -0.30
    elif recommendation_strength == "strong":
        strength_modifier = 0.20

    return strength_modifier


@dataclass(frozen=True)
class SupervisorPolicy:
    #: Human-readable policy name.
    """Base class for supervisor policies."""
    policy_name: str

    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        """Decide whether to accept the AI recommendation.

        Args:
            ai_confidence: Confidence score for the AI plan.
            trust_score: Current machine trust estimate.
            recommendation_strength: Recommendation strength label.
            rng: Random number generator.

        Returns:
            True if AI plan is accepted, otherwise False.
        """
        raise NotImplementedError("Subclasses must implement accept_ai_plan().")


@dataclass(frozen=True)
class UndertrustSupervisorPolicy(SupervisorPolicy):
    """Supervisor policy representing undertrust behavior."""
    def __init__(self) -> None:
        """Initialize the undertrust policy name."""
        object.__setattr__(self, "policy_name", "undertrust")

    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        """Decide whether to accept the AI recommendation.

        Args:
            ai_confidence: Confidence score for the AI plan.
            trust_score: Current machine trust estimate.
            recommendation_strength: Recommendation strength label.
            rng: Random number generator.

        Returns:
            True if AI plan is accepted, otherwise False.
        """
        if ai_confidence < 0.75:
            accept_probability = 0.05 + 0.10 * trust_score
        elif ai_confidence < 0.85:
            accept_probability = 0.20 + 0.15 * trust_score
        else:
            accept_probability = 0.40 + 0.20 * trust_score

        accept_probability += get_strength_modifier(recommendation_strength)
        accept_probability = clamp_probability(accept_probability)
        return rng.random() < accept_probability


@dataclass(frozen=True)
class CalibratedSupervisorPolicy(SupervisorPolicy):
    """Supervisor policy representing calibrated behavior."""
    def __init__(self) -> None:
        """Initialize the calibrated policy name."""
        object.__setattr__(self, "policy_name", "calibrated")

    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        """Decide whether to accept the AI recommendation.

        Args:
            ai_confidence: Confidence score for the AI plan.
            trust_score: Current machine trust estimate.
            recommendation_strength: Recommendation strength label.
            rng: Random number generator.

        Returns:
            True if AI plan is accepted, otherwise False.
        """
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


@dataclass(frozen=True)
class OvertrustSupervisorPolicy(SupervisorPolicy):
    """Supervisor policy representing overtrust behavior."""
    def __init__(self) -> None:
        """Initialize the overtrust policy name."""
        object.__setattr__(self, "policy_name", "overtrust")

    def accept_ai_plan(
        self,
        ai_confidence: float,
        trust_score: float,
        recommendation_strength: str,
        rng: random.Random,
    ) -> bool:
        """Decide whether to accept the AI recommendation.

        Args:
            ai_confidence: Confidence score for the AI plan.
            trust_score: Current machine trust estimate.
            recommendation_strength: Recommendation strength label.
            rng: Random number generator.

        Returns:
            True if AI plan is accepted, otherwise False.
        """
        if ai_confidence < 0.70:
            accept_probability = 0.65 + 0.10 * trust_score
        elif ai_confidence < 0.85:
            accept_probability = 0.80 + 0.10 * trust_score
        else:
            accept_probability = 0.92 + 0.05 * trust_score

        accept_probability += get_strength_modifier(recommendation_strength)
        accept_probability = clamp_probability(accept_probability)
        return rng.random() < accept_probability
    