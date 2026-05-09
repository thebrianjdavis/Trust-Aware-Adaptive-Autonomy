## @file config.py
## @brief Configuration values for the HMT resource allocation MVP.

from dataclasses import dataclass


## @brief Container for simulation configuration values.
@dataclass(frozen=True)
class SimulationConfig:
    ## @brief Number of assets available in each episode.
    num_assets: int = 4

    ## @brief Number of incidents generated in each episode.
    num_incidents: int = 18

    ## @brief Number of discrete time slots in the planning horizon.
    num_time_slots: int = 20

    ## @brief Minimum incident priority value.
    min_priority: int = 5

    ## @brief Maximum incident priority value.
    max_priority: int = 20

    ## @brief Minimum incident duration in time slots.
    min_duration: int = 1

    ## @brief Maximum incident duration in time slots.
    max_duration: int = 3

    ## @brief Alpha parameter for the Beta-distributed success probability.
    beta_alpha: float = 5.0

    ## @brief Beta parameter for the Beta-distributed success probability.
    beta_beta: float = 2.0

    ## @brief Random seed used for reproducible episode generation.
    seed: int = 42
    