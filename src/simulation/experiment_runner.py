## @file experiment_runner.py
## @brief Run repeated simulation episodes and track trust over time.

import random
from dataclasses import dataclass
from pathlib import Path
from typing import List

from data.calibration.fema_distribution import (
    FemaCalibrationData,
    load_fema_calibration_data,
)

from src.autonomy.adaptive_autonomy import (
    AdaptiveAutonomyConfig,
    compute_intervention_score,
    compute_override_rate,
    get_fixed_recommendation_strength,
    get_recommendation_strength,
)
from src.planners.ai_planner import create_ai_plan
from src.planners.baseline_planner import create_baseline_plan
from src.trust.beta_trust_model import BetaTrustModel
from src.autonomy.confidence_estimator import estimate_plan_confidence
from config import SimulationConfig
from src.environment.generator import generate_episode
from src.simulation.outcome_simulator import evaluate_plan
from src.supervisor.supervisor_policies import (
    CalibratedSupervisorPolicy,
    OvertrustSupervisorPolicy,
    UndertrustSupervisorPolicy,
)


## @brief Stores the summary output of one full experiment run.
@dataclass(frozen=True)
class ExperimentRunSummary:
    ## @brief Supervisor policy mode.
    supervisor_mode: str

    ## @brief Autonomy mode.
    autonomy_mode: str

    ## @brief Number of episodes run.
    num_episodes: int

    ## @brief Number of AI wins.
    ai_wins: int

    ## @brief Number of baseline wins.
    baseline_wins: int

    ## @brief Number of ties.
    ties: int

    ## @brief Number of times the AI plan was accepted.
    ai_accepted: int

    ## @brief Number of times the AI plan was overridden.
    ai_overridden: int

    ## @brief Number of weak recommendations.
    weak_recommendations: int

    ## @brief Number of normal recommendations.
    normal_recommendations: int

    ## @brief Number of strong recommendations.
    strong_recommendations: int

    ## @brief Mean executed utility.
    mean_executed_utility: float

    ## @brief Mean AI confidence.
    mean_ai_confidence: float

    ## @brief Mean override rate.
    mean_override_rate: float

    ## @brief Mean intervention score.
    mean_intervention_score: float

    ## @brief Final trust score.
    final_trust: float

    ## @brief Final trust variance.
    trust_variance: float

    ## @brief Trust history over episodes.
    trust_history: List[float]


## @brief Run a sequence of episodes and optionally print trust evolution.
## @param config Simulation configuration values.
## @param num_episodes Number of episodes to run.
## @param supervisor_mode Supervisor policy mode: "undertrust", "calibrated", or "overtrust".
## @param autonomy_mode Autonomy mode: "fixed" or "adaptive".
## @param calibration_data Optional preloaded FEMA calibration data.
## @param verbose If True, print per-episode output and final summary.
## @return Experiment summary object.
def run_trust_experiment(
    config: SimulationConfig,
    num_episodes: int,
    supervisor_mode: str = "calibrated",
    autonomy_mode: str = "fixed",
    calibration_data: FemaCalibrationData | None = None,
    verbose: bool = True,
) -> ExperimentRunSummary:
    run_rng = random.Random(config.seed)
    trust_model = BetaTrustModel()
    autonomy_config = AdaptiveAutonomyConfig()

    trust_history: List[float] = []
    executed_utility_history: List[int] = []
    ai_confidence_history: List[float] = []
    intervention_score_history: List[float] = []
    override_rate_history: List[float] = []

    if supervisor_mode == "undertrust":
        supervisor_policy = UndertrustSupervisorPolicy()
    elif supervisor_mode == "overtrust":
        supervisor_policy = OvertrustSupervisorPolicy()
    else:
        supervisor_policy = CalibratedSupervisorPolicy()

    ai_win_count = 0
    baseline_win_count = 0
    tie_count = 0

    ai_accepted_count = 0
    ai_overridden_count = 0

    weak_recommendation_count = 0
    normal_recommendation_count = 0
    strong_recommendation_count = 0

    current_calibration_data = calibration_data
    if current_calibration_data is None:
        csv_path = Path("data/raw/us_disaster_declarations.csv")
        current_calibration_data = load_fema_calibration_data(csv_path)

    for episode_index in range(1, num_episodes + 1):
        episode = generate_episode(
            config=config,
            calibration_data=current_calibration_data,
            rng=run_rng,
        )

        baseline_plan = create_baseline_plan(episode)
        ai_plan = create_ai_plan(episode)

        baseline_evaluation = evaluate_plan(
            episode=episode,
            plan=baseline_plan,
            seed=config.seed + 2000 + episode_index,
        )
        ai_evaluation = evaluate_plan(
            episode=episode,
            plan=ai_plan,
            seed=config.seed + 3000 + episode_index,
        )

        comparison_result = trust_model.compare_utilities(
            ai_utility=ai_evaluation.total_utility,
            baseline_utility=baseline_evaluation.total_utility,
        )
        trust_model.update(comparison_result)

        trust_score = trust_model.get_trust_score()
        trust_history.append(trust_score)

        ai_confidence = estimate_plan_confidence(
            episode=episode,
            plan=ai_plan,
        )
        ai_confidence_history.append(ai_confidence)

        current_override_rate = compute_override_rate(
            accepted_count=ai_accepted_count,
            overridden_count=ai_overridden_count,
            config=autonomy_config,
        )
        override_rate_history.append(current_override_rate)

        if autonomy_mode == "adaptive":
            intervention_score = compute_intervention_score(
                ai_confidence=ai_confidence,
                trust_score=trust_score,
                override_rate=current_override_rate,
                config=autonomy_config,
            )
            recommendation_strength = get_recommendation_strength(
                intervention_score=intervention_score,
                config=autonomy_config,
            )
        else:
            intervention_score = ai_confidence
            recommendation_strength = get_fixed_recommendation_strength()

        intervention_score_history.append(intervention_score)

        if recommendation_strength == "weak":
            weak_recommendation_count += 1
        elif recommendation_strength == "strong":
            strong_recommendation_count += 1
        else:
            normal_recommendation_count += 1

        ai_accepted = supervisor_policy.accept_ai_plan(
            ai_confidence=ai_confidence,
            trust_score=trust_score,
            recommendation_strength=recommendation_strength,
            rng=run_rng,
        )

        if ai_accepted:
            executed_plan_name = "ai"
            executed_utility = ai_evaluation.total_utility
            ai_accepted_count += 1
        else:
            executed_plan_name = "baseline"
            executed_utility = baseline_evaluation.total_utility
            ai_overridden_count += 1

        executed_utility_history.append(executed_utility)

        if comparison_result > 0:
            ai_win_count += 1
            comparison_label = "AI_WIN"
        elif comparison_result < 0:
            baseline_win_count += 1
            comparison_label = "BASELINE_WIN"
        else:
            tie_count += 1
            comparison_label = "TIE"

        if verbose:
            print(
                f"Episode {episode_index}: "
                f"baseline={baseline_evaluation.total_utility}, "
                f"ai={ai_evaluation.total_utility}, "
                f"comparison={comparison_label}, "
                f"trust={trust_score:.3f}, "
                f"confidence={ai_confidence:.3f}, "
                f"override_rate={current_override_rate:.3f}, "
                f"intervention={intervention_score:.3f}, "
                f"strength={recommendation_strength}, "
                f"supervisor={supervisor_policy.policy_name}, "
                f"autonomy={autonomy_mode}, "
                f"executed={executed_plan_name}, "
                f"executed_utility={executed_utility}"
            )

    mean_executed_utility = (
        sum(executed_utility_history) / len(executed_utility_history)
        if executed_utility_history
        else 0.0
    )
    mean_ai_confidence = (
        sum(ai_confidence_history) / len(ai_confidence_history)
        if ai_confidence_history
        else 0.0
    )
    mean_intervention_score = (
        sum(intervention_score_history) / len(intervention_score_history)
        if intervention_score_history
        else 0.0
    )
    mean_override_rate = (
        sum(override_rate_history) / len(override_rate_history)
        if override_rate_history
        else 0.0
    )

    summary = ExperimentRunSummary(
        supervisor_mode=supervisor_policy.policy_name,
        autonomy_mode=autonomy_mode,
        num_episodes=num_episodes,
        ai_wins=ai_win_count,
        baseline_wins=baseline_win_count,
        ties=tie_count,
        ai_accepted=ai_accepted_count,
        ai_overridden=ai_overridden_count,
        weak_recommendations=weak_recommendation_count,
        normal_recommendations=normal_recommendation_count,
        strong_recommendations=strong_recommendation_count,
        mean_executed_utility=mean_executed_utility,
        mean_ai_confidence=mean_ai_confidence,
        mean_override_rate=mean_override_rate,
        mean_intervention_score=mean_intervention_score,
        final_trust=trust_model.get_trust_score(),
        trust_variance=trust_model.get_variance(),
        trust_history=[round(value, 3) for value in trust_history],
    )

    if verbose:
        print("\n=== SUMMARY ===")
        print(f"Supervisor mode: {summary.supervisor_mode}")
        print(f"Autonomy mode: {summary.autonomy_mode}")
        print(f"AI wins: {summary.ai_wins}")
        print(f"Baseline wins: {summary.baseline_wins}")
        print(f"Ties: {summary.ties}")
        print(f"AI accepted: {summary.ai_accepted}")
        print(f"AI overridden: {summary.ai_overridden}")
        print(f"Weak recommendations: {summary.weak_recommendations}")
        print(f"Normal recommendations: {summary.normal_recommendations}")
        print(f"Strong recommendations: {summary.strong_recommendations}")
        print(f"Mean executed utility: {summary.mean_executed_utility:.3f}")
        print(f"Mean AI confidence: {summary.mean_ai_confidence:.3f}")
        print(f"Mean override rate: {summary.mean_override_rate:.3f}")
        print(f"Mean intervention score: {summary.mean_intervention_score:.3f}")
        print(f"Final trust: {summary.final_trust:.3f}")
        print(f"Trust variance: {summary.trust_variance:.5f}")
        print(f"Trust history: {summary.trust_history}")

    return summary
