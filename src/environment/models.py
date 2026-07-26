"""Core data models for the HMT resource allocation MVP."""

from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass(frozen=True)
class Incident:
    #: Unique incident identifier.
    """Represents a single incident requiring a resource allocation."""
    incident_id: str

    #: Utility value awarded if the incident is completed successfully.
    priority: int

    #: Number of discrete time slots required to service the incident.
    duration: int

    #: Earliest feasible incident start time.
    earliest_start: int

    #: Latest feasible incident finish time.
    latest_finish: int

    #: Probability that the incident succeeds if assigned.
    success_probability: float

    #: Capability required to service the incident.
    required_capability: str


@dataclass(frozen=True)
class Asset:
    #: Unique asset identifier.
    """Represents a response asset that can service incidents."""
    asset_id: str

    #: Set of capabilities supported by the asset.
    capabilities: Set[str]

    #: Set of time slots during which the asset is available.
    available_time_slots: Set[int]


@dataclass(frozen=True)
class PlanAssignment:
    #: Identifier of the assigned incident.
    """Represents a single incident-to-asset assignment."""
    incident_id: str

    #: Identifier of the assigned asset.
    asset_id: str

    #: Inclusive assignment start time.
    start_time: int

    #: Exclusive assignment end time.
    end_time: int


@dataclass
class Plan:
    #: Name of the plan.
    """Represents a full plan containing zero or more assignments."""
    plan_name: str

    #: Collection of assignments contained in the plan.
    assignments: List[PlanAssignment] = field(default_factory=list)

    def add_assignment(self, assignment: PlanAssignment) -> None:
        """Append a new assignment to the plan.

        Args:
            assignment: Assignment to append.
        """
        self.assignments.append(assignment)

    def get_assignment_for_incident(self, incident_id: str) -> Optional[PlanAssignment]:
        """Return the assignment for the requested incident if present.

        Args:
            incident_id: Incident identifier to search for.

        Returns:
            Matching assignment or None.
        """
        assignment: Optional[PlanAssignment] = None

        for current_assignment in self.assignments:
            if current_assignment.incident_id == incident_id:
                assignment = current_assignment
                break

        return assignment


@dataclass(frozen=True)
class Episode:
    #: Incidents generated for the episode.
    """Represents one simulated planning episode."""
    incidents: List[Incident]

    #: Assets available for the episode.
    assets: List[Asset]

    #: Number of discrete time slots in the episode.
    num_time_slots: int


@dataclass(frozen=True)
class PlanEvaluation:
    #: Name of the evaluated plan.
    """Stores utility results for a single evaluated plan."""
    plan_name: str

    #: Total realized utility for the plan.
    total_utility: int

    #: Incident identifiers that completed successfully.
    successful_incident_ids: List[str]

    #: Incident identifiers that were attempted but failed.
    failed_incident_ids: List[str]
    