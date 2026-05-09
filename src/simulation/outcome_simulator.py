## @file outcome_simulator.py
## @brief Outcome simulation for evaluating plans under assignment-sensitive stochastic realizations.

import random
from typing import Dict, List

from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment, PlanEvaluation


## @brief Build a dictionary of incidents keyed by identifier.
## @param episode Episode containing incidents.
## @return Incident lookup dictionary.
def build_incident_lookup(episode: Episode) -> Dict[str, Incident]:
    incident_lookup: Dict[str, Incident] = {}

    for incident in episode.incidents:
        incident_lookup[incident.incident_id] = incident

    return incident_lookup


## @brief Build a dictionary of assets keyed by identifier.
## @param episode Episode containing assets.
## @return Asset lookup dictionary.
def build_asset_lookup(episode: Episode) -> Dict[str, Asset]:
    asset_lookup: Dict[str, Asset] = {}

    for asset in episode.assets:
        asset_lookup[asset.asset_id] = asset

    return asset_lookup


## @brief Clamp a probability to the valid interval [0, 1].
## @param probability Probability value to clamp.
## @return Clamped probability.
def clamp_probability(probability: float) -> float:
    clamped_probability = max(0.0, min(1.0, probability))
    return clamped_probability


## @brief Compute an adjusted success probability for one assignment.
## @details
## The adjusted probability accounts for:
## 1. Base incident success probability
## 2. Asset specialization bonus
## 3. Schedule slack pressure
##
## Specialized assets receive a small bonus for their primary capability.
## Starting later in the time window receives a small penalty.
## @param incident Assigned incident.
## @param asset Assigned asset.
## @param assignment Assignment details.
## @return Adjusted success probability.
def compute_adjusted_success_probability(
    incident: Incident,
    asset: Asset,
    assignment: PlanAssignment,
) -> float:
    adjusted_probability = incident.success_probability

    if incident.required_capability == "medical" and asset.asset_id == "A1":
        adjusted_probability += 0.10
    elif incident.required_capability == "logistics" and asset.asset_id == "A2":
        adjusted_probability += 0.10
    elif asset.asset_id == "A3":
        adjusted_probability += 0.00

    latest_start = incident.latest_finish - incident.duration
    available_slack = latest_start - incident.earliest_start

    if available_slack > 0:
        start_delay = assignment.start_time - incident.earliest_start
        delay_fraction = start_delay / available_slack
        adjusted_probability -= 0.10 * delay_fraction

    adjusted_probability = clamp_probability(adjusted_probability)
    return adjusted_probability


## @brief Evaluate a plan under assignment-sensitive stochastic outcomes.
## @param episode Episode containing incidents and assets.
## @param plan Plan to evaluate.
## @param seed Random seed for reproducible outcome sampling.
## @return Plan evaluation result.
def evaluate_plan(
    episode: Episode,
    plan: Plan,
    seed: int,
) -> PlanEvaluation:
    rng = random.Random(seed)
    incident_lookup = build_incident_lookup(episode)
    asset_lookup = build_asset_lookup(episode)

    total_utility = 0
    successful_incident_ids: List[str] = []
    failed_incident_ids: List[str] = []

    for assignment in plan.assignments:
        incident = incident_lookup[assignment.incident_id]
        asset = asset_lookup[assignment.asset_id]

        adjusted_success_probability = compute_adjusted_success_probability(
            incident=incident,
            asset=asset,
            assignment=assignment,
        )
        incident_succeeded = rng.random() < adjusted_success_probability

        if incident_succeeded:
            total_utility += incident.priority
            successful_incident_ids.append(incident.incident_id)
        else:
            failed_incident_ids.append(incident.incident_id)

    evaluation = PlanEvaluation(
        plan_name=plan.plan_name,
        total_utility=total_utility,
        successful_incident_ids=successful_incident_ids,
        failed_incident_ids=failed_incident_ids,
    )

    return evaluation


## @brief Evaluate two plans under comparable stochastic conditions.
## @details
## Each plan is evaluated with its own assignment-sensitive outcomes, but both
## evaluations remain reproducible through deterministic seeds derived from a
## shared seed.
## @param episode Episode containing incidents and assets.
## @param baseline_plan Baseline plan to evaluate.
## @param ai_plan AI plan to evaluate.
## @param seed Shared seed used to derive per-plan evaluation seeds.
## @return Tuple containing baseline evaluation and AI evaluation.
def evaluate_plans_under_shared_outcomes(
    episode: Episode,
    baseline_plan: Plan,
    ai_plan: Plan,
    seed: int,
) -> tuple[PlanEvaluation, PlanEvaluation]:
    baseline_evaluation = evaluate_plan(
        episode=episode,
        plan=baseline_plan,
        seed=seed + 1,
    )
    ai_evaluation = evaluate_plan(
        episode=episode,
        plan=ai_plan,
        seed=seed + 2,
    )

    return baseline_evaluation, ai_evaluation
