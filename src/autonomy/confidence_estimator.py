## @file confidence_estimator.py
## @brief Confidence estimation for AI-generated plans.

from typing import Dict

from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment


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


## @brief Clamp a confidence value to the valid interval [0, 1].
## @param confidence_value Confidence value to clamp.
## @return Clamped confidence value.
def clamp_confidence(confidence_value: float) -> float:
    clamped_confidence = max(0.0, min(1.0, confidence_value))
    return clamped_confidence


## @brief Compute an assignment-level confidence contribution.
## @details
## Confidence is based on:
## 1. Base incident success probability
## 2. Small specialization bonus for primary-capability assets
## 3. Small penalty for starting later within the feasible window
## @param incident Assigned incident.
## @param asset Assigned asset.
## @param assignment Assignment details.
## @return Assignment-level confidence contribution.
def compute_assignment_confidence(
    incident: Incident,
    asset: Asset,
    assignment: PlanAssignment,
) -> float:
    confidence_value = incident.success_probability

    if incident.required_capability == "medical" and asset.asset_id == "A1":
        confidence_value += 0.10
    elif incident.required_capability == "logistics" and asset.asset_id == "A2":
        confidence_value += 0.10
    elif asset.asset_id == "A3":
        confidence_value += 0.00

    latest_start = incident.latest_finish - incident.duration
    available_slack = latest_start - incident.earliest_start

    if available_slack > 0:
        start_delay = assignment.start_time - incident.earliest_start
        delay_fraction = start_delay / available_slack
        confidence_value -= 0.10 * delay_fraction

    confidence_value = clamp_confidence(confidence_value)
    return confidence_value


## @brief Estimate plan confidence as the mean assignment confidence.
## @param episode Episode containing incidents and assets.
## @param plan Plan to score.
## @return Confidence score in [0, 1].
def estimate_plan_confidence(episode: Episode, plan: Plan) -> float:
    incident_lookup = build_incident_lookup(episode)
    asset_lookup = build_asset_lookup(episode)

    if not plan.assignments:
        return 0.0

    confidence_sum = 0.0

    for assignment in plan.assignments:
        incident = incident_lookup[assignment.incident_id]
        asset = asset_lookup[assignment.asset_id]
        confidence_sum += compute_assignment_confidence(
            incident=incident,
            asset=asset,
            assignment=assignment,
        )

    plan_confidence = confidence_sum / len(plan.assignments)
    plan_confidence = clamp_confidence(plan_confidence)

    return plan_confidence
