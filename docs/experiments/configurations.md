# Scenario Configurations

The canonical schema and defaults live in `config.py`. JSON files under
`configs/` provide experiment-specific overrides.

## Default parameters

| Parameter | Default | Meaning |
|---|---:|---|
| `num_assets` | 3 | Response assets per episode |
| `num_incidents` | 8 | Incidents per episode |
| `num_time_slots` | 10 | Discrete planning horizon |
| `min_priority` | 5 | Minimum task utility |
| `max_priority` | 20 | Maximum task utility |
| `min_duration` | 1 | Minimum duration in slots |
| `max_duration` | 3 | Maximum duration in slots |
| `beta_alpha` | 5.0 | Success-probability Beta alpha |
| `beta_beta` | 2.0 | Success-probability Beta beta |
| `seed` | 42 | Default random seed |

## Included scenarios

| File | Purpose |
|---|---|
| `configs/baseline.json` | Default scenario |
| `configs/high_workload.json` | Increased task density |
| `configs/scarce_resources.json` | Reduced asset availability |
| `configs/moderate_uncertainty.json` | Lower task success probability |
| `configs/high_reliability.json` | Higher task success probability |
| `configs/stress.json` | High workload, scarcity, and uncertainty |

## Applying an override

```bash
python main.py \
  --mode multi-seed \
  --study standard \
  --episodes 250 \
  --num-seeds 250 \
  --seed-start 8675309 \
  --config-file configs/high_workload.json \
  --visualize
```

Only fields defined by `SimulationConfig` are valid overrides. The multi-seed
metadata records both the selected file and the resolved configuration.
