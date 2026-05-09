# Dataset Calibration

This project grounds its stochastic simulation environment in publicly available FEMA disaster declaration data.

Dataset used:

**US Natural Disaster Declarations**  
https://www.kaggle.com/datasets/headsortails/us-natural-disaster-declarations

Records analyzed: **68,485**

The dataset contains historical disaster declarations in the United States, including disaster type and event duration. These statistics are used to calibrate the generative model that produces incidents for the simulation environment.

---

# Incident Type Calibration

Incident types in the simulator are **sampled directly from the empirical distribution of FEMA incident types**.

The most common disaster types in the dataset include:

| Incident Type | Approximate Frequency |
|---|---|
| Severe Storm | ~28% |
| Hurricane | ~20% |
| Flood | ~16% |
| Biological | ~11% |
| Fire | ~6% |
| Snowstorm | ~5% |

These disaster categories represent different operational response scenarios.

In the simulation environment, FEMA disaster types are mapped to two high-level tactical capability classes:

| FEMA Incident Type | Simulator Capability |
|---|---|
| Biological, Chemical, Toxic Substances, Terrorist, Fire, Earthquake | medical |
| Storms, Hurricanes, Floods, Snow/Ice, Tornado, Drought, Coastal events | logistics |

This mapping converts large-scale disasters into **tactical response tasks** suitable for short-term operational planning.

---

# Incident Duration Calibration

FEMA disaster declaration durations were computed as:
```
duration_days = incident_end_date − incident_begin_date
```

Observed statistics:

| Metric | Value |
|---|---|
| Median duration | 13 days |
| 75th percentile | 40 days |
| Mean | ~159 days (skewed by very long declarations) |

Because FEMA declarations represent **long-duration disaster management operations**, the simulation compresses these events into a short tactical planning horizon.

Duration mapping used in the simulator:

| FEMA Duration | Simulator Duration |
|---|---|
| 0-5 days | 1 planning slot |
| 6-20 days | 2 planning slots |
| >20 days | 3 planning slots |

This allows the simulator to preserve **relative duration variability** while operating within a manageable 10-slot planning horizon.

---

# Incident Generation Model

Each simulation episode generates incidents using FEMA-calibrated distributions:

| Parameter | Source |
|---|---|
| Incident type | Sampled from empirical FEMA incident-type frequency |
| Capability requirement | Deterministic mapping from incident type |
| Incident duration | Derived from FEMA duration distribution |
| Incident priority | Uniform(5,20) severity range |
| Success probability | Beta(5,2) reliability model |

Success probabilities are not present in the FEMA dataset, so a **Beta-Bernoulli reliability model** is used to represent uncertain task completion outcomes.

---

# Scheduling Structure

Scheduling constraints follow structures similar to the **Solomon Vehicle Routing Problem with Time Windows (VRPTW)** benchmark datasets:

http://www.vrp-rep.org/variants/item/vrptw.html

These benchmarks provide canonical examples of resource-constrained scheduling with time windows, which closely resemble disaster response task allocation problems.

---

# Summary

The simulation environment combines:

- **Empirical disaster statistics from FEMA**
- **Logistics scheduling structure from VRPTW benchmarks**
- **Stochastic reliability modeling**

This produces a **data-grounded but computationally tractable environment** for evaluating trust-aware adaptive autonomy in human-machine teaming systems.
