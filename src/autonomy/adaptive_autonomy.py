## @file adaptive_autonomy.py
## @brief Adaptive autonomy and ablation-mode intervention scoring logic.

from dataclasses import dataclass


## @brief Stores the adaptive autonomy configuration parameters.
@dataclass(frozen=True)
class AdaptiveAutonomyConfig:
    ## @brief Weight assigned to AI confidence in the intervention score.
    confidence_weight: float = 0.50

    ## @brief Weight assigned to trust in the intervention score.
    trust_weight: float = 0.20

    ## @brief Weight assigned to centered supervisor override behavior.
    ## @details
    ## Positive values should increase intervention when override rate is above
    ## target, and decrease intervention when override rate is below target.
    override_weight: float = 0.30

    ## @brief Target override rate representing approximately calibrated behavior.
    target_override_rate: float = 0.50

    ## @brief Pseudo-count for prior accepted decisions.
    ## @details
    ## Used to smooth early override-rate estimates.
    prior_accept_count: float = 2.0

    ## @brief Pseudo-count for prior overridden decisions.
    ## @details
    ## Used to smooth early override-rate estimates.
    prior_override_count: float = 2.0

    ## @brief Threshold for weak recommendation behavior.
    weak_threshold: float = 0.45

    ## @brief Threshold for strong recommendation behavior.
    strong_threshold: float = 0.65


## @brief Clamp a score to the valid interval [0, 1].
## @param score_value Score value to clamp.
## @return Clamped score.
def clamp_score(score_value: float) -> float:
    clamped_score = max(0.0, min(1.0, score_value))
    return clamped_score


## @brief Clamp a value to the valid interval [-1, 1].
## @param signal_value Signal value to clamp.
## @return Clamped signal.
def clamp_behavior_signal(signal_value: float) -> float:
    clamped_signal = max(-1.0, min(1.0, signal_value))
    return clamped_signal


## @brief Compute a smoothed supervisor override rate.
## @details
## Pseudo-count smoothing prevents the earliest episodes from producing
## extreme 0.0 or 1.0 override rates after only one or two decisions.
## @param accepted_count Number of times the AI recommendation was accepted.
## @param overridden_count Number of times the AI recommendation was overridden.
## @param config Adaptive autonomy configuration.
## @return Smoothed override rate in [0, 1].
def compute_override_rate(
    accepted_count: int,
    overridden_count: int,
    config: AdaptiveAutonomyConfig,
) -> float:
    smoothed_accepted_count = accepted_count + config.prior_accept_count
    smoothed_overridden_count = overridden_count + config.prior_override_count
    total_decisions = smoothed_accepted_count + smoothed_overridden_count

    override_rate = smoothed_overridden_count / total_decisions
    override_rate = clamp_score(override_rate)

    return override_rate


## @brief Compute a centered supervisor behavior signal from override rate.
## @details
## A value near 0 means approximately calibrated supervisor behavior.
## Positive values indicate frequent overriding (undertrust-like behavior).
## Negative values indicate infrequent overriding (overtrust-like behavior).
## @param override_rate Smoothed override rate.
## @param config Adaptive autonomy configuration.
## @return Centered behavior signal in [-1, 1].
def compute_override_behavior_signal(
    override_rate: float,
    config: AdaptiveAutonomyConfig,
) -> float:
    normalization_scale = max(
        config.target_override_rate,
        1.0 - config.target_override_rate,
    )

    behavior_signal = (
        override_rate - config.target_override_rate
    ) / normalization_scale

    behavior_signal = clamp_behavior_signal(behavior_signal)
    return behavior_signal


## @brief Compute an intervention score from confidence, trust, and supervisor behavior.
## @details
## High override rates should drive stronger recommendations.
## Low override rates should drive weaker recommendations.
## @param ai_confidence Confidence score for the AI plan.
## @param trust_score Current trust score.
## @param override_rate Smoothed supervisor override rate.
## @param config Adaptive autonomy configuration.
## @return Intervention score in [0, 1].
def compute_intervention_score(
    ai_confidence: float,
    trust_score: float,
    override_rate: float,
    config: AdaptiveAutonomyConfig,
) -> float:
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


## @brief Normalize autonomy mode aliases.
## @param autonomy_mode Requested autonomy mode.
## @return Canonical autonomy mode string.
def normalize_autonomy_mode(autonomy_mode: str) -> str:
    normalized_mode = autonomy_mode

    if autonomy_mode == "adaptive_full":
        normalized_mode = "adaptive"

    return normalized_mode


## @brief Compute an intervention score for a specific autonomy ablation mode.
## @details
## Supported modes:
## - fixed: fixed normal recommendations; score returned for logging only.
## - confidence_trust: confidence + trust, no behavior signal.
## - behavior_only: centered override behavior signal only.
## - adaptive: confidence + trust + centered override behavior signal.
## @param ai_confidence Confidence score for the AI plan.
## @param trust_score Current trust score.
## @param override_rate Smoothed supervisor override rate.
## @param autonomy_mode Autonomy mode or ablation mode.
## @param config Adaptive autonomy configuration.
## @return Intervention score in [0, 1].
def compute_intervention_score_for_mode(
    ai_confidence: float,
    trust_score: float,
    override_rate: float,
    autonomy_mode: str,
    config: AdaptiveAutonomyConfig,
) -> float:
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


## @brief Map an intervention score to a recommendation strength label.
## @param intervention_score Combined intervention score.
## @param config Adaptive autonomy configuration.
## @return Recommendation strength: "weak", "normal", or "strong".
def get_recommendation_strength(
    intervention_score: float,
    config: AdaptiveAutonomyConfig,
) -> str:
    if intervention_score < config.weak_threshold:
        recommendation_strength = "weak"
    elif intervention_score < config.strong_threshold:
        recommendation_strength = "normal"
    else:
        recommendation_strength = "strong"

    return recommendation_strength


## @brief Return a fixed recommendation strength for the non-adaptive condition.
## @return Fixed recommendation strength label.
def get_fixed_recommendation_strength() -> str:
    recommendation_strength = "normal"
    return recommendation_strength
