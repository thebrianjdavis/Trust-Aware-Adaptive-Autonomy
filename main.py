## @file main.py
## @brief Entry point for single-run and multi-seed HMT experiments.

import argparse
import os
from contextlib import redirect_stdout
from dataclasses import replace
from datetime import datetime
from math import sqrt
from pathlib import Path
from typing import Dict, List

import pandas as pd

from config import SimulationConfig
from data.calibration.fema_distribution import load_fema_calibration_data
from src.simulation.experiment_runner import ExperimentRunSummary, run_trust_experiment


## @brief Create results directory if it does not already exist.
## @param directory_path Path to results directory.
def ensure_results_directory(directory_path: str) -> None:
    os.makedirs(directory_path, exist_ok=True)


## @brief Generate a timestamp string for the current run.
## @return Timestamp string formatted as YYYYMMDDHHMMSS.
def generate_run_timestamp() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return timestamp


## @brief Return the canonical supervisor modes.
## @return Ordered list of supervisor modes.
def get_supervisor_modes() -> List[str]:
    supervisor_modes = [
        "undertrust",
        "calibrated",
        "overtrust",
    ]
    return supervisor_modes


## @brief Return the canonical autonomy modes.
## @return Ordered list of autonomy modes.
def get_autonomy_modes() -> List[str]:
    autonomy_modes = [
        "fixed",
        "adaptive",
    ]
    return autonomy_modes


## @brief Load FEMA calibration data once for reuse across all experiment calls.
## @return Loaded FEMA calibration data.
def load_shared_calibration_data():
    csv_path = Path("data/raw/us_disaster_declarations.csv")
    calibration_data = load_fema_calibration_data(csv_path)
    return calibration_data


## @brief Generate a results file path for a supervisor and autonomy mode.
## @param directory_path Results directory.
## @param supervisor_mode Supervisor mode name.
## @param autonomy_mode Autonomy mode name.
## @return Full path to results file.
def generate_results_filepath(
    directory_path: str,
    supervisor_mode: str,
    autonomy_mode: str,
) -> str:
    filename = f"{supervisor_mode}_{autonomy_mode}.txt"
    filepath = os.path.join(directory_path, filename)
    return filepath


## @brief Run one single-seed experiment configuration and write results to file.
## @param config Simulation configuration values.
## @param calibration_data Preloaded FEMA calibration data.
## @param num_episodes Number of episodes to run.
## @param results_directory Output results directory.
## @param supervisor_mode Supervisor mode name.
## @param autonomy_mode Autonomy mode name.
def run_and_log_experiment(
    config: SimulationConfig,
    calibration_data,
    num_episodes: int,
    results_directory: str,
    supervisor_mode: str,
    autonomy_mode: str,
) -> None:
    results_filepath = generate_results_filepath(
        directory_path=results_directory,
        supervisor_mode=supervisor_mode,
        autonomy_mode=autonomy_mode,
    )

    with open(results_filepath, "w") as results_file:
        with redirect_stdout(results_file):
            print("=== TRUST-AWARE ADAPTIVE AUTONOMY EXPERIMENT ===")
            print(f"Timestamp: {datetime.now()}")
            print(f"Episodes: {num_episodes}")
            print(f"Supervisor mode: {supervisor_mode}")
            print(f"Autonomy mode: {autonomy_mode}\n")

            run_trust_experiment(
                config=config,
                calibration_data=calibration_data,
                num_episodes=num_episodes,
                supervisor_mode=supervisor_mode,
                autonomy_mode=autonomy_mode,
                verbose=True,
            )

    print(f"Results written to: {results_filepath}")


## @brief Compute mean, standard deviation, and 95% CI for a numeric series.
## @param series Numeric pandas series.
## @return Dictionary with count, mean, std, sem, and ci95.
def compute_mean_std_ci(series: pd.Series) -> Dict[str, float]:
    count = int(series.count())
    mean_value = float(series.mean())

    if count > 1:
        std_value = float(series.std(ddof=1))
        sem_value = std_value / sqrt(count)
        ci95_value = 1.96 * sem_value
    else:
        std_value = 0.0
        sem_value = 0.0
        ci95_value = 0.0

    statistics = {
        "count": count,
        "mean": mean_value,
        "std": std_value,
        "sem": sem_value,
        "ci95": ci95_value,
    }
    return statistics


## @brief Convert one experiment summary into a seed-level CSV row.
## @param run_timestamp Shared timestamp for the batch.
## @param seed Seed used for the run.
## @param summary Experiment summary object.
## @return Dictionary representing one CSV row.
def build_seed_level_row(
    run_timestamp: str,
    seed: int,
    summary: ExperimentRunSummary,
) -> Dict[str, float | int | str]:
    total_decisions = summary.ai_accepted + summary.ai_overridden
    accept_rate = summary.ai_accepted / total_decisions
    override_rate = summary.ai_overridden / total_decisions

    total_recommendations = (
        summary.weak_recommendations
        + summary.normal_recommendations
        + summary.strong_recommendations
    )
    weak_rate = summary.weak_recommendations / total_recommendations
    normal_rate = summary.normal_recommendations / total_recommendations
    strong_rate = summary.strong_recommendations / total_recommendations

    row = {
        "run_timestamp": run_timestamp,
        "seed": seed,
        "num_episodes": summary.num_episodes,
        "supervisor_mode": summary.supervisor_mode,
        "autonomy_mode": summary.autonomy_mode,
        "condition_label": f"{summary.supervisor_mode}_{summary.autonomy_mode}",
        "ai_wins": summary.ai_wins,
        "baseline_wins": summary.baseline_wins,
        "ties": summary.ties,
        "ai_accepted": summary.ai_accepted,
        "ai_overridden": summary.ai_overridden,
        "weak_recommendations": summary.weak_recommendations,
        "normal_recommendations": summary.normal_recommendations,
        "strong_recommendations": summary.strong_recommendations,
        "accept_rate": accept_rate,
        "override_rate": override_rate,
        "weak_rate": weak_rate,
        "normal_rate": normal_rate,
        "strong_rate": strong_rate,
        "mean_executed_utility": summary.mean_executed_utility,
        "mean_ai_confidence": summary.mean_ai_confidence,
        "mean_override_rate": summary.mean_override_rate,
        "mean_intervention_score": summary.mean_intervention_score,
        "final_trust": summary.final_trust,
        "trust_variance": summary.trust_variance,
    }

    return row


## @brief Build a condition-level aggregate summary table across many seeds.
## @param raw_dataframe Seed-level results dataframe.
## @return Aggregate summary dataframe.
def build_multi_seed_summary_table(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    metrics_to_summarize = [
        "mean_executed_utility",
        "accept_rate",
        "override_rate",
        "weak_rate",
        "normal_rate",
        "strong_rate",
        "mean_ai_confidence",
        "mean_override_rate",
        "mean_intervention_score",
        "final_trust",
        "trust_variance",
    ]

    rows: List[Dict[str, float | int | str]] = []

    grouped = raw_dataframe.groupby(["supervisor_mode", "autonomy_mode"], sort=False)

    for (supervisor_mode, autonomy_mode), group_df in grouped:
        row: Dict[str, float | int | str] = {
            "supervisor_mode": supervisor_mode,
            "autonomy_mode": autonomy_mode,
            "condition_label": f"{supervisor_mode}_{autonomy_mode}",
            "num_seeds": int(group_df["seed"].nunique()),
        }

        for metric_name in metrics_to_summarize:
            statistics = compute_mean_std_ci(group_df[metric_name])
            row[f"{metric_name}_mean"] = statistics["mean"]
            row[f"{metric_name}_std"] = statistics["std"]
            row[f"{metric_name}_ci95"] = statistics["ci95"]

        rows.append(row)

    aggregate_dataframe = pd.DataFrame(rows)
    return aggregate_dataframe


## @brief Build paired adaptive-minus-fixed delta rows by seed and supervisor.
## @param raw_dataframe Seed-level results dataframe.
## @return Paired delta dataframe.
def build_paired_delta_table(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    pivot_df = raw_dataframe.pivot(
        index=["seed", "supervisor_mode"],
        columns="autonomy_mode",
        values=[
            "mean_executed_utility",
            "accept_rate",
            "override_rate",
            "weak_rate",
            "normal_rate",
            "strong_rate",
            "mean_intervention_score",
        ],
    )

    rows: List[Dict[str, float | int | str]] = []

    for (seed, supervisor_mode), pivot_row in pivot_df.iterrows():
        row = {
            "seed": int(seed),
            "supervisor_mode": supervisor_mode,
            "utility_delta": (
                pivot_row[("mean_executed_utility", "adaptive")]
                - pivot_row[("mean_executed_utility", "fixed")]
            ),
            "accept_rate_delta": (
                pivot_row[("accept_rate", "adaptive")]
                - pivot_row[("accept_rate", "fixed")]
            ),
            "override_rate_delta": (
                pivot_row[("override_rate", "adaptive")]
                - pivot_row[("override_rate", "fixed")]
            ),
            "weak_rate_delta": (
                pivot_row[("weak_rate", "adaptive")]
                - pivot_row[("weak_rate", "fixed")]
            ),
            "normal_rate_delta": (
                pivot_row[("normal_rate", "adaptive")]
                - pivot_row[("normal_rate", "fixed")]
            ),
            "strong_rate_delta": (
                pivot_row[("strong_rate", "adaptive")]
                - pivot_row[("strong_rate", "fixed")]
            ),
            "intervention_score_delta": (
                pivot_row[("mean_intervention_score", "adaptive")]
                - pivot_row[("mean_intervention_score", "fixed")]
            ),
        }
        rows.append(row)

    delta_dataframe = pd.DataFrame(rows)
    return delta_dataframe


## @brief Run the original six-condition single-seed batch.
## @param config Simulation configuration values.
## @param calibration_data Preloaded FEMA calibration data.
## @param num_episodes Number of episodes to run.
## @param results_directory Output results directory.
## @param run_timestamp Shared timestamp for the full run.
def run_single_batch(
    config: SimulationConfig,
    calibration_data,
    num_episodes: int,
    results_directory: str,
    run_timestamp: str,
) -> None:
    batch_directory = os.path.join(results_directory, "single_seed", run_timestamp)
    ensure_results_directory(batch_directory)

    for supervisor_mode in get_supervisor_modes():
        for autonomy_mode in get_autonomy_modes():
            run_and_log_experiment(
                config=config,
                calibration_data=calibration_data,
                num_episodes=num_episodes,
                results_directory=batch_directory,
                supervisor_mode=supervisor_mode,
                autonomy_mode=autonomy_mode,
            )


## @brief Run a paired multi-seed batch and save aggregate CSV outputs.
## @param config Base simulation configuration values.
## @param calibration_data Preloaded FEMA calibration data.
## @param num_episodes Number of episodes per seed-condition run.
## @param results_directory Output results directory.
## @param run_timestamp Shared timestamp for the full run.
## @param num_seeds Number of seeds to evaluate.
## @param seed_start First seed in the sequence.
def run_multi_seed_batch(
    config: SimulationConfig,
    calibration_data,
    num_episodes: int,
    results_directory: str,
    run_timestamp: str,
    num_seeds: int,
    seed_start: int,
) -> None:
    batch_directory = os.path.join(results_directory, "multi_seed", run_timestamp)
    ensure_results_directory(batch_directory)

    seed_rows: List[Dict[str, float | int | str]] = []

    for seed in range(seed_start, seed_start + num_seeds):
        seed_config = replace(config, seed=seed)
        print(f"Running paired multi-seed batch for seed {seed}...")

        for supervisor_mode in get_supervisor_modes():
            for autonomy_mode in get_autonomy_modes():
                summary = run_trust_experiment(
                    config=seed_config,
                    calibration_data=calibration_data,
                    num_episodes=num_episodes,
                    supervisor_mode=supervisor_mode,
                    autonomy_mode=autonomy_mode,
                    verbose=False,
                )

                seed_rows.append(
                    build_seed_level_row(
                        run_timestamp=run_timestamp,
                        seed=seed,
                        summary=summary,
                    )
                )

    raw_dataframe = pd.DataFrame(seed_rows)
    aggregate_dataframe = build_multi_seed_summary_table(raw_dataframe)
    delta_dataframe = build_paired_delta_table(raw_dataframe)

    raw_csv_path = os.path.join(batch_directory, "seed_level_results.csv")
    aggregate_csv_path = os.path.join(batch_directory, "aggregate_summary.csv")
    delta_csv_path = os.path.join(batch_directory, "paired_deltas.csv")

    raw_dataframe.to_csv(raw_csv_path, index=False)
    aggregate_dataframe.to_csv(aggregate_csv_path, index=False)
    delta_dataframe.to_csv(delta_csv_path, index=False)

    print(f"Seed-level results written to: {raw_csv_path}")
    print(f"Aggregate summary written to: {aggregate_csv_path}")
    print(f"Paired deltas written to: {delta_csv_path}")


## @brief Parse command-line arguments.
## @return Parsed argument namespace.
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run single-seed or multi-seed HMT experiments.",
    )
    parser.add_argument(
        "--mode",
        choices=["single-seed", "multi-seed"],
        default="single-seed",
        help="Execution mode. 'single-seed' preserves the current six-text-file workflow.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=100,
        help="Number of episodes per experiment run.",
    )
    parser.add_argument(
        "--num-seeds",
        type=int,
        default=30,
        help="Number of seeds to run in multi-seed mode.",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=1,
        help="Starting seed value for multi-seed mode.",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Base results directory.",
    )

    arguments = parser.parse_args()
    return arguments


## @brief Program entry point.
def main() -> None:
    arguments = parse_arguments()
    config = SimulationConfig()
    run_timestamp = generate_run_timestamp()

    ensure_results_directory(arguments.results_dir)
    calibration_data = load_shared_calibration_data()

    if arguments.mode == "single-seed":
        run_single_batch(
            config=config,
            calibration_data=calibration_data,
            num_episodes=arguments.episodes,
            results_directory=arguments.results_dir,
            run_timestamp=run_timestamp,
        )
    else:
        run_multi_seed_batch(
            config=config,
            calibration_data=calibration_data,
            num_episodes=arguments.episodes,
            results_directory=arguments.results_dir,
            run_timestamp=run_timestamp,
            num_seeds=arguments.num_seeds,
            seed_start=arguments.seed_start,
        )


if __name__ == "__main__":
    main()
    
