# Trust-Aware Adaptive Autonomy for Resource Allocation Under Uncertainty

This repository contains a simulation framework for studying **trust-aware adaptive autonomy** in human-machine teaming (HMT) resource allocation under uncertainty. The system models a disaster-response-inspired decision environment in which a machine teammate proposes resource allocation plans, a simulated supervisor may accept or override those recommendations, and the autonomy system adapts the strength of its intervention based on AI confidence, machine-side trust, and observed supervisor behavior.

The project is designed as a research prototype for exploring how adaptive autonomy can regulate reliance behavior under undertrust, calibrated trust, and overtrust. It supports single-seed demonstrations, multi-seed Monte Carlo experiments, ablation studies, sensitivity analysis, result visualization, and reproducible run metadata.

---

## Documentation

[Explore the Material for MkDocs portal](https://thebrianjdavis.github.io/Trust-Aware-Adaptive-Autonomy/) for the research overview, concepts, architecture, experiment guides, results, and generated Python API reference.

---

## Research Motivation

Human-machine teams can fail when trust is miscalibrated. If a human supervisor undertrusts an AI system, useful recommendations may be ignored. If the supervisor overtrusts the AI, poor recommendations may be accepted too readily. In both cases, the problem is not simply whether the AI can produce a plan, but whether the human-machine team relies on that plan appropriately.

This repository studies a behavior-aware adaptive autonomy mechanism that changes the *strength* of AI recommendations rather than only changing the plan itself. The controller is designed to:

- increase intervention strength when supervisor behavior suggests undertrust,
- decrease intervention strength when supervisor behavior suggests overtrust,
- remain minimally invasive when supervisor behavior is already calibrated.

The long-term research direction is to understand when trust-aware autonomy improves team behavior, when it improves task performance, and when those two objectives diverge.

---

## Research Questions

The current system is organized around the following research questions:

1. **Reliance Regulation:** Can behavior-aware adaptive autonomy shift supervisor reliance in the intended direction under simulated undertrust and overtrust?
2. **Performance Impact:** Does correcting reliance behavior improve executed utility, and under what scenario conditions?
3. **Ablation:** Is supervisor behavior feedback necessary, or can AI confidence and machine-side trust alone produce comparable adaptation?
4. **Sensitivity:** How sensitive are the results to workload, resource scarcity, task-success uncertainty, and AI reliability?
5. **Generalization:** Which scenario regimes expose the strengths and limitations of trust-aware adaptive autonomy?

---

## Conceptual Overview

Each experiment consists of repeated simulated resource allocation episodes.

For each episode:

1. A disaster-response-inspired scenario is generated.
2. A baseline planner creates a supervisor-only comparison plan.
3. An AI planner creates an uncertainty-aware plan.
4. Both plans are evaluated under stochastic task outcomes.
5. A Bayesian trust model updates the machine-side estimate of AI helpfulness.
6. The autonomy controller computes an intervention score.
7. The intervention score is mapped to weak, normal, or strong recommendation strength.
8. A simulated supervisor policy accepts or overrides the AI recommendation.
9. Executed utility, acceptance behavior, recommendation strength, and trust state are recorded.

The key distinction is that the AI is not only planning. The system is also regulating how strongly the AI recommendation is presented based on confidence, trust, and supervisor behavior.

---

## Data Grounding

The simulation environment is partially grounded using the FEMA Disaster Declarations dataset.

The FEMA data is used to derive:

- empirical incident type frequencies,
- incident duration distributions,
- disaster-category-driven task capability mappings.

The FEMA dataset does **not** provide task-level success probabilities, task-level priority labels, or operational outcome labels. Those quantities are explicitly modeled in the simulator.

This produces a hybrid methodology:

> FEMA data grounds the structure of the simulated environment, while stochastic modeling defines task uncertainty, task value, and outcome realization.

Additional details are documented in the
[data-grounding guide](https://thebrianjdavis.github.io/Trust-Aware-Adaptive-Autonomy/concepts/data-grounding/).

---

## Simulation Environment

Each episode contains:

- a set of incidents,
- a set of response assets,
- a finite planning horizon,
- task time windows,
- task durations,
- task priorities,
- task success probabilities,
- required capabilities.

The default configuration is defined in `config.py` by the `SimulationConfig` dataclass. JSON configuration files in `configs/` can override these defaults for sensitivity analysis.

### Default Simulation Parameters

| Parameter | Default | Description |
|---|---:|---|
| `num_assets` | 3 | Number of response assets |
| `num_incidents` | 8 | Number of incidents per episode |
| `num_time_slots` | 10 | Discrete planning horizon |
| `min_priority` | 5 | Minimum task utility value |
| `max_priority` | 20 | Maximum task utility value |
| `min_duration` | 1 | Minimum task duration |
| `max_duration` | 3 | Maximum task duration |
| `beta_alpha` | 5.0 | Alpha parameter for task success probability |
| `beta_beta` | 2.0 | Beta parameter for task success probability |
| `seed` | 42 | Default random seed |

Task success probability is sampled from a Beta distribution:

```text
p_i ~ Beta(alpha, beta)
```

Task outcomes are sampled as Bernoulli random variables:

```text
Y_i ~ Bernoulli(p_i)
```

Utility is computed from successful task completions:

```text
U = sum(priority_i * 1(success_i))
```

---

## Planners

The framework compares two interpretable heuristic planners.

### Baseline Planner

The baseline planner represents a supervisor-only heuristic. It sorts incidents by priority and uses a first-fit feasible assignment strategy.

Implemented in:

```text
src/planners/baseline_planner.py
```

### AI Planner

The AI planner uses an uncertainty-aware heuristic. It sorts incidents using expected utility density:

```text
score_i = (priority_i * success_probability_i) / duration_i
```

It also considers compatible asset scarcity and latest finish time. The planner is intentionally interpretable rather than globally optimized.

Implemented in:

```text
src/planners/ai_planner.py
```

---

## Trust Model

Trust is modeled as a machine-side estimate of AI helpfulness using a Beta-Bernoulli update.

After each episode, the system compares AI utility against baseline utility:

- If AI utility is greater than baseline utility, alpha is incremented.
- If baseline utility is greater than AI utility, beta is incremented.
- If the utilities tie, the posterior is unchanged.

The trust score is the posterior mean:

```text
T = alpha / (alpha + beta)
```

This trust value estimates whether the AI is likely to improve team performance relative to the baseline.

Implemented in:

```text
src/trust/beta_trust_model.py
```

---

## Supervisor Policies

The simulator includes three supervisor behavior models.

| Supervisor Mode | Behavior |
|---|---|
| `undertrust` | Rejects AI recommendations too often |
| `calibrated` | Accepts or overrides more appropriately based on confidence and trust |
| `overtrust` | Accepts AI recommendations too often |

Each supervisor policy maps AI confidence, trust, and recommendation strength into an acceptance probability.

Implemented in:

```text
src/supervisor/supervisor_policies.py
```

---

## Adaptive Autonomy

The adaptive autonomy controller computes an intervention score using:

- AI confidence,
- machine-side trust estimate,
- smoothed supervisor override behavior.

The full adaptive intervention score is:

```text
I = w_c * C + w_t * T + w_o * B
```

where:

- `C` is AI confidence,
- `T` is trust,
- `B` is a centered supervisor behavior signal,
- `w_c`, `w_t`, and `w_o` are controller weights.

The centered behavior signal is derived from the supervisor override rate. High override rates indicate undertrust-like behavior and increase intervention strength. Low override rates indicate overtrust-like behavior and decrease intervention strength.

The intervention score is mapped to recommendation strength:

| Score Range | Recommendation Strength |
|---|---|
| Below weak threshold | `weak` |
| Between thresholds | `normal` |
| Above strong threshold | `strong` |

Implemented in:

```text
src/autonomy/adaptive_autonomy.py
```

---

## Study Modes

The framework supports two study modes.

### Standard Study

The standard study compares:

1. `fixed`
2. `adaptive`

The fixed condition always uses normal recommendation strength. The adaptive condition uses the full confidence + trust + behavior controller.

### Ablation Study

The ablation study compares:

1. `fixed`
2. `confidence_trust`
3. `behavior_only`
4. `adaptive`

| Mode | Description |
|---|---|
| `fixed` | Always normal recommendation strength |
| `confidence_trust` | Uses AI confidence and trust only |
| `behavior_only` | Uses supervisor override behavior only |
| `adaptive` | Uses confidence, trust, and supervisor override behavior |

The ablation study is intended to identify whether supervisor behavior feedback is necessary for trust calibration.

---

## Sensitivity Configurations

Sensitivity analysis is performed by passing JSON configuration files through the command line.

Available configurations:

| Config File | Purpose |
|---|---|
| `configs/baseline.json` | Default scenario |
| `configs/high_workload.json` | Increased task density |
| `configs/scarce_resources.json` | Reduced asset availability |
| `configs/moderate_uncertainty.json` | Lower task success probability |
| `configs/high_reliability.json` | Higher task success probability |
| `configs/stress.json` | Combined high workload, resource scarcity, and uncertainty |

Example:

```bash
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/high_workload.json --visualize
```

---

## Running Experiments

### Single-Seed Standard Run

```bash
python main.py --mode single-seed --study standard --episodes 100 --visualize
```

### Multi-Seed Standard Run

```bash
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/baseline.json --visualize
```

### Multi-Seed Ablation Run

```bash
python main.py --mode multi-seed --study ablation --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/baseline.json --visualize
```

### Sensitivity Sweep Examples

```bash
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/high_workload.json --visualize
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/scarce_resources.json --visualize
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/moderate_uncertainty.json --visualize
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/high_reliability.json --visualize
python main.py --mode multi-seed --study standard --episodes 250 --num-seeds 250 --seed-start 8675309 --config-file configs/stress.json --visualize
```

---

## Output Structure

Experiment results are written under `results/`.

### Single-Seed Results

```text
results/
  single_seed/
    <timestamp>_<study>_<config>/
      undertrust_fixed.txt
      undertrust_adaptive.txt
      calibrated_fixed.txt
      calibrated_adaptive.txt
      overtrust_fixed.txt
      overtrust_adaptive.txt
      figures/
      tables/
```

### Multi-Seed Results

```text
results/
  multi_seed/
    <timestamp>_<study>_<config>/
      seed_level_results.csv
      aggregate_summary.csv
      paired_deltas.csv
      ablation_deltas.csv
      metadata.json
      figures/
      tables/
```

The `metadata.json` file records the run parameters, resolved simulation configuration, command used, Python version, platform, supervisor modes, autonomy modes, and batch directory.

---

## Main Output Files

| File | Description |
|---|---|
| `seed_level_results.csv` | One row per seed, supervisor mode, and autonomy mode |
| `aggregate_summary.csv` | Condition-level means, standard deviations, and confidence intervals |
| `paired_deltas.csv` | Paired adaptive-minus-fixed deltas by seed and supervisor |
| `ablation_deltas.csv` | Paired mode-minus-fixed deltas for ablation studies |
| `metadata.json` | Reproducibility metadata |

---

## Analysis Outputs

Aggregate visualization scripts produce:

- utility delta plots,
- acceptance delta plots,
- recommendation strength distributions,
- acceptance-utility trajectory plots,
- ablation utility comparisons,
- ablation acceptance comparisons,
- weak recommendation ablation comparisons,
- strong recommendation ablation comparisons.

Single-seed visualization scripts produce:

- acceptance-rate comparisons,
- recommendation-strength distributions,
- acceptance-utility trajectories,
- slopegraph/table summaries.

---

## Repository Organization

```text
.
├── analysis/
│   ├── generate_aggregate_visuals.py
│   └── generate_results_visuals.py
├── configs/
│   ├── baseline.json
│   ├── high_reliability.json
│   ├── high_workload.json
│   ├── moderate_uncertainty.json
│   ├── scarce_resources.json
│   └── stress.json
├── data/
│   ├── calibration/
│   │   ├── dataset_analysis.py
│   │   ├── dataset_analysis.txt
│   │   └── fema_distribution.py
│   └── raw/
│       └── us_disaster_declarations.csv
├── docs/
│   ├── api-reference/
│   ├── architecture/
│   ├── concepts/
│   ├── experiments/
│   └── user-guide/
├── results/
│   ├── multi_seed/
│   └── single_seed/
├── src/
│   ├── autonomy/
│   │   ├── adaptive_autonomy.py
│   │   └── confidence_estimator.py
│   ├── environment/
│   │   ├── generator.py
│   │   └── models.py
│   ├── planners/
│   │   ├── ai_planner.py
│   │   └── baseline_planner.py
│   ├── simulation/
│   │   ├── experiment_runner.py
│   │   └── outcome_simulator.py
│   ├── supervisor/
│   │   └── supervisor_policies.py
│   └── trust/
│       └── beta_trust_model.py
├── config.py
├── LICENSE
├── main.py
├── mkdocs.yml
├── README.md
├── requirements-docs.txt
└── requirements.txt
```

---

## Current Research Interpretation

Monte Carlo experiments suggest that behavior-aware adaptive autonomy reliably changes supervisor reliance behavior in the intended direction:

- undertrust conditions tend to receive stronger intervention,
- overtrust conditions tend to receive weaker intervention,
- calibrated conditions remain comparatively stable.

Utility effects are scenario-dependent. Overtrust correction often improves utility by reducing excessive AI reliance. Undertrust correction is more sensitive to AI reliability and task difficulty, since increasing reliance on an imperfect AI does not always improve outcomes.

The emerging research claim is:

> Adaptive autonomy can robustly regulate reliance behavior, but performance gains depend on AI reliability and scenario conditions.

---

## Limitations

The current system has several limitations:

1. Supervisor behavior is simulated rather than human-subject based.
2. Task priority is modeled rather than derived from FEMA data.
3. Task success probabilities are modeled using Beta distributions rather than learned from outcome labels.
4. The AI planner is heuristic and interpretable, not globally optimized.
5. Trust is modeled as a machine-side estimate of AI helpfulness, not as a full psychological model of human trust.
6. FEMA data grounds incident types and durations, but does not provide operational success labels.

These limitations are intentional for the current stage, which focuses on controlled simulation and mechanism evaluation.

---

## Future Work

Potential extensions include:

1. Sensitivity analysis across broader task-density and uncertainty regimes.
2. Human-subject validation of the supervisor policies.
3. Learned or optimized AI planning strategies.
4. Alternative trust update models based on executed outcomes.
5. Dynamic supervisor policies that evolve over time.
6. Expanded multimodal or geospatial disaster response data integration.
7. Statistical testing and effect-size reporting for publication.
8. Cross-configuration summary plots for sensitivity comparison.

---

## Reproducibility Notes

Each experiment batch should be interpreted alongside its `metadata.json` file. A complete report of simulation results should include:

- study mode,
- configuration file,
- resolved `SimulationConfig` values,
- number of seeds,
- seed start,
- episodes per seed,
- supervisor modes,
- autonomy modes,
- random seed range,
- generated output CSV files.

The JSON config files are experiment-specific overrides. The canonical configuration schema and default values are defined in `config.py`.

---

## Citation and Use

This repository is a research prototype. Results should be interpreted as simulation-based evidence rather than human-subject validation. Any publication using this code should report the configuration parameters, seed ranges, number of episodes, number of seeds, study mode, and supervisor policies used.
