"""Build FEMA-derived empirical distributions for simulator calibration."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd


#: Maps FEMA incident types to simulator capabilities.
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


@dataclass(frozen=True)
class FemaCalibrationData:
    #: FEMA incident types available for sampling.
    """Stores FEMA-derived sampling distributions for the simulator."""
    incident_types: List[str]

    #: Sampling weights aligned with incident_types.
    incident_type_weights: List[float]

    #: FEMA-derived duration slot samples.
    duration_slots: List[int]


def map_duration_days_to_slots(duration_days: float) -> int:
    """Convert a FEMA disaster duration in days into a simulator slot duration.

    Args:
        duration_days: FEMA duration in days.

    Returns:
        Simulator duration in slots.
    """
    duration_slots = 1

    if duration_days <= 5:
        duration_slots = 1
    elif duration_days <= 20:
        duration_slots = 2
    else:
        duration_slots = 3

    return duration_slots


def load_fema_calibration_data(csv_path: str | Path) -> FemaCalibrationData:
    """Load and process FEMA data for simulator calibration.

    Args:
        csv_path: Path to the FEMA-style disaster declarations CSV.

    Returns:
        FEMA calibration data object.
    """
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


def sample_incident_type(
    calibration_data: FemaCalibrationData,
    rng: random.Random,
) -> str:
    """Sample a FEMA-derived incident type.

    Args:
        calibration_data: FEMA calibration data.
        rng: Random number generator.

    Returns:
        Sampled FEMA incident type.
    """
    incident_type = rng.choices(
        population=calibration_data.incident_types,
        weights=calibration_data.incident_type_weights,
        k=1,
    )[0]
    return incident_type


def map_incident_type_to_capability(incident_type: str) -> str:
    """Convert a FEMA incident type into a simulator capability.

    Args:
        incident_type: FEMA incident type.

    Returns:
        Simulator capability label.
    """
    required_capability = FEMA_TYPE_TO_CAPABILITY[incident_type]
    return required_capability


def sample_duration_slots(
    calibration_data: FemaCalibrationData,
    rng: random.Random,
) -> int:
    """Sample a FEMA-derived simulator duration.

    Args:
        calibration_data: FEMA calibration data.
        rng: Random number generator.

    Returns:
        Sampled duration in simulator slots.
    """
    duration_slots = rng.choice(calibration_data.duration_slots)
    return duration_slots
