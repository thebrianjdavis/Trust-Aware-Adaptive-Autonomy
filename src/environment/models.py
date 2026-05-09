## @file models.py
## @brief Core data models for the HMT resource allocation MVP.

from dataclasses import dataclass, field
from typing import List, Optional, Set


## @brief Represents a single incident requiring a resource allocation.
@dataclass(frozen=True)
class Incident:
    ## @brief Unique incident identifier.
    incident_id: str

    ## @brief Utility value awarded if the incident is completed successfully.
    priority: int

    ## @brief Number of discrete time slots required to service the incident.
    duration: int

    ## @brief Earliest feasible incident start time.
    earliest_start: int

    ## @brief Latest feasible incident finish time.
    latest_finish: int

    ## @brief Probability that the incident succeeds if assigned.
    success_probability: float

    ## @brief Capability required to service the incident.
    required_capability: str


## @brief Represents a response asset that can service incidents.
@dataclass(frozen=True)
class Asset:
    ## @brief Unique asset identifier.
    asset_id: str

    ## @brief Set of capabilities supported by the asset.
    capabilities: Set[str]

    ## @brief Set of time slots during which the asset is available.
    available_time_slots: Set[int]


## @brief Represents a single incident-to-asset assignment.
@dataclass(frozen=True)
class PlanAssignment:
    ## @brief Identifier of the assigned incident.
    incident_id: str

    ## @brief Identifier of the assigned asset.
    asset_id: str

    ## @brief Inclusive assignment start time.
    start_time: int

    ## @brief Exclusive assignment end time.
    end_time: int


## @brief Represents a full plan containing zero or more assignments.
@dataclass
class Plan:
    ## @brief Name of the plan.
    plan_name: str

    ## @brief Collection of assignments contained in the plan.
    assignments: List[PlanAssignment] = field(default_factory=list)

    ## @brief Append a new assignment to the plan.
    ## @param assignment Assignment to append.
    def add_assignment(self, assignment: PlanAssignment) -> None:
        self.assignments.append(assignment)

    ## @brief Return the assignment for the requested incident if present.
    ## @param incident_id Incident identifier to search for.
    ## @return Matching assignment or None.
    def get_assignment_for_incident(self, incident_id: str) -> Optional[PlanAssignment]:
        assignment: Optional[PlanAssignment] = None

        for current_assignment in self.assignments:
            if current_assignment.incident_id == incident_id:
                assignment = current_assignment
                break

        return assignment


## @brief Represents one simulated planning episode.
@dataclass(frozen=True)
class Episode:
    ## @brief Incidents generated for the episode.
    incidents: List[Incident]

    ## @brief Assets available for the episode.
    assets: List[Asset]

    ## @brief Number of discrete time slots in the episode.
    num_time_slots: int


## @brief Stores utility results for a single evaluated plan.
@dataclass(frozen=True)
class PlanEvaluation:
    ## @brief Name of the evaluated plan.
    plan_name: str

    ## @brief Total realized utility for the plan.
    total_utility: int

    ## @brief Incident identifiers that completed successfully.
    successful_incident_ids: List[str]

    ## @brief Incident identifiers that were attempted but failed.
    failed_incident_ids: List[str]
    