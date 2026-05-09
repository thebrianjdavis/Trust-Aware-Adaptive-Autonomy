## @file generator.py
## @brief Episode generation for the HMT resource allocation MVP.

from __future__ import annotations

import random
from typing import List

from config import SimulationConfig
from data.calibration.fema_distribution import (
    FemaCalibrationData,
    map_incident_type_to_capability,
    sample_duration_slots,
    sample_incident_type,
)
from src.environment.models import Asset, Episode, Incident


## @brief Generate a fixed set of assets for the MVP scenario.
## @param config Simulation configuration values.
## @return List of generated assets.
def generate_assets(config: SimulationConfig) -> List[Asset]:
    assets: List[Asset] = []

    predefined_assets = [
        Asset(
            asset_id="A1",
            capabilities={"medical"},
            available_time_slots=set(range(config.num_time_slots)),
        ),
        Asset(
            asset_id="A2",
            capabilities={"logistics"},
            available_time_slots=set(range(config.num_time_slots)),
        ),
        Asset(
            asset_id="A3",
            capabilities={"medical", "logistics"},
            available_time_slots=set(range(config.num_time_slots)),
        ),
    ]

    assets.extend(predefined_assets[: config.num_assets])

    return assets


## @brief Generate synthetic incidents for one episode using FEMA-derived sampling.
## @param config Simulation configuration values.
## @param rng Random number generator.
## @param calibration_data FEMA-derived calibration data.
## @return List of generated incidents.
def generate_incidents(
    config: SimulationConfig,
    rng: random.Random,
    calibration_data: FemaCalibrationData,
) -> List[Incident]:
    incidents: List[Incident] = []

    for incident_index in range(config.num_incidents):
        incident_type = sample_incident_type(calibration_data, rng)
        required_capability = map_incident_type_to_capability(incident_type)
        duration = sample_duration_slots(calibration_data, rng)

        duration = max(config.min_duration, min(config.max_duration, duration))

        earliest_start = rng.randint(0, config.num_time_slots - duration)
        latest_finish = rng.randint(earliest_start + duration, config.num_time_slots)
        priority = rng.randint(config.min_priority, config.max_priority)
        success_probability = rng.betavariate(config.beta_alpha, config.beta_beta)

        incidents.append(
            Incident(
                incident_id=f"I{incident_index + 1}",
                priority=priority,
                duration=duration,
                earliest_start=earliest_start,
                latest_finish=latest_finish,
                success_probability=success_probability,
                required_capability=required_capability,
            )
        )

    return incidents


## @brief Generate one full episode consisting of incidents and assets.
## @param config Simulation configuration values.
## @param calibration_data FEMA-derived calibration data.
## @param rng Random number generator. If None, a reproducible RNG is created from config.seed.
## @return Generated episode.
def generate_episode(
    config: SimulationConfig,
    calibration_data: FemaCalibrationData,
    rng: random.Random | None = None,
) -> Episode:
    episode_rng = rng if rng is not None else random.Random(config.seed)
    assets = generate_assets(config)
    incidents = generate_incidents(config, episode_rng, calibration_data)

    episode = Episode(
        incidents=incidents,
        assets=assets,
        num_time_slots=config.num_time_slots,
    )

    return episode
