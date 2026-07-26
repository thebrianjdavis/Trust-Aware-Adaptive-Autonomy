# Getting Started

## Requirements

- Python 3.10 or newer;
- `pip`;
- Git, if cloning the repository.

## Install

=== "macOS / Linux"

    ```bash
    git clone https://github.com/thebrianjdavis/Trust-Aware-Adaptive-Autonomy.git
    cd Trust-Aware-Adaptive-Autonomy
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    ```

=== "Windows PowerShell"

    ```powershell
    git clone https://github.com/thebrianjdavis/Trust-Aware-Adaptive-Autonomy.git
    Set-Location Trust-Aware-Adaptive-Autonomy
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    ```

## Run a small experiment

```bash
python main.py --mode single-seed --study standard --episodes 10
```

The command evaluates fixed and adaptive autonomy with all three supervisor
policies. Text summaries are written beneath `results/single_seed/`.

## Generate figures

Add `--visualize` to generate plots and presentation tables:

```bash
python main.py --mode single-seed --study standard --episodes 100 --visualize
```

## Confirm command options

```bash
python main.py --help
```

Next, use the [experiment command guide](running-experiments.md) to select a
study, seed count, and scenario.
