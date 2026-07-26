"""Adaptive autonomy and ablation-mode intervention scoring logic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveAutonomyConfig:
    #: Weight assigned to AI confidence in the intervention score.
    """Stores the adaptive autonomy configuration parameters."""
    confidence_weight: float = 0.50

    #: Weight assigned to trust in the intervention score.
    trust_weight: float = 0.20

    #: Weight assigned to centered supervisor override behavior.
    #: Positive values should increase intervention when override rate is above
    #: target, and decrease intervention when override rate is below target.
    override_weight: float = 0.30

    #: Target override rate representing approximately calibrated behavior.
    target_override_rate: float = 0.50

    #: Pseudo-count for prior accepted decisions.
    #: Used to smooth early override-rate estimates.
    prior_accept_count: float = 2.0

    #: Pseudo-count for prior overridden decisions.
    #: Used to smooth early override-rate estimates.
    prior_override_count: float = 2.0

    #: Threshold for weak recommendation behavior.
    weak_threshold: float = 0.45

    #: Threshold for strong recommendation behavior.
    strong_threshold: float = 0.65


def clamp_score(score_value: float) -> float:
    """Clamp a score to the valid interval [0, 1].

    Args:
        score_value: Score value to clamp.

    Returns:
        Clamped score.
    """
    clamped_score = max(0.0, min(1.0, score_value))
    return clamped_score


def clamp_behavior_signal(signal_value: float) -> float:
    """Clamp a value to the valid interval [-1, 1].

    Args:
        signal_value: Signal value to clamp.

    Returns:
        Clamped signal.
    """
    clamped_signal = max(-1.0, min(1.0, signal_value))
    return clamped_signal


def compute_override_rate(
    accepted_count: int,
    overridden_count: int,
    config: AdaptiveAutonomyConfig,
) -> float:
    """Compute a smoothed supervisor override rate.

    Pseudo-count smoothing prevents the earliest episodes from producing
    extreme 0.0 or 1.0 override rates after only one or two decisions.

    Args:
        accepted_count: Number of times the AI recommendation was accepted.
        overridden_count: Number of times the AI recommendation was overridden.
        config: Adaptive autonomy configuration.

    Returns:
        Smoothed override rate in [0, 1].
    """
    smoothed_accepted_count = accepted_count + config.prior_accept_count
    smoothed_overridden_count = overridden_count + config.prior_override_count
    total_decisions = smoothed_accepted_count + smoothed_overridden_count

    override_rate = smoothed_overridden_count / total_decisions
    override_rate = clamp_score(override_rate)

    return override_rate


def compute_override_behavior_signal(
    override_rate: float,
    config: AdaptiveAutonomyConfig,
) -> float:
    """Compute a centered supervisor behavior signal from override rate.

    A value near 0 means approximately calibrated supervisor behavior.
    Positive values indicate frequent overriding (undertrust-like behavior).
    Negative values indicate infrequent overriding (overtrust-like behavior).

    Args:
        override_rate: Smoothed override rate.
        config: Adaptive autonomy configuration.

    Returns:
        Centered behavior signal in [-1, 1].
    """
    normalization_scale = max(
        config.target_override_rate,
        1.0 - config.target_override_rate,
    )

    behavior_signal = (
        override_rate - config.target_override_rate
    ) / normalization_scale

    behavior_signal = clamp_behavior_signal(behavior_signal)
    return behavior_signal


def compute_intervention_score(
    ai_confidence: float,
    trust_score: float,
    override_rate: float,
    config: AdaptiveAutonomyConfig,
) -> float:
    """Compute an intervention score from confidence, trust, and supervisor behavior.

    High override rates should drive stronger recommendations.
    Low override rates should drive weaker recommendations.

    Args:
        ai_confidence: Confidence score for the AI plan.
        trust_score: Current trust score.
        override_rate: Smoothed supervisor override rate.
        config: Adaptive autonomy configuration.

    Returns:
        Intervention score in [0, 1].
    """
    behavior_signal = compute_override_behavior_signal(
        override_rate=override_rate,
        config=config,
    )

    intervention_score = (
        config.confidence_weight * ai_confidence
        + config.trust_weight * trust_score
        + config.override_weight * behavior_signal
    )

    intervention_score = clamp_score(intervention_score)
    return intervention_score


def normalize_autonomy_mode(autonomy_mode: str) -> str:
    """Normalize autonomy mode aliases.

    Args:
        autonomy_mode: Requested autonomy mode.

    Returns:
        Canonical autonomy mode string.
    """
    normalized_mode = autonomy_mode

    if autonomy_mode == "adaptive_full":
        normalized_mode = "adaptive"

    return normalized_mode


def compute_intervention_score_for_mode(
    ai_confidence: float,
    trust_score: float,
    override_rate: float,
    autonomy_mode: str,
    config: AdaptiveAutonomyConfig,
) -> float:
    """Compute an intervention score for a specific autonomy ablation mode.

    Supported modes:
    - fixed: fixed normal recommendations; score returned for logging only.
    - confidence_trust: confidence + trust, no behavior signal.
    - behavior_only: centered override behavior signal only.
    - adaptive: confidence + trust + centered override behavior signal.

    Args:
        ai_confidence: Confidence score for the AI plan.
        trust_score: Current trust score.
        override_rate: Smoothed supervisor override rate.
        autonomy_mode: Autonomy mode or ablation mode.
        config: Adaptive autonomy configuration.

    Returns:
        Intervention score in [0, 1].
    """
    normalized_mode = normalize_autonomy_mode(autonomy_mode)

    if normalized_mode == "fixed":
        intervention_score = ai_confidence

    elif normalized_mode == "confidence_trust":
        intervention_score = (
            config.confidence_weight * ai_confidence
            + config.trust_weight * trust_score
        )

    elif normalized_mode == "behavior_only":
        behavior_signal = compute_override_behavior_signal(
            override_rate=override_rate,
            config=config,
        )

        intervention_score = (
            config.target_override_rate
            + config.override_weight * behavior_signal
        )

    elif normalized_mode == "adaptive":
        intervention_score = compute_intervention_score(
            ai_confidence=ai_confidence,
            trust_score=trust_score,
            override_rate=override_rate,
            config=config,
        )

    else:
        raise ValueError(f"Unsupported autonomy mode: {autonomy_mode}")

    intervention_score = clamp_score(intervention_score)
    return intervention_score


def get_recommendation_strength(
    intervention_score: float,
    config: AdaptiveAutonomyConfig,
) -> str:
    """Map an intervention score to a recommendation strength label.

    Args:
        intervention_score: Combined intervention score.
        config: Adaptive autonomy configuration.

    Returns:
        Recommendation strength: "weak", "normal", or "strong".
    """
    if intervention_score < config.weak_threshold:
        recommendation_strength = "weak"
    elif intervention_score < config.strong_threshold:
        recommendation_strength = "normal"
    else:
        recommendation_strength = "strong"

    return recommendation_strength


def get_fixed_recommendation_strength() -> str:
    """Return a fixed recommendation strength for the non-adaptive condition.

    Returns:
        Fixed recommendation strength label.
    """
    recommendation_strength = "normal"
    return recommendation_strength
