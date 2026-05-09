## @file ai_planner.py
## @brief AI planner for the HMT resource allocation MVP.

from typing import Dict, List, Set

from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment


## @brief Create an empty occupancy map for each asset.
## @param assets Assets available in the episode.
## @return Dictionary mapping asset identifiers to occupied time slots.
def build_asset_occupancy_map(assets: List[Asset]) -> Dict[str, Set[int]]:
    occupancy_map: Dict[str, Set[int]] = {}

    for asset in assets:
        occupancy_map[asset.asset_id] = set()

    return occupancy_map


## @brief Return all feasible start times for an incident.
## @param incident Incident to evaluate.
## @return Candidate start times.
def get_candidate_start_times(incident: Incident) -> List[int]:
    candidate_start_times: List[int] = []
    latest_start = incident.latest_finish - incident.duration

    for start_time in range(incident.earliest_start, latest_start + 1):
        candidate_start_times.append(start_time)

    return candidate_start_times


## @brief Check whether an incident can be assigned to an asset at a start time.
## @param incident Incident to assign.
## @param asset Candidate asset.
## @param start_time Proposed start time.
## @param occupancy_map Current asset occupancy map.
## @return True if assignment is feasible, otherwise False.
def is_assignment_feasible(
    incident: Incident,
    asset: Asset,
    start_time: int,
    occupancy_map: Dict[str, Set[int]],
) -> bool:
    is_feasible = True

    if incident.required_capability not in asset.capabilities:
        is_feasible = False

    if is_feasible:
        requested_slots = set(range(start_time, start_time + incident.duration))

        if not requested_slots.issubset(asset.available_time_slots):
            is_feasible = False

        if requested_slots.intersection(occupancy_map[asset.asset_id]):
            is_feasible = False

    return is_feasible


## @brief Compute an incident score for the AI planner.
## @details
## The score favors high-priority, high-probability, shorter-duration incidents.
## @param incident Incident to score.
## @return Incident score.
def compute_incident_score(incident: Incident) -> float:
    score = (incident.priority * incident.success_probability) / incident.duration
    return score


## @brief Count how many assets can service the incident.
## @param incident Incident to evaluate.
## @param assets Available assets.
## @return Number of compatible assets.
def count_compatible_assets(incident: Incident, assets: List[Asset]) -> int:
    compatible_asset_count = 0

    for asset in assets:
        if incident.required_capability in asset.capabilities:
            compatible_asset_count += 1

    return compatible_asset_count


## @brief Compute a ranking tuple for a candidate asset assignment.
## @details
## Lower tuples are preferred. The planner prefers:
## 1. Less flexible assets first, preserving flexible assets for later.
## 2. Earlier start times.
## 3. Lower current occupancy to spread load when possible.
## @param asset Candidate asset.
## @param start_time Proposed assignment start time.
## @param occupancy_map Current asset occupancy map.
## @return Ranking tuple for lexicographic comparison.
def compute_assignment_rank(
    asset: Asset,
    start_time: int,
    occupancy_map: Dict[str, Set[int]],
) -> tuple[int, int, int]:
    asset_flexibility = len(asset.capabilities)
    current_occupancy = len(occupancy_map[asset.asset_id])
    assignment_rank = (asset_flexibility, start_time, current_occupancy)
    return assignment_rank


## @brief Find the best feasible asset/start-time pair for an incident.
## @param incident Incident to assign.
## @param assets Assets available in the episode.
## @param occupancy_map Current asset occupancy map.
## @return Best asset/start-time tuple if found, otherwise None.
def find_best_feasible_assignment(
    incident: Incident,
    assets: List[Asset],
    occupancy_map: Dict[str, Set[int]],
) -> tuple[str, int] | None:
    best_asset_id: str | None = None
    best_start_time: int | None = None
    best_rank: tuple[int, int, int] | None = None

    for asset in assets:
        candidate_start_times = get_candidate_start_times(incident)

        for start_time in candidate_start_times:
            if is_assignment_feasible(incident, asset, start_time, occupancy_map):
                candidate_rank = compute_assignment_rank(
                    asset=asset,
                    start_time=start_time,
                    occupancy_map=occupancy_map,
                )

                if best_rank is None or candidate_rank < best_rank:
                    best_rank = candidate_rank
                    best_asset_id = asset.asset_id
                    best_start_time = start_time

    best_assignment = None

    if best_asset_id is not None and best_start_time is not None:
        best_assignment = (best_asset_id, best_start_time)

    return best_assignment


## @brief Create an AI plan using an uncertainty-aware heuristic.
## @details
## The AI planner sorts incidents by:
## 1. Higher expected utility density
## 2. Fewer compatible assets first
## 3. Earlier latest finish
##
## It then assigns incidents while preserving flexible assets when possible.
## @param episode Episode containing incidents and assets.
## @return Constructed AI plan.
def create_ai_plan(episode: Episode) -> Plan:
    sorted_incidents = sorted(
        episode.incidents,
        key=lambda incident: (
            -compute_incident_score(incident),
            count_compatible_assets(incident, episode.assets),
            incident.latest_finish,
        ),
    )

    occupancy_map = build_asset_occupancy_map(episode.assets)
    plan = Plan(plan_name="ai")

    for incident in sorted_incidents:
        best_assignment = find_best_feasible_assignment(
            incident=incident,
            assets=episode.assets,
            occupancy_map=occupancy_map,
        )

        if best_assignment is not None:
            asset_id, start_time = best_assignment
            end_time = start_time + incident.duration
            requested_slots = set(range(start_time, end_time))

            occupancy_map[asset_id].update(requested_slots)
            plan.add_assignment(
                PlanAssignment(
                    incident_id=incident.incident_id,
                    asset_id=asset_id,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

    return plan
