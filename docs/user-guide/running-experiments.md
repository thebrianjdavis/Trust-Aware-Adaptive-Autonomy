# Running Experiments

## Single-seed standard run

Use this mode for quick inspection and demonstrations:

```bash
python main.py \
  --mode single-seed \
  --study standard \
  --episodes 100 \
  --visualize
```

## Multi-seed standard run

Use multiple seeds for aggregate comparisons:

```bash
python main.py \
  --mode multi-seed \
  --study standard \
  --episodes 250 \
  --num-seeds 250 \
  --seed-start 8675309 \
  --config-file configs/baseline.json \
  --visualize
```

## Multi-seed ablation run

```bash
python main.py \
  --mode multi-seed \
  --study ablation \
  --episodes 250 \
  --num-seeds 250 \
  --seed-start 8675309 \
  --config-file configs/baseline.json \
  --visualize
```

## Sensitivity sweep

Repeat a fixed seed range across scenario files to isolate configuration
effects:

```bash
for scenario in high_workload scarce_resources moderate_uncertainty high_reliability stress
do
  python main.py \
    --mode multi-seed \
    --study standard \
    --episodes 250 \
    --num-seeds 250 \
    --seed-start 8675309 \
    --config-file "configs/${scenario}.json" \
    --visualize
done
```

## Reproducibility checklist

Report the following with a result:

- study and run mode;
- configuration file and resolved `SimulationConfig`;
- episode count and seed count;
- starting seed and full seed range;
- supervisor and autonomy modes;
- output batch directory and `metadata.json`.

Keeping the seed range constant across configurations supports paired
comparisons, although it does not remove the need for appropriate statistical
analysis.
