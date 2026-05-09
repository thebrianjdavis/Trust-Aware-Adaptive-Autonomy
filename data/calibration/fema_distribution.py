## @file fema_distribution.py
## @brief Build FEMA-derived empirical distributions for simulator calibration.

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


## @brief Maps FEMA incident types to simulator capabilities.
FEMA_TYPE_TO_CAPABILITY: Dict[str, str] = {
    "Biological": "medical",
    "Chemical": "medical",
    "Toxic Substances": "medical",
    "Terrorist": "medical",
    "Human Cause": "medical",
    "Fire": "medical",
    "Earthquake": "medical",
    "Severe Storm": "logistics",
    "Hurricane": "logistics",
    "Flood": "logistics",
    "Snowstorm": "logistics",
    "Severe Ice Storm": "logistics",
    "Tornado": "logistics",
    "Drought": "logistics",
    "Tropical Storm": "logistics",
    "Coastal Storm": "logistics",
    "Freezing": "logistics",
    "Winter Storm": "logistics",
    "Typhoon": "logistics",
    "Volcanic Eruption": "logistics",
    "Mud/Landslide": "logistics",
    "Fishing Losses": "logistics",
    "Dam/Levee Break": "logistics",
    "Tsunami": "logistics",
    "Straight-Line Winds": "logistics",
    "Tropical Depression": "logistics",
    "Other": "logistics",
}


## @brief Stores FEMA-derived sampling distributions for the simulator.
@dataclass(frozen=True)
class FemaCalibrationData:
    ## @brief FEMA incident types available for sampling.
    incident_types: List[str]

    ## @brief Sampling weights aligned with incident_types.
    incident_type_weights: List[float]

    ## @brief FEMA-derived duration slot samples.
    duration_slots: List[int]


## @brief Convert a FEMA disaster duration in days into a simulator slot duration.
## @param duration_days FEMA duration in days.
## @return Simulator duration in slots.
def map_duration_days_to_slots(duration_days: float) -> int:
    duration_slots = 1

    if duration_days <= 5:
        duration_slots = 1
    elif duration_days <= 20:
        duration_slots = 2
    else:
        duration_slots = 3

    return duration_slots


## @brief Load and process FEMA data for simulator calibration.
## @param csv_path Path to the FEMA-style disaster declarations CSV.
## @return FEMA calibration data object.
def load_fema_calibration_data(csv_path: str | Path) -> FemaCalibrationData:
    df = pd.read_csv(csv_path)

    df["incident_begin_date"] = pd.to_datetime(
        df["incident_begin_date"],
        errors="coerce",
    )
    df["incident_end_date"] = pd.to_datetime(
        df["incident_end_date"],
        errors="coerce",
    )

    df["duration_days"] = (
        df["incident_end_date"] - df["incident_begin_date"]
    ).dt.days

    df = df[df["incident_type"].notna()].copy()
    df = df[df["incident_type"].isin(FEMA_TYPE_TO_CAPABILITY.keys())].copy()
    df = df[df["duration_days"].notna()].copy()
    df = df[df["duration_days"] >= 0].copy()

    incident_type_probabilities = (
        df["incident_type"]
        .value_counts(normalize=True)
        .sort_values(ascending=False)
    )

    incident_types = incident_type_probabilities.index.tolist()
    incident_type_weights = incident_type_probabilities.values.tolist()

    duration_slots = [
        map_duration_days_to_slots(duration_days)
        for duration_days in df["duration_days"].tolist()
    ]

    calibration_data = FemaCalibrationData(
        incident_types=incident_types,
        incident_type_weights=incident_type_weights,
        duration_slots=duration_slots,
    )

    return calibration_data


## @brief Sample a FEMA-derived incident type.
## @param calibration_data FEMA calibration data.
## @param rng Random number generator.
## @return Sampled FEMA incident type.
def sample_incident_type(
    calibration_data: FemaCalibrationData,
    rng: random.Random,
) -> str:
    incident_type = rng.choices(
        population=calibration_data.incident_types,
        weights=calibration_data.incident_type_weights,
        k=1,
    )[0]
    return incident_type


## @brief Convert a FEMA incident type into a simulator capability.
## @param incident_type FEMA incident type.
## @return Simulator capability label.
def map_incident_type_to_capability(incident_type: str) -> str:
    required_capability = FEMA_TYPE_TO_CAPABILITY[incident_type]
    return required_capability


## @brief Sample a FEMA-derived simulator duration.
## @param calibration_data FEMA calibration data.
## @param rng Random number generator.
## @return Sampled duration in simulator slots.
def sample_duration_slots(
    calibration_data: FemaCalibrationData,
    rng: random.Random,
) -> int:
    duration_slots = rng.choice(calibration_data.duration_slots)
    return duration_slots
