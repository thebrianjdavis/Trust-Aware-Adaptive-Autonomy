# Outputs and Visualizations

Experiment results are written under `results/` in timestamped batch
directories.

## Single-seed layout

```text
results/
└── single_seed/
    └── <timestamp>_<study>_<config>/
        ├── undertrust_fixed.txt
        ├── undertrust_adaptive.txt
        ├── calibrated_fixed.txt
        ├── calibrated_adaptive.txt
        ├── overtrust_fixed.txt
        ├── overtrust_adaptive.txt
        ├── figures/
        └── tables/
```

Ablation runs include the additional autonomy modes.

## Multi-seed layout

```text
results/
└── multi_seed/
    └── <timestamp>_<study>_<config>/
        ├── seed_level_results.csv
        ├── aggregate_summary.csv
        ├── paired_deltas.csv
        ├── ablation_deltas.csv
        ├── metadata.json
        ├── figures/
        └── tables/
```

## Main files

| File | Contents |
|---|---|
| `seed_level_results.csv` | One row per seed, supervisor, and autonomy mode |
| `aggregate_summary.csv` | Condition means, standard deviations, and confidence intervals |
| `paired_deltas.csv` | Adaptive-minus-fixed deltas paired by seed |
| `ablation_deltas.csv` | Mode-minus-fixed deltas for ablation studies |
| `metadata.json` | Run parameters, resolved config, command, platform, and batch details |

## Generated analysis

Aggregate visualization produces utility and acceptance delta plots,
recommendation-strength distributions, acceptance-utility trajectories, and
ablation comparisons. Single-seed visualization produces acceptance-rate
comparisons, recommendation distributions, trajectories, and slopegraph/table
summaries.

The analysis scripts can also be run directly:

```bash
python analysis/generate_aggregate_visuals.py --help
python analysis/generate_results_visuals.py --help
```

!!! tip

    Interpret every result alongside its `metadata.json`; a figure without its
    resolved configuration and seed range is not a complete reproducibility
    record.
