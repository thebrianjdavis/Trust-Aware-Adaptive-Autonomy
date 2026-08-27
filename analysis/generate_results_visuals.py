"""Generate polished figures and tables from single-seed experiment results."""

## @file generate_results_visuals.py
## @brief Generate polished figures and summary tables from experiment result files.

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

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

## @brief Canonical condition ordering for plots and tables.
CONDITION_ORDER: List[str] = [
    "undertrust_fixed",
    "undertrust_adaptive",
    "calibrated_fixed",
    "calibrated_adaptive",
    "overtrust_fixed",
    "overtrust_adaptive",
]

## @brief Human-readable condition labels.
CONDITION_DISPLAY_LABELS: Dict[str, str] = {
    "undertrust_fixed": "Undertrust\nFixed",
    "undertrust_adaptive": "Undertrust\nAdaptive",
    "calibrated_fixed": "Calibrated\nFixed",
    "calibrated_adaptive": "Calibrated\nAdaptive",
    "overtrust_fixed": "Overtrust\nFixed",
    "overtrust_adaptive": "Overtrust\nAdaptive",
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


## @brief Stores parsed summary information for one experiment run.
@dataclass
class ExperimentSummary:
    """Store parsed summary metrics for one experiment condition."""

    ## @brief Supervisor policy mode.
    supervisor_mode: str

    ## @brief Autonomy mode.
    autonomy_mode: str

    ## @brief Number of AI wins.
    ai_wins: int

    ## @brief Number of baseline wins.
    baseline_wins: int

    ## @brief Number of ties.
    ties: int

    ## @brief Number of times the AI plan was accepted.
    ai_accepted: int

    ## @brief Number of times the AI plan was overridden.
    ai_overridden: int

    ## @brief Number of weak recommendations.
    weak_recommendations: int

    ## @brief Number of normal recommendations.
    normal_recommendations: int

    ## @brief Number of strong recommendations.
    strong_recommendations: int

    ## @brief Mean executed utility.
    mean_executed_utility: float

    ## @brief Mean AI confidence.
    mean_ai_confidence: float

    ## @brief Mean intervention score.
    mean_intervention_score: float

    ## @brief Final trust value.
    final_trust: float

    ## @brief Trust variance.
    trust_variance: float

    ## @brief Trust history over episodes.
    trust_history: List[float]

    ## @brief Source filename.
    filename: str


## @brief Parse a single experiment results file.
## @param filepath Path to the results text file.
## @return Parsed experiment summary.
def parse_results_file(filepath: Path) -> ExperimentSummary:
    """Parse a text results file into a structured experiment summary."""
    text = filepath.read_text()

    def extract_string(label: str) -> str:
        """Extract a labeled string value from the results text."""
        match = re.search(rf"{re.escape(label)}:\s*(.+)", text)
        if match is None:
            raise ValueError(f"Could not find label '{label}' in {filepath}")
        return match.group(1).strip()

    def extract_int(label: str) -> int:
        """Extract a labeled integer value from the results text."""
        return int(extract_string(label))

    def extract_float(label: str) -> float:
        """Extract a labeled floating-point value from the results text."""
        return float(extract_string(label))

    def extract_list(label: str) -> List[float]:
        """Extract a labeled list of floating-point values from the results text."""
        raw_value = extract_string(label)
        parsed_value = ast.literal_eval(raw_value)
        return [float(item) for item in parsed_value]

    return ExperimentSummary(
        supervisor_mode=extract_string("Supervisor mode"),
        autonomy_mode=extract_string("Autonomy mode"),
        ai_wins=extract_int("AI wins"),
        baseline_wins=extract_int("Baseline wins"),
        ties=extract_int("Ties"),
        ai_accepted=extract_int("AI accepted"),
        ai_overridden=extract_int("AI overridden"),
        weak_recommendations=extract_int("Weak recommendations"),
        normal_recommendations=extract_int("Normal recommendations"),
        strong_recommendations=extract_int("Strong recommendations"),
        mean_executed_utility=extract_float("Mean executed utility"),
        mean_ai_confidence=extract_float("Mean AI confidence"),
        mean_intervention_score=extract_float("Mean intervention score"),
        final_trust=extract_float("Final trust"),
        trust_variance=extract_float("Trust variance"),
        trust_history=extract_list("Trust history"),
        filename=filepath.name,
    )


## @brief Convert experiment summaries into a dataframe.
## @param summaries Parsed experiment summaries.
## @return Dataframe of summary values.
def build_summary_dataframe(summaries: List[ExperimentSummary]) -> pd.DataFrame:
    """Convert parsed experiment summaries into a tabular dataset."""
    rows: List[Dict[str, object]] = []

    for summary in summaries:
        rows.append(
            {
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
                "mean_executed_utility": summary.mean_executed_utility,
                "mean_ai_confidence": summary.mean_ai_confidence,
                "mean_intervention_score": summary.mean_intervention_score,
                "final_trust": summary.final_trust,
                "trust_variance": summary.trust_variance,
                "filename": summary.filename,
            }
        )

    return pd.DataFrame(rows)


## @brief Add derived acceptance, override, and recommendation-rate columns.
## @param dataframe Raw summary dataframe.
## @return Dataframe with added derived columns.
def add_rate_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add acceptance, override, and recommendation proportion columns."""
    enriched_df = dataframe.copy()

    total_decisions = enriched_df["ai_accepted"] + enriched_df["ai_overridden"]
    enriched_df["accept_rate"] = enriched_df["ai_accepted"] / total_decisions
    enriched_df["override_rate"] = enriched_df["ai_overridden"] / total_decisions

    total_recommendations = (
        enriched_df["weak_recommendations"]
        + enriched_df["normal_recommendations"]
        + enriched_df["strong_recommendations"]
    )
    enriched_df["weak_rate"] = enriched_df["weak_recommendations"] / total_recommendations
    enriched_df["normal_rate"] = enriched_df["normal_recommendations"] / total_recommendations
    enriched_df["strong_rate"] = enriched_df["strong_recommendations"] / total_recommendations

    return enriched_df


## @brief Build a compact presentation-friendly summary table.
## @param dataframe Summary dataframe with rate columns.
## @return Compact summary dataframe for reporting and slides.
def build_presentation_summary_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Build a compact fixed-versus-adaptive presentation table."""
    utility_pivot_df = (
        dataframe.pivot(
            index="supervisor_mode",
            columns="autonomy_mode",
            values="mean_executed_utility",
        )
        .reindex(SUPERVISOR_ORDER)
        .reset_index()
    )
    utility_pivot_df = utility_pivot_df.rename(
        columns={
            "fixed": "fixed_utility",
            "adaptive": "adaptive_utility",
        }
    )
    utility_pivot_df["delta_utility"] = (
        utility_pivot_df["adaptive_utility"] - utility_pivot_df["fixed_utility"]
    )

    accept_pivot_df = (
        dataframe.pivot(
            index="supervisor_mode",
            columns="autonomy_mode",
            values="accept_rate",
        )
        .reindex(SUPERVISOR_ORDER)
        .reset_index()
    )
    accept_pivot_df = accept_pivot_df.rename(
        columns={
            "fixed": "fixed_accept_rate",
            "adaptive": "adaptive_accept_rate",
        }
    )
    accept_pivot_df["delta_accept_pp"] = 100.0 * (
        accept_pivot_df["adaptive_accept_rate"] - accept_pivot_df["fixed_accept_rate"]
    )

    presentation_df = utility_pivot_df.merge(accept_pivot_df, on="supervisor_mode")

    presentation_df["fixed_accept_rate_pct"] = (
        100.0 * presentation_df["fixed_accept_rate"]
    )
    presentation_df["adaptive_accept_rate_pct"] = (
        100.0 * presentation_df["adaptive_accept_rate"]
    )

    return presentation_df


## @brief Save a dataframe as CSV.
## @param dataframe Dataframe to save.
## @param output_path Output CSV path.
def save_table(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Write a dataframe to a header-bearing CSV file."""
    dataframe.to_csv(output_path, index=False)


## @brief Compute a consistent utility-axis range that avoids exaggerating tiny differences.
## @param dataframe Summary dataframe with rate columns.
## @return Tuple of y-axis minimum and maximum.
def get_utility_axis_limits(dataframe: pd.DataFrame) -> tuple[float, float]:
    """Choose readable utility-axis limits without exaggerating small changes."""
    utility_min = float(dataframe["mean_executed_utility"].min())
    utility_max = float(dataframe["mean_executed_utility"].max())

    center_value = 0.5 * (utility_min + utility_max)
    half_range = max(0.6, 0.5 * (utility_max - utility_min) + 0.12)

    y_min = center_value - half_range
    y_max = center_value + half_range

    return y_min, y_max


## @brief Plot AI acceptance vs override rates as 100% stacked bars.
## @param dataframe Summary dataframe with rate columns.
## @param output_path Output figure path.
def plot_acceptance_rate_comparison(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot acceptance and override proportions as stacked bars."""
    plot_df = dataframe.copy()
    plot_df["condition_label"] = pd.Categorical(
        plot_df["condition_label"],
        categories=CONDITION_ORDER,
        ordered=True,
    )
    plot_df = plot_df.sort_values("condition_label")
    plot_df["display_label"] = plot_df["condition_label"].map(CONDITION_DISPLAY_LABELS)

    stacked_df = plot_df.set_index("display_label")[["accept_rate", "override_rate"]]

    ax = stacked_df.plot(kind="bar", stacked=True, figsize=(12, 6))
    ax.set_title("AI Acceptance vs Override Rate")
    ax.set_xlabel("Experiment Condition")
    ax.set_ylabel("Proportion")
    ax.legend(["Accepted", "Overridden"])
    plt.xticks(rotation=0)
    plt.ylim(0, 1)
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Plot recommendation strength distribution for adaptive conditions only.
## @param dataframe Summary dataframe with rate columns.
## @param output_path Output figure path.
def plot_recommendation_strength_distribution(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot recommendation-strength proportions for adaptive conditions."""
    adaptive_df = dataframe[dataframe["autonomy_mode"] == "adaptive"].copy()
    adaptive_df["supervisor_mode"] = pd.Categorical(
        adaptive_df["supervisor_mode"],
        categories=SUPERVISOR_ORDER,
        ordered=True,
    )
    adaptive_df = adaptive_df.sort_values("supervisor_mode")
    adaptive_df["display_label"] = adaptive_df["supervisor_mode"].map(
        SUPERVISOR_DISPLAY_LABELS
    )

    stacked_df = adaptive_df.set_index("display_label")[
        ["weak_rate", "normal_rate", "strong_rate"]
    ]

    ax = stacked_df.plot(kind="bar", stacked=True, figsize=(10, 6))
    ax.set_title("Recommendation Strength Distribution (Adaptive Only)")
    ax.set_xlabel("Supervisor Mode")
    ax.set_ylabel("Proportion")
    ax.legend(["Weak", "Normal", "Strong"])
    plt.xticks(rotation=0)
    plt.ylim(0, 1)
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Plot fixed-to-adaptive trajectories in acceptance-utility space.
## @param dataframe Summary dataframe with rate columns.
## @param output_path Output figure path.
def plot_acceptance_utility_trajectory(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot fixed-to-adaptive trajectories in acceptance-utility space."""
    y_min, y_max = get_utility_axis_limits(dataframe)
    x_min = max(0.0, float(dataframe["accept_rate"].min()) - 0.05)
    x_max = min(1.0, float(dataframe["accept_rate"].max()) + 0.05)

    pivot_df = (
        dataframe.pivot(index="supervisor_mode", columns="autonomy_mode")
        .reindex(SUPERVISOR_ORDER)
    )

    plt.figure(figsize=(10, 6))

    for supervisor_mode in SUPERVISOR_ORDER:
        color_value = SUPERVISOR_COLORS[supervisor_mode]

        fixed_accept_rate = pivot_df.loc[supervisor_mode, ("accept_rate", "fixed")]
        adaptive_accept_rate = pivot_df.loc[supervisor_mode, ("accept_rate", "adaptive")]
        fixed_utility = pivot_df.loc[supervisor_mode, ("mean_executed_utility", "fixed")]
        adaptive_utility = pivot_df.loc[supervisor_mode, ("mean_executed_utility", "adaptive")]

        plt.annotate(
            "",
            xy=(adaptive_accept_rate, adaptive_utility),
            xytext=(fixed_accept_rate, fixed_utility),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=2.5,
                color=color_value,
                shrinkA=6,
                shrinkB=6,
            ),
        )

        plt.scatter(
            fixed_accept_rate,
            fixed_utility,
            s=180,
            color=color_value,
            marker=AUTONOMY_MARKERS["fixed"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )
        plt.scatter(
            adaptive_accept_rate,
            adaptive_utility,
            s=180,
            color=color_value,
            marker=AUTONOMY_MARKERS["adaptive"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )

        midpoint_x = 0.5 * (fixed_accept_rate + adaptive_accept_rate)
        midpoint_y = 0.5 * (fixed_utility + adaptive_utility)

        plt.annotate(
            SUPERVISOR_DISPLAY_LABELS[supervisor_mode],
            (midpoint_x, midpoint_y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=color_value,
        )

    fixed_handle = plt.Line2D(
        [0],
        [0],
        marker=AUTONOMY_MARKERS["fixed"],
        color="white",
        markerfacecolor="gray",
        markeredgecolor="black",
        markersize=10,
        linestyle="None",
        label="Fixed",
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
        label="Adaptive",
    )

    plt.title("Supervisor Trajectories in Acceptance-Utility Space")
    plt.xlabel("AI Acceptance Rate")
    plt.ylabel("Mean Executed Utility")
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend(handles=[fixed_handle, adaptive_handle], loc="best")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Create a slopegraph/table combo figure for presentation.
## @param presentation_table Compact presentation summary table.
## @param output_path Output figure path.
def plot_slopegraph_table_combo(
    presentation_table: pd.DataFrame,
    output_path: Path,
) -> None:
    """Create a presentation figure combining a utility slopegraph and table."""
    utility_values = list(presentation_table["fixed_utility"]) + list(
        presentation_table["adaptive_utility"]
    )
    utility_min = min(utility_values)
    utility_max = max(utility_values)
    center_value = 0.5 * (utility_min + utility_max)
    half_range = max(0.6, 0.5 * (utility_max - utility_min) + 0.12)

    figure, (axis_left, axis_right) = plt.subplots(
        1,
        2,
        figsize=(14, 6),
        gridspec_kw={"width_ratios": [1.25, 1.0]},
    )

    for supervisor_mode in SUPERVISOR_ORDER:
        row = presentation_table[
            presentation_table["supervisor_mode"] == supervisor_mode
        ].iloc[0]

        fixed_value = row["fixed_utility"]
        adaptive_value = row["adaptive_utility"]
        delta_value = row["delta_utility"]
        line_color = SUPERVISOR_COLORS[supervisor_mode]

        axis_left.plot(
            [0, 1],
            [fixed_value, adaptive_value],
            color=line_color,
            linewidth=2.5,
        )
        axis_left.scatter(
            0,
            fixed_value,
            s=150,
            color=line_color,
            marker=AUTONOMY_MARKERS["fixed"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )
        axis_left.scatter(
            1,
            adaptive_value,
            s=150,
            color=line_color,
            marker=AUTONOMY_MARKERS["adaptive"],
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )

        axis_left.text(
            0.50,
            0.5 * (fixed_value + adaptive_value),
            SUPERVISOR_DISPLAY_LABELS[supervisor_mode],
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=line_color,
        )
        axis_left.text(
            1.08,
            adaptive_value,
            f"ΔU={delta_value:+.2f}",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    axis_left.set_xticks([0, 1])
    axis_left.set_xticklabels(["Fixed", "Adaptive"])
    axis_left.set_title("Utility Shift by Supervisor")
    axis_left.set_ylabel("Mean Executed Utility")
    axis_left.set_ylim(center_value - half_range, center_value + half_range)
    axis_left.grid(axis="y", linestyle="--", alpha=0.3)

    fixed_handle = plt.Line2D(
        [0],
        [0],
        marker=AUTONOMY_MARKERS["fixed"],
        color="white",
        markerfacecolor="gray",
        markeredgecolor="black",
        markersize=10,
        linestyle="None",
        label="Fixed",
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
        label="Adaptive",
    )
    axis_left.legend(handles=[fixed_handle, adaptive_handle], loc="best")

    axis_right.axis("off")

    display_df = presentation_table.copy()
    display_df["Supervisor"] = display_df["supervisor_mode"].map(SUPERVISOR_DISPLAY_LABELS)
    display_df["Fixed Accept"] = display_df["fixed_accept_rate_pct"].map(
        lambda value: f"{value:.0f}%"
    )
    display_df["Adaptive Accept"] = display_df["adaptive_accept_rate_pct"].map(
        lambda value: f"{value:.0f}%"
    )
    display_df["Δ Accept (pp)"] = display_df["delta_accept_pp"].map(
        lambda value: f"{value:+.0f}"
    )
    display_df["Δ Utility"] = display_df["delta_utility"].map(
        lambda value: f"{value:+.2f}"
    )

    display_df = display_df[
        [
            "Supervisor",
            "Fixed Accept",
            "Adaptive Accept",
            "Δ Accept (pp)",
            "Δ Utility",
        ]
    ]

    table = axis_right.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.7)

    axis_right.set_title("Summary Table")
    plt.suptitle("Adaptive Autonomy Results Summary", fontsize=16)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


## @brief Find the most recent complete single-seed batch directory.
## @param results_dir Path to the single_seed results directory.
## @return Tuple containing the latest batch directory and its six result files.
def find_latest_complete_batch(results_dir: Path) -> tuple[Path, List[Path]]:
    """Return the latest batch containing all six condition result files."""
    batch_directories = sorted(
        batch_path for batch_path in results_dir.iterdir() if batch_path.is_dir()
    )

    if not batch_directories:
        raise ValueError("No single-seed batch directories were found.")

    complete_batches: List[tuple[Path, List[Path]]] = []

    for batch_directory in batch_directories:
        result_files = sorted(batch_directory.glob("*.txt"))

        if len(result_files) == 6:
            complete_batches.append((batch_directory, result_files))

    if not complete_batches:
        raise ValueError("No complete single-seed batch with 6 files was found.")

    latest_batch_directory, latest_batch_files = complete_batches[-1]
    return latest_batch_directory, latest_batch_files


## @brief Ensure output directories exist.
## @param figures_dir Figures output directory.
## @param tables_dir Tables output directory.
def ensure_output_directories(figures_dir: Path, tables_dir: Path) -> None:
    """Create the figure and table output directories when needed."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)


## @brief Parse command-line arguments.
## @return Parsed argument namespace.
def parse_arguments() -> argparse.Namespace:
    """Parse command-line options for single-seed visualization generation."""
    parser = argparse.ArgumentParser(
        description="Generate single-seed result figures.",
    )
    parser.add_argument(
        "--batch-dir",
        type=str,
        default="",
        help="Specific single-seed batch directory to visualize. If omitted, latest batch is used.",
    )

    arguments = parser.parse_args()
    return arguments


## @brief Program entry point.
def main() -> None:
    """Load one complete single-seed batch and generate its report artifacts."""
    arguments = parse_arguments()
    results_dir = Path("results/single_seed")

    if arguments.batch_dir:
        latest_batch_dir = Path(arguments.batch_dir)
        latest_batch_files = sorted(latest_batch_dir.glob("*.txt"))

        if len(latest_batch_files) != 6:
            raise ValueError(
                f"Expected 6 result files in {latest_batch_dir}, found {len(latest_batch_files)}."
            )
    else:
        latest_batch_dir, latest_batch_files = find_latest_complete_batch(results_dir)

    figures_dir = latest_batch_dir / "figures"
    tables_dir = latest_batch_dir / "tables"
    ensure_output_directories(figures_dir, tables_dir)

    summaries = [parse_results_file(filepath) for filepath in latest_batch_files]

    raw_dataframe = build_summary_dataframe(summaries)
    summary_dataframe = add_rate_columns(raw_dataframe)
    presentation_table = build_presentation_summary_table(summary_dataframe)

    timestamp_prefix = latest_batch_dir.name

    save_table(
        dataframe=summary_dataframe,
        output_path=tables_dir / f"{timestamp_prefix}_raw_summary_table.csv",
    )

    save_table(
        dataframe=presentation_table,
        output_path=tables_dir / f"{timestamp_prefix}_presentation_summary_table.csv",
    )

    plot_acceptance_rate_comparison(
        dataframe=summary_dataframe,
        output_path=figures_dir / f"{timestamp_prefix}_acceptance_rate_comparison.png",
    )

    plot_recommendation_strength_distribution(
        dataframe=summary_dataframe,
        output_path=figures_dir / f"{timestamp_prefix}_recommendation_strength_distribution.png",
    )

    plot_acceptance_utility_trajectory(
        dataframe=summary_dataframe,
        output_path=figures_dir / f"{timestamp_prefix}_acceptance_utility_trajectory.png",
    )

    plot_slopegraph_table_combo(
        presentation_table=presentation_table,
        output_path=figures_dir / f"{timestamp_prefix}_slopegraph_table_combo.png",
    )

    print(f"Processed batch: {timestamp_prefix}")
    print(f"Saved tables to: {tables_dir}")
    print(f"Saved figures to: {figures_dir}")


if __name__ == "__main__":
    main()
