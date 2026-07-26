# Data Grounding

The stochastic environment is partially grounded in the
[US Natural Disaster Declarations](https://www.kaggle.com/datasets/headsortails/us-natural-disaster-declarations)
dataset. The calibration analysis used 68,485 records containing historical
incident categories and event durations.

## What the data grounds

FEMA-derived data provides:

- empirical incident-type frequencies;
- incident-duration distributions;
- disaster-category-driven capability mappings.

The dataset does **not** provide task-level success probabilities, priorities,
or operational outcome labels. Those quantities are explicitly modeled.

> FEMA data grounds the structure of the simulated environment, while
> stochastic modeling defines task uncertainty, task value, and outcome
> realization.

## Incident type calibration

| Incident type | Approximate frequency |
|---|---:|
| Severe Storm | 28% |
| Hurricane | 20% |
| Flood | 16% |
| Biological | 11% |
| Fire | 6% |
| Snowstorm | 5% |

Disaster categories are mapped to tactical capabilities:

| FEMA category | Simulator capability |
|---|---|
| Biological, Chemical, Toxic Substances, Terrorist, Fire, Earthquake | `medical` |
| Storms, Hurricanes, Floods, Snow/Ice, Tornado, Drought, Coastal events | `logistics` |

## Duration calibration

FEMA declaration duration is calculated as:

```text
duration_days = incident_end_date - incident_begin_date
```

| Metric | Observed value |
|---|---:|
| Median | 13 days |
| 75th percentile | 40 days |
| Mean | approximately 159 days |

Because declarations represent long-duration operations, durations are
compressed into a ten-slot tactical planning horizon:

| FEMA duration | Simulator duration |
|---|---:|
| 0–5 days | 1 slot |
| 6–20 days | 2 slots |
| More than 20 days | 3 slots |

This preserves relative variability without treating declaration length as a
literal task duration.

## Incident generation model

| Parameter | Source |
|---|---|
| Incident type | Empirical FEMA frequency |
| Capability requirement | Deterministic incident mapping |
| Incident duration | FEMA-derived distribution |
| Incident priority | Uniform range from 5 to 20 |
| Success probability | Beta(5, 2) reliability model |

Task success probability and outcome are modeled as:

\[
p_i \sim \operatorname{Beta}(\alpha, \beta)
\]

\[
Y_i \sim \operatorname{Bernoulli}(p_i)
\]

The simulation combines empirical disaster statistics,
[Vehicle Routing Problems with Time Windows](http://www.vrp-rep.org/variants/item/vrptw.html)-inspired
scheduling structures, and stochastic reliability modeling. See the
[calibration API](../api-reference/data-calibration.md) for implementation
details.
