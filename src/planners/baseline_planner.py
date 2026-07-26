"""Supervisor-only baseline heuristic planner."""

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


def assign_incident_if_possible(
    incident: Incident,
    assets: List[Asset],
    occupancy_map: Dict[str, Set[int]],
    plan: Plan,
) -> bool:
    """Assign an incident using a first-fit heuristic if possible.

    Args:
        incident: Incident to assign.
        assets: Assets available in the episode.
        occupancy_map: Current asset occupancy map.
        plan: Plan being constructed.

    Returns:
        True if assignment was made, otherwise False.
    """
    assignment_made = False

    for asset in assets:
        candidate_start_times = get_candidate_start_times(incident)

        for start_time in candidate_start_times:
            if is_assignment_feasible(incident, asset, start_time, occupancy_map):
                end_time = start_time + incident.duration
                requested_slots = set(range(start_time, end_time))

                occupancy_map[asset.asset_id].update(requested_slots)
                plan.add_assignment(
                    PlanAssignment(
                        incident_id=incident.incident_id,
                        asset_id=asset.asset_id,
                        start_time=start_time,
                        end_time=end_time,
                    )
                )
                assignment_made = True
                break

        if assignment_made:
            break

    return assignment_made


def create_baseline_plan(episode: Episode) -> Plan:
    """Create a supervisor-only baseline plan using a greedy heuristic.

    Args:
        episode: Episode containing incidents and assets.

    Returns:
        Constructed baseline plan.
    """
    sorted_incidents = sorted(
        episode.incidents,
        key=lambda incident: -incident.priority,
    )

    occupancy_map = build_asset_occupancy_map(episode.assets)
    plan = Plan(plan_name="baseline")

    for incident in sorted_incidents:
        assign_incident_if_possible(
            incident=incident,
            assets=episode.assets,
            occupancy_map=occupancy_map,
            plan=plan,
        )

    return plan
