"""Default simulation configuration schema for HMT experiments."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    #: Number of assets available in each episode.
    """Container for simulation configuration values.

    This dataclass provides default parameters for the simulator and defines the
    valid fields that may be overridden by JSON configuration files passed through
    the command-line interface.
    """
    num_assets: int = 3

    #: Number of incidents generated in each episode.
    num_incidents: int = 8

    #: Number of discrete time slots in the planning horizon.
    num_time_slots: int = 10

    #: Minimum incident priority value.
    min_priority: int = 5

    #: Maximum incident priority value.
    max_priority: int = 20

    #: Minimum incident duration in time slots.
    min_duration: int = 1

    #: Maximum incident duration in time slots.
    max_duration: int = 3

    #: Alpha parameter for the Beta-distributed success probability.
    beta_alpha: float = 5.0

    #: Beta parameter for the Beta-distributed success probability.
    beta_beta: float = 2.0

    #: Random seed used for reproducible episode generation.
    seed: int = 42
    