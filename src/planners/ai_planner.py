"""AI planner for the HMT resource allocation MVP."""

from typing import Dict, List, Set

from src.environment.models import Asset, Episode, Incident, Plan, PlanAssignment


def build_asset_occupancy_map(assets: List[Asset]) -> Dict[str, Set[int]]:
    """Create an empty occupancy map for each asset.

    Args:
        assets: Assets available in the episode.

    Returns:
        Dictionary mapping asset identifiers to occupied time slots.
    """
    occupancy_map: Dict[str, Set[int]] = {}

    for asset in assets:
        occupancy_map[asset.asset_id] = set()

    return occupancy_map


def get_candidate_start_times(incident: Incident) -> List[int]:
    """Return all feasible start times for an incident.

    Args:
        incident: Incident to evaluate.

    Returns:
        Candidate start times.
    """
    candidate_start_times: List[int] = []
    latest_start = incident.latest_finish - incident.duration

    for start_time in range(incident.earliest_start, latest_start + 1):
        candidate_start_times.append(start_time)

    return candidate_start_times


def is_assignment_feasible(
    incident: Incident,
    asset: Asset,
    start_time: int,
    occupancy_map: Dict[str, Set[int]],
) -> bool:
    """Check whether an incident can be assigned to an asset at a start time.

    Args:
        incident: Incident to assign.
        asset: Candidate asset.
        start_time: Proposed start time.
        occupancy_map: Current asset occupancy map.

    Returns:
        True if assignment is feasible, otherwise False.
    """
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


def compute_incident_score(incident: Incident) -> float:
    """Compute an incident score for the AI planner.

    The score favors high-priority, high-probability, shorter-duration incidents.

    Args:
        incident: Incident to score.

    Returns:
        Incident score.
    """
    score = (incident.priority * incident.success_probability) / incident.duration
    return score


def count_compatible_assets(incident: Incident, assets: List[Asset]) -> int:
    """Count how many assets can service the incident.

    Args:
        incident: Incident to evaluate.
        assets: Available assets.

    Returns:
        Number of compatible assets.
    """
    compatible_asset_count = 0

    for asset in assets:
        if incident.required_capability in asset.capabilities:
            compatible_asset_count += 1

    return compatible_asset_count


def compute_assignment_rank(
    asset: Asset,
    start_time: int,
    occupancy_map: Dict[str, Set[int]],
) -> tuple[int, int, int]:
    """Compute a ranking tuple for a candidate asset assignment.

    Lower tuples are preferred. The planner prefers:
    1. Less flexible assets first, preserving flexible assets for later.
    2. Earlier start times.
    3. Lower current occupancy to spread load when possible.

    Args:
        asset: Candidate asset.
        start_time: Proposed assignment start time.
        occupancy_map: Current asset occupancy map.

    Returns:
        Ranking tuple for lexicographic comparison.
    """
    asset_flexibility = len(asset.capabilities)
    current_occupancy = len(occupancy_map[asset.asset_id])
    assignment_rank = (asset_flexibility, start_time, current_occupancy)
    return assignment_rank


def find_best_feasible_assignment(
    incident: Incident,
    assets: List[Asset],
    occupancy_map: Dict[str, Set[int]],
) -> tuple[str, int] | None:
    """Find the best feasible asset/start-time pair for an incident.

    Args:
        incident: Incident to assign.
        assets: Assets available in the episode.
        occupancy_map: Current asset occupancy map.

    Returns:
        Best asset/start-time tuple if found, otherwise None.
    """
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


def create_ai_plan(episode: Episode) -> Plan:
    """Create an AI plan using an uncertainty-aware heuristic.

    The AI planner sorts incidents by:
    1. Higher expected utility density
    2. Fewer compatible assets first
    3. Earlier latest finish
    It then assigns incidents while preserving flexible assets when possible.

    Args:
        episode: Episode containing incidents and assets.

    Returns:
        Constructed AI plan.
    """
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
