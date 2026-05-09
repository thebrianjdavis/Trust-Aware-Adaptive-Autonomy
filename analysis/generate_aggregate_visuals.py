## @file generate_aggregate_visuals.py
## @brief Generate aggregate Monte Carlo figures from multi-seed CSV results.

from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Dict, List, Tuple

import argparse
import matplotlib.pyplot as plt
import pandas as pd


## @brief Canonical supervisor ordering for plots and tables.
SUPERVISOR_ORDER: List[str] = ["undertrust", "calibrated", "overtrust"]

## @brief Human-readable supervisor labels.
SUPERVISOR_DISPLAY_LABELS: Dict[str, str] = {
    "undertrust": "Undertrust",
    "calibrated": "Calibrated",
    "overtrust": "Overtrust",
}

## @brief Fixed marker mapping for autonomy mode.
AUTONOMY_MARKERS: Dict[str, str] = {
    "fixed": "o",
    "adaptive": "s",
}

## @brief Fixed color mapping for supervisor mode.
SUPERVISOR_COLORS: Dict[str, str] = {
    "undertrust": "tab:blue",
    "calibrated": "tab:green",
    "overtrust": "tab:red",
}


## @brief Ensure output directories exist.
## @param figures_dir Figures output directory.
## @param tables_dir Tables output directory.
def ensure_output_directories(figures_dir: Path, tables_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)


## @brief Find the latest multi-seed batch directory.
## @param results_dir Base results directory.
## @return Path to latest multi-seed batch directory.
def find_latest_multi_seed_batch(results_dir: Path) -> Path:
    multi_seed_root = results_dir / "multi_seed"

    if not multi_seed_root.exists():
        raise ValueError("No multi_seed directory exists under results/.")

    batch_directories = sorted(
        batch_path for batch_path in multi_seed_root.iterdir() if batch_path.is_dir()
    )

    if not batch_directories:
        raise ValueError("No multi-seed batch directories were found.")

    latest_batch_directory = batch_directories[-1]
    return latest_batch_directory


## @brief Compute mean, standard deviation, and 95% CI for a numeric series.
## @param series Numeric pandas series.
## @return Tuple of mean, standard deviation, and 95% CI.
def compute_mean_std_ci(series: pd.Series) -> Tuple[float, float, float]:
    count = int(series.count())
    mean_value = float(series.mean())

    if count > 1:
        std_value = float(series.std(ddof=1))
        sem_value = std_value / sqrt(count)
        ci95_value = 1.96 * sem_value
    else:
        std_value = 0.0
        ci95_value = 0.0

    return mean_value, std_value, ci95_value


## @brief Build a presentation-friendly paired-delta summary table.
## @param delta_dataframe Paired adaptive-minus-fixed delta dataframe.
## @return Aggregate paired-delta summary dataframe.
def build_paired_delta_summary_table(delta_dataframe: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, float | str]] = []

    for supervisor_mode in SUPERVISOR_ORDER:
        supervisor_delta_df = delta_dataframe[
            delta_dataframe["supervisor_mode"] == supervisor_mode
        ]

        utility_mean, utility_std, utility_ci95 = compute_mean_std_ci(
            supervisor_delta_df["utility_delta"]
        )
        accept_mean, accept_std, accept_ci95 = compute_mean_std_ci(
            100.0 * supervisor_delta_df["accept_rate_delta"]
        )

        rows.append(
            {
                "Supervisor": SUPERVISOR_DISPLAY_LABELS[supervisor_mode],
                "utility_delta_mean": utility_mean,
                "utility_delta_std": utility_std,
                "utility_delta_ci95": utility_ci95,
                "accept_delta_pp_mean": accept_mean,
                "accept_delta_pp_std": accept_std,
                "accept_delta_pp_ci95": accept_ci95,
            }
        )

    summary_dataframe = pd.DataFrame(rows)
    return summary_dataframe


## @brief Plot mean adaptive-minus-fixed utility with 95% CI.
## @param delta_dataframe Paired adaptive-minus-fixed delta dataframe.
## @param output_path Output figure path.
def plot_utility_delta_with_ci(
    delta_dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    x_labels: List[str] = []
    mean_values: List[float] = []
    ci_values: List[float] = []
    bar_colors: List[str] = []

    for supervisor_mode in SUPERVISOR_ORDER:
        supervisor_delta_df = delta_dataframe[
            delta_dataframe["supervisor_mode"] == supervisor_mode
        ]
        mean_value, _, ci95_value = compute_mean_std_ci(
            supervisor_delta_df["utility_delta"]
        )

        x_labels.append(SUPERVISOR_DISPLAY_LABELS[supervisor_mode])
        mean_values.append(mean_value)
        ci_values.append(ci95_value)
        bar_colors.append(SUPERVISOR_COLORS[supervisor_mode])

    plt.figure(figsize=(9, 6))
    plt.bar(x_labels, mean_values, yerr=ci_values, capsize=6, color=bar_colors)
    plt.axhline(0.0, color="black", linewidth=1.0)
    plt.title("Adaptive − Fixed Utility Across Seeds")
    plt.xlabel("Supervisor Mode")
    plt.ylabel("Utility Difference")
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Plot mean adaptive-minus-fixed acceptance change with 95% CI.
## @param delta_dataframe Paired adaptive-minus-fixed delta dataframe.
## @param output_path Output figure path.
def plot_acceptance_delta_with_ci(
    delta_dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    x_labels: List[str] = []
    mean_values: List[float] = []
    ci_values: List[float] = []
    bar_colors: List[str] = []

    for supervisor_mode in SUPERVISOR_ORDER:
        supervisor_delta_df = delta_dataframe[
            delta_dataframe["supervisor_mode"] == supervisor_mode
        ]
        mean_value, _, ci95_value = compute_mean_std_ci(
            100.0 * supervisor_delta_df["accept_rate_delta"]
        )

        x_labels.append(SUPERVISOR_DISPLAY_LABELS[supervisor_mode])
        mean_values.append(mean_value)
        ci_values.append(ci95_value)
        bar_colors.append(SUPERVISOR_COLORS[supervisor_mode])

    plt.figure(figsize=(9, 6))
    plt.bar(x_labels, mean_values, yerr=ci_values, capsize=6, color=bar_colors)
    plt.axhline(0.0, color="black", linewidth=1.0)
    plt.title("Adaptive − Fixed Acceptance Change Across Seeds")
    plt.xlabel("Supervisor Mode")
    plt.ylabel("Acceptance Difference (percentage points)")
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Plot average recommendation strength distribution for adaptive runs.
## @param raw_dataframe Seed-level results dataframe.
## @param output_path Output figure path.
def plot_aggregate_recommendation_strength_distribution(
    raw_dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    adaptive_df = raw_dataframe[raw_dataframe["autonomy_mode"] == "adaptive"].copy()
    adaptive_df["supervisor_mode"] = pd.Categorical(
        adaptive_df["supervisor_mode"],
        categories=SUPERVISOR_ORDER,
        ordered=True,
    )
    adaptive_df = adaptive_df.sort_values("supervisor_mode")

    grouped_df = (
        adaptive_df.groupby("supervisor_mode", sort=False)[
            ["weak_rate", "normal_rate", "strong_rate"]
        ]
        .mean()
        .reset_index()
    )
    grouped_df["display_label"] = grouped_df["supervisor_mode"].map(
        SUPERVISOR_DISPLAY_LABELS
    )

    stacked_df = grouped_df.set_index("display_label")[
        ["weak_rate", "normal_rate", "strong_rate"]
    ]

    ax = stacked_df.plot(kind="bar", stacked=True, figsize=(10, 6))
    ax.set_title("Average Recommendation Strength Distribution (Adaptive Only)")
    ax.set_xlabel("Supervisor Mode")
    ax.set_ylabel("Mean Proportion Across Seeds")
    ax.legend(["Weak", "Normal", "Strong"])
    plt.xticks(rotation=0)
    plt.ylim(0, 1)
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Plot aggregate fixed-to-adaptive trajectories with error bars.
## @param raw_dataframe Seed-level results dataframe.
## @param output_path Output figure path.
def plot_aggregate_acceptance_utility_trajectory(
    raw_dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    ## Show the full acceptance range for interpretability.
    x_min = 0.0
    x_max = 1.0

    plt.figure(figsize=(10, 6))

    utility_lower_bounds: List[float] = []
    utility_upper_bounds: List[float] = []

    for supervisor_mode in SUPERVISOR_ORDER:
        supervisor_df = raw_dataframe[
            raw_dataframe["supervisor_mode"] == supervisor_mode
        ]

        fixed_df = supervisor_df[supervisor_df["autonomy_mode"] == "fixed"]
        adaptive_df = supervisor_df[supervisor_df["autonomy_mode"] == "adaptive"]

        fixed_accept_mean, _, fixed_accept_ci95 = compute_mean_std_ci(
            fixed_df["accept_rate"]
        )
        adaptive_accept_mean, _, adaptive_accept_ci95 = compute_mean_std_ci(
            adaptive_df["accept_rate"]
        )

        fixed_utility_mean, _, fixed_utility_ci95 = compute_mean_std_ci(
            fixed_df["mean_executed_utility"]
        )
        adaptive_utility_mean, _, adaptive_utility_ci95 = compute_mean_std_ci(
            adaptive_df["mean_executed_utility"]
        )

        utility_lower_bounds.append(fixed_utility_mean - fixed_utility_ci95)
        utility_lower_bounds.append(adaptive_utility_mean - adaptive_utility_ci95)
        utility_upper_bounds.append(fixed_utility_mean + fixed_utility_ci95)
        utility_upper_bounds.append(adaptive_utility_mean + adaptive_utility_ci95)

        color_value = SUPERVISOR_COLORS[supervisor_mode]

        plt.annotate(
            "",
            xy=(adaptive_accept_mean, adaptive_utility_mean),
            xytext=(fixed_accept_mean, fixed_utility_mean),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=2.5,
                color=color_value,
                shrinkA=6,
                shrinkB=6,
            ),
        )

        plt.errorbar(
            fixed_accept_mean,
            fixed_utility_mean,
            xerr=fixed_accept_ci95,
            yerr=fixed_utility_ci95,
            fmt="none",
            ecolor=color_value,
            elinewidth=1.5,
            capsize=4,
            zorder=2,
        )
        plt.errorbar(
            adaptive_accept_mean,
            adaptive_utility_mean,
            xerr=adaptive_accept_ci95,
            yerr=adaptive_utility_ci95,
            fmt="none",
            ecolor=color_value,
            elinewidth=1.5,
            capsize=4,
            zorder=2,
        )

        plt.scatter(
            fixed_accept_mean,
            fixed_utility_mean,
            s=180,
            color=color_value,
            marker=AUTONOMY_MARKERS["fixed"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )
        plt.scatter(
            adaptive_accept_mean,
            adaptive_utility_mean,
            s=180,
            color=color_value,
            marker=AUTONOMY_MARKERS["adaptive"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )

        label_offsets = {
            "undertrust": (0, 10),
            "calibrated": (0, 12),
            "overtrust": (0, 10),
        }
        midpoint_x = 0.5 * (fixed_accept_mean + adaptive_accept_mean)
        midpoint_y = 0.5 * (fixed_utility_mean + adaptive_utility_mean)
        offset_x, offset_y = label_offsets[supervisor_mode]

        plt.annotate(
            SUPERVISOR_DISPLAY_LABELS[supervisor_mode],
            (midpoint_x, midpoint_y),
            textcoords="offset points",
            xytext=(offset_x, offset_y),
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=color_value,
        )

    ## Build y-axis from what is actually plotted.
    y_min = min(utility_lower_bounds)
    y_max = max(utility_upper_bounds)

    y_padding = max(0.10, 0.15 * (y_max - y_min))
    y_min -= y_padding
    y_max += y_padding

    ## Keep a modest minimum span so the plot is readable but not exaggerated.
    minimum_span = 1.2
    current_span = y_max - y_min

    if current_span < minimum_span:
        center_value = 0.5 * (y_min + y_max)
        half_span = 0.5 * minimum_span
        y_min = center_value - half_span
        y_max = center_value + half_span

    fixed_handle = plt.Line2D(
        [0],
        [0],
        marker=AUTONOMY_MARKERS["fixed"],
        color="white",
        markerfacecolor="gray",
        markeredgecolor="black",
        markersize=10,
        linestyle="None",
        label="Fixed mean",
    )
    adaptive_handle = plt.Line2D(
        [0],
        [0],
        marker=AUTONOMY_MARKERS["adaptive"],
        color="white",
        markerfacecolor="gray",
        markeredgecolor="black",
        markersize=10,
        linestyle="None",
        label="Adaptive mean",
    )

    plt.title("Aggregate Supervisor Trajectories in Acceptance-Utility Space")
    plt.xlabel("Mean AI Acceptance Rate")
    plt.ylabel("Mean Executed Utility")
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend(handles=[fixed_handle, adaptive_handle], loc="best")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Build an aggregate summary table for ablation deltas.
## @param ablation_delta_dataframe Ablation delta dataframe.
## @return Summary dataframe grouped by supervisor and comparison mode.
def build_ablation_delta_summary_table(
    ablation_delta_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    metric_columns = [
        "mean_executed_utility_delta",
        "accept_rate_delta",
        "override_rate_delta",
        "weak_rate_delta",
        "normal_rate_delta",
        "strong_rate_delta",
        "mean_intervention_score_delta",
    ]

    comparison_mode_order = [
        "confidence_trust",
        "behavior_only",
        "adaptive",
    ]

    rows: List[Dict[str, float | str]] = []

    for supervisor_mode in SUPERVISOR_ORDER:
        for comparison_mode in comparison_mode_order:
            group_df = ablation_delta_dataframe[
                (ablation_delta_dataframe["supervisor_mode"] == supervisor_mode)
                & (ablation_delta_dataframe["comparison_mode"] == comparison_mode)
            ]

            if group_df.empty:
                continue

            row: Dict[str, float | str] = {
                "supervisor_mode": supervisor_mode,
                "comparison_mode": comparison_mode,
            }

            for metric_column in metric_columns:
                mean_value, std_value, ci95_value = compute_mean_std_ci(
                    group_df[metric_column]
                )
                row[f"{metric_column}_mean"] = mean_value
                row[f"{metric_column}_std"] = std_value
                row[f"{metric_column}_ci95"] = ci95_value

            rows.append(row)

    summary_dataframe = pd.DataFrame(rows)
    return summary_dataframe


## @brief Plot ablation delta metric grouped by supervisor and comparison mode.
## @param summary_dataframe Ablation summary dataframe.
## @param metric_mean_column Mean metric column name.
## @param metric_ci_column CI metric column name.
## @param title Plot title.
## @param y_label Y-axis label.
## @param output_path Output figure path.
def plot_ablation_delta_grouped_bars(
    summary_dataframe: pd.DataFrame,
    metric_mean_column: str,
    metric_ci_column: str,
    title: str,
    y_label: str,
    output_path: Path,
) -> None:
    comparison_modes = [
        "confidence_trust",
        "behavior_only",
        "adaptive",
    ]

    comparison_labels = {
        "confidence_trust": "Confidence + Trust",
        "behavior_only": "Behavior Only",
        "adaptive": "Full Adaptive",
    }

    x_positions = list(range(len(SUPERVISOR_ORDER)))
    bar_width = 0.22

    plt.figure(figsize=(11, 6))

    for mode_index, comparison_mode in enumerate(comparison_modes):
        mode_df = summary_dataframe[
            summary_dataframe["comparison_mode"] == comparison_mode
        ]

        mean_values: List[float] = []
        ci_values: List[float] = []

        for supervisor_mode in SUPERVISOR_ORDER:
            row = mode_df[mode_df["supervisor_mode"] == supervisor_mode].iloc[0]
            mean_values.append(float(row[metric_mean_column]))
            ci_values.append(float(row[metric_ci_column]))

        offset = (mode_index - 1) * bar_width
        shifted_positions = [
            position + offset for position in x_positions
        ]

        plt.bar(
            shifted_positions,
            mean_values,
            width=bar_width,
            yerr=ci_values,
            capsize=5,
            label=comparison_labels[comparison_mode],
        )

    plt.axhline(0.0, color="black", linewidth=1.0)
    plt.xticks(
        x_positions,
        [SUPERVISOR_DISPLAY_LABELS[mode] for mode in SUPERVISOR_ORDER],
    )
    plt.title(title)
    plt.xlabel("Supervisor Mode")
    plt.ylabel(y_label)
    plt.legend(title="Mode vs Fixed")
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Parse command-line arguments.
## @return Parsed argument namespace.
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate aggregate Monte Carlo figures.",
    )
    parser.add_argument(
        "--batch-dir",
        type=str,
        default="",
        help="Specific multi-seed batch directory to visualize. If omitted, latest batch is used.",
    )

    arguments = parser.parse_args()
    return arguments


## @brief Program entry point.
def main() -> None:
    arguments = parse_arguments()
    results_dir = Path("results")

    if arguments.batch_dir:
        batch_dir = Path(arguments.batch_dir)
    else:
        batch_dir = find_latest_multi_seed_batch(results_dir)

    raw_csv_path = batch_dir / "seed_level_results.csv"
    paired_delta_csv_path = batch_dir / "paired_deltas.csv"

    if not raw_csv_path.exists():
        raise ValueError(f"Missing seed-level results CSV: {raw_csv_path}")
    if not paired_delta_csv_path.exists():
        raise ValueError(f"Missing paired delta CSV: {paired_delta_csv_path}")

    raw_dataframe = pd.read_csv(raw_csv_path)
    delta_dataframe = pd.read_csv(paired_delta_csv_path)
    paired_delta_summary_df = build_paired_delta_summary_table(delta_dataframe)

    figures_dir = batch_dir / "figures"
    tables_dir = batch_dir / "tables"
    ensure_output_directories(figures_dir, tables_dir)

    paired_delta_summary_df.to_csv(
        tables_dir / "aggregate_paired_delta_summary.csv",
        index=False,
    )

    plot_utility_delta_with_ci(
        delta_dataframe=delta_dataframe,
        output_path=figures_dir / "aggregate_utility_delta_ci.png",
    )

    plot_acceptance_delta_with_ci(
        delta_dataframe=delta_dataframe,
        output_path=figures_dir / "aggregate_acceptance_delta_ci.png",
    )

    plot_aggregate_recommendation_strength_distribution(
        raw_dataframe=raw_dataframe,
        output_path=figures_dir / "aggregate_recommendation_strength_distribution.png",
    )

    plot_aggregate_acceptance_utility_trajectory(
        raw_dataframe=raw_dataframe,
        output_path=figures_dir / "aggregate_acceptance_utility_trajectory.png",
    )

    ablation_delta_csv_path = batch_dir / "ablation_deltas.csv"

    if ablation_delta_csv_path.exists():
        ablation_delta_dataframe = pd.read_csv(ablation_delta_csv_path)
        ablation_summary_df = build_ablation_delta_summary_table(
            ablation_delta_dataframe
        )

        ablation_summary_df.to_csv(
            tables_dir / "aggregate_ablation_delta_summary.csv",
            index=False,
        )

        plot_ablation_delta_grouped_bars(
            summary_dataframe=ablation_summary_df,
            metric_mean_column="mean_executed_utility_delta_mean",
            metric_ci_column="mean_executed_utility_delta_ci95",
            title="Ablation Utility Difference vs Fixed",
            y_label="Utility Difference",
            output_path=figures_dir / "ablation_utility_delta_grouped.png",
        )

        plot_ablation_delta_grouped_bars(
            summary_dataframe=ablation_summary_df,
            metric_mean_column="accept_rate_delta_mean",
            metric_ci_column="accept_rate_delta_ci95",
            title="Ablation Acceptance Difference vs Fixed",
            y_label="Acceptance Difference",
            output_path=figures_dir / "ablation_acceptance_delta_grouped.png",
        )

        plot_ablation_delta_grouped_bars(
            summary_dataframe=ablation_summary_df,
            metric_mean_column="weak_rate_delta_mean",
            metric_ci_column="weak_rate_delta_ci95",
            title="Ablation Weak Recommendation Difference vs Fixed",
            y_label="Weak Recommendation Difference",
            output_path=figures_dir / "ablation_weak_recommendation_delta_grouped.png",
        )

        plot_ablation_delta_grouped_bars(
            summary_dataframe=ablation_summary_df,
            metric_mean_column="strong_rate_delta_mean",
            metric_ci_column="strong_rate_delta_ci95",
            title="Ablation Strong Recommendation Difference vs Fixed",
            y_label="Strong Recommendation Difference",
            output_path=figures_dir / "ablation_strong_recommendation_delta_grouped.png",
        )

    print(f"Processed multi-seed batch: {batch_dir.name}")
    print(f"Saved aggregate tables to: {tables_dir}")
    print(f"Saved aggregate figures to: {figures_dir}")


if __name__ == "__main__":
    main()
