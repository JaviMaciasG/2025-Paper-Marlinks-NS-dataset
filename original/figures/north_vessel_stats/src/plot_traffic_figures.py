#!/usr/bin/env python3
"""
Generate the two traffic-characterization figures used in the manuscript:

1. Number of distinct vessel identities versus the number of day-wise folds
   in which each identity occurs.
2. Direction-specific distribution of anonymized lateral crossing offsets.

The script accepts either:
- passage-level directional data:
    passage_event,direction,lateral_crossing_offset_m
- or pre-binned directional data:
    direction,bin_left_m,bin_right_m,bin_center_m,passage_event_count

Examples
--------
Generate both figures using the default filenames in the script directory:

    python plot_traffic_figures.py

Generate only the recurrence figure:

    python plot_traffic_figures.py --figure recurrence

Use passage-level offsets and change the histogram resolution:

    python plot_traffic_figures.py \
        --figure lanes \
        --lane-csv traffic_directional_lane_offsets_source_data.csv \
        --lane-bins 35

Generate PDF figures:

    python plot_traffic_figures.py \
        --recurrence-output recurrence.pdf \
        --lane-output directional_lanes.pdf

Control the shared size and typography:

    python plot_traffic_figures.py \
        --figure-width 10 --figure-height 6.5 \
        --axis-title-font-size 26 \
        --axis-label-font-size 24 \
        --bar-label-font-size 22

Show figures interactively in addition to saving them:

    python plot_traffic_figures.py --show
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =============================================================================
# DEFAULT CONFIGURATION
# Modify these values directly for a simple, no-command-line workflow.
# Command-line arguments override these defaults.
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_RECURRENCE_CSV = SCRIPT_DIR / "traffic_vessel_recurrence_source_data.csv"
DEFAULT_LANE_CSV = SCRIPT_DIR / "traffic_directional_lane_offsets_source_data.csv"

DEFAULT_RECURRENCE_OUTPUT = SCRIPT_DIR / "traffic_vessel_recurrence_by_fold_count.png"
DEFAULT_LANE_OUTPUT = SCRIPT_DIR / "traffic_directional_lane_offsets.png"

DEFAULT_DPI = 300
DEFAULT_FONT_SIZE = 26
DEFAULT_AXIS_TITLE_FONT_SIZE = 26
DEFAULT_AXIS_LABEL_FONT_SIZE = 24
DEFAULT_BAR_LABEL_FONT_SIZE = 22
DEFAULT_FIGURE_SIZE = (10.0, 6.5)
DEFAULT_LANE_BINS = 30
DEFAULT_ALPHA = 0.58

DEFAULT_DIRECTION_ORDER = ("A", "B")
DEFAULT_DIRECTION_LABELS = {
    "A": "Direction A",
    "B": "Direction B",
}


def positive_int(value: str) -> int:
    """Argparse validator for positive integers."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be a positive integer.")
    return parsed


def positive_float(value: str) -> float:
    """Argparse validator for positive floating-point values."""
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero.")
    return parsed


def fraction(value: str) -> float:
    """Argparse validator for values in the closed interval [0, 1]."""
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("Value must be between 0 and 1.")
    return parsed


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
    source: Path,
) -> None:
    """Raise a clear error if a CSV lacks required columns."""
    missing = sorted(set(required_columns) - set(dataframe.columns))
    if missing:
        raise ValueError(
            f"{source} is missing required column(s): {', '.join(missing)}. "
            f"Available columns: {', '.join(map(str, dataframe.columns))}"
        )


def prepare_output_path(path: Path) -> Path:
    """Create the output directory and return an absolute output path."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def configure_matplotlib(
    font_size: float,
    axis_title_font_size: float,
    axis_label_font_size: float,
) -> None:
    """Apply global typography without selecting a custom color palette."""
    plt.rcParams.update(
        {
            "font.size": font_size,
            "axes.labelsize": axis_title_font_size,
            "xtick.labelsize": axis_label_font_size,
            "ytick.labelsize": axis_label_font_size,
            "legend.fontsize": font_size,
        }
    )


def plot_recurrence(
    csv_path: Path,
    output_path: Path,
    *,
    metric: str = "unique_vessels",
    figsize: tuple[float, float] = DEFAULT_FIGURE_SIZE,
    dpi: int = DEFAULT_DPI,
    title: str | None = None,
    show_percentages: bool = False,
    bar_label_font_size: float = DEFAULT_BAR_LABEL_FONT_SIZE,
) -> None:
    """
    Plot vessel-identity recurrence across day-wise folds.

    Parameters
    ----------
    metric:
        "unique_vessels" plots distinct vessel identities.
        "passage_events" plots passage-event counts associated with each
        recurrence category.
    """
    csv_path = csv_path.expanduser().resolve()
    df = pd.read_csv(csv_path)

    validate_columns(df, ["number_of_folds", metric], csv_path)

    percentage_column = {
        "unique_vessels": "percentage_of_unique_vessels",
        "passage_events": "percentage_of_passage_events",
    }[metric]

    if show_percentages:
        validate_columns(df, [percentage_column], csv_path)

    plot_df = (
        df[
            ["number_of_folds", metric]
            + ([percentage_column] if show_percentages else [])
        ]
        .copy()
        .sort_values("number_of_folds")
    )

    # Ensure that omitted zero-count recurrence categories still appear.
    maximum_fold = max(10, int(plot_df["number_of_folds"].max()))
    full_index = pd.Index(range(1, maximum_fold + 1), name="number_of_folds")
    plot_df = (
        plot_df.set_index("number_of_folds")
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    x = plot_df["number_of_folds"].to_numpy()
    y = plot_df[metric].to_numpy()

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    bars = ax.bar(x, y)

    ax.set_xlabel("Number of day-wise folds containing a vessel identity")
    if metric == "unique_vessels":
        ax.set_ylabel("Distinct vessel identities")
    else:
        ax.set_ylabel("Passage events")

    ax.set_xticks(x)
    ax.set_ylim(bottom=0)

    if title:
        ax.set_title(title)

    if show_percentages:
        percentages = plot_df[percentage_column].to_numpy()
        vertical_offset = max(y.max() * 0.012, 0.4)
        for bar, count, percentage in zip(bars, y, percentages):
            if count <= 0:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + vertical_offset,
                f"{percentage:.1f}%",
                ha="center",
                va="bottom",
                fontsize=bar_label_font_size,
            )
        ax.margins(y=0.10)

    output_path = prepare_output_path(output_path)
    fig.savefig(output_path, dpi=dpi)
    print(f"Saved recurrence figure: {output_path}")


def _direction_order(
    values: Iterable[str],
    preferred_order: tuple[str, ...] = DEFAULT_DIRECTION_ORDER,
) -> list[str]:
    """Return a stable direction order while preserving unexpected labels."""
    observed = [
        str(value) for value in pd.unique(np.asarray(list(values), dtype=object))
    ]
    ordered = [value for value in preferred_order if value in observed]
    ordered.extend(value for value in observed if value not in ordered)
    return ordered


def plot_lane_histogram_from_offsets(
    df: pd.DataFrame,
    output_path: Path,
    *,
    bins: int,
    alpha: float,
    figsize: tuple[float, float],
    dpi: int,
    title: str | None,
) -> None:
    """Plot overlaid histograms from one anonymized offset per passage."""
    validate_columns(
        df,
        ["direction", "lateral_crossing_offset_m"],
        Path("<passage-level lane dataframe>"),
    )

    clean = df[["direction", "lateral_crossing_offset_m"]].copy()
    clean["direction"] = clean["direction"].astype(str)
    clean["lateral_crossing_offset_m"] = pd.to_numeric(
        clean["lateral_crossing_offset_m"],
        errors="coerce",
    )
    clean = clean.dropna()

    if clean.empty:
        raise ValueError("The lane-offset CSV contains no valid numeric offsets.")

    directions = _direction_order(clean["direction"])
    all_offsets = clean["lateral_crossing_offset_m"].to_numpy()

    # Shared bin edges are essential for a meaningful direction comparison.
    bin_edges = np.histogram_bin_edges(all_offsets, bins=bins)

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)

    for direction in directions:
        values = clean.loc[
            clean["direction"] == direction,
            "lateral_crossing_offset_m",
        ].to_numpy()

        ax.hist(
            values,
            bins=bin_edges,
            alpha=alpha,
            label=DEFAULT_DIRECTION_LABELS.get(direction, direction),
        )

    ax.set_xlabel("Anonymized lateral crossing offset at the reference transect (m)")
    ax.set_ylabel("Passage events")
    ax.set_ylim(bottom=0)
    ax.legend()

    if title:
        ax.set_title(title)

    output_path = prepare_output_path(output_path)
    fig.savefig(output_path, dpi=dpi)
    print(f"Saved directional-lane figure: {output_path}")


def plot_lane_histogram_from_binned_counts(
    df: pd.DataFrame,
    output_path: Path,
    *,
    alpha: float,
    figsize: tuple[float, float],
    dpi: int,
    title: str | None,
) -> None:
    """Plot the directional distributions from pre-computed histogram bins."""
    required = [
        "direction",
        "bin_left_m",
        "bin_right_m",
        "bin_center_m",
        "passage_event_count",
    ]
    validate_columns(df, required, Path("<binned lane dataframe>"))

    clean = df[required].copy()
    clean["direction"] = clean["direction"].astype(str)
    for column in required[1:]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna()

    if clean.empty:
        raise ValueError("The binned lane CSV contains no valid histogram data.")

    directions = _direction_order(clean["direction"])
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)

    for direction in directions:
        subset = clean.loc[clean["direction"] == direction].sort_values("bin_left_m")
        widths = subset["bin_right_m"] - subset["bin_left_m"]

        ax.bar(
            subset["bin_left_m"],
            subset["passage_event_count"],
            width=widths,
            align="edge",
            alpha=alpha,
            label=DEFAULT_DIRECTION_LABELS.get(direction, direction),
        )

    ax.set_xlabel("Anonymized lateral crossing offset at the reference transect (m)")
    ax.set_ylabel("Passage events")
    ax.set_ylim(bottom=0)
    ax.legend()

    if title:
        ax.set_title(title)

    output_path = prepare_output_path(output_path)
    fig.savefig(output_path, dpi=dpi)
    print(f"Saved directional-lane figure: {output_path}")


def plot_lanes(
    csv_path: Path,
    output_path: Path,
    *,
    bins: int = DEFAULT_LANE_BINS,
    alpha: float = DEFAULT_ALPHA,
    figsize: tuple[float, float] = DEFAULT_FIGURE_SIZE,
    dpi: int = DEFAULT_DPI,
    title: str | None = None,
) -> None:
    """
    Plot directional-lane distributions.

    The input format is detected automatically:
    - passage-level offsets if `lateral_crossing_offset_m` exists;
    - pre-binned counts if the histogram-bin columns exist.
    """
    csv_path = csv_path.expanduser().resolve()
    df = pd.read_csv(csv_path)

    if "lateral_crossing_offset_m" in df.columns:
        plot_lane_histogram_from_offsets(
            df,
            output_path,
            bins=bins,
            alpha=alpha,
            figsize=figsize,
            dpi=dpi,
            title=title,
        )
        return

    binned_columns = {
        "direction",
        "bin_left_m",
        "bin_right_m",
        "bin_center_m",
        "passage_event_count",
    }
    if binned_columns.issubset(df.columns):
        plot_lane_histogram_from_binned_counts(
            df,
            output_path,
            alpha=alpha,
            figsize=figsize,
            dpi=dpi,
            title=title,
        )
        return

    raise ValueError(
        f"Could not identify the lane CSV format in {csv_path}. "
        "Expected either a 'lateral_crossing_offset_m' column or all of: "
        + ", ".join(sorted(binned_columns))
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate traffic-characterization figures from aggregate CSV data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--figure",
        choices=("both", "recurrence", "lanes"),
        default="both",
        help="Select which figure or figures to generate.",
    )

    parser.add_argument(
        "--recurrence-csv",
        type=Path,
        default=DEFAULT_RECURRENCE_CSV,
        help="CSV containing the vessel-identity recurrence summary.",
    )
    parser.add_argument(
        "--lane-csv",
        type=Path,
        default=DEFAULT_LANE_CSV,
        help=(
            "CSV containing either one lateral crossing offset per passage "
            "or pre-computed directional histogram bins."
        ),
    )

    parser.add_argument(
        "--recurrence-output",
        type=Path,
        default=DEFAULT_RECURRENCE_OUTPUT,
        help="Output path for the recurrence figure.",
    )
    parser.add_argument(
        "--lane-output",
        type=Path,
        default=DEFAULT_LANE_OUTPUT,
        help="Output path for the directional-lane figure.",
    )

    parser.add_argument(
        "--recurrence-metric",
        choices=("unique_vessels", "passage_events"),
        default="unique_vessels",
        help="Quantity plotted on the recurrence figure's vertical axis.",
    )
    parser.add_argument(
        "--show-recurrence-percentages",
        action="store_true",
        help="Annotate recurrence bars with percentages.",
    )

    parser.add_argument(
        "--lane-bins",
        type=positive_int,
        default=DEFAULT_LANE_BINS,
        help=(
            "Number of shared histogram bins when passage-level offsets are used. "
            "Ignored for pre-binned input."
        ),
    )
    parser.add_argument(
        "--alpha",
        type=fraction,
        default=DEFAULT_ALPHA,
        help="Transparency of overlapping directional histograms.",
    )

    parser.add_argument(
        "--dpi",
        type=positive_int,
        default=DEFAULT_DPI,
        help="Raster resolution. Ignored by vector outputs such as PDF and SVG.",
    )
    parser.add_argument(
        "--font-size",
        type=positive_float,
        default=DEFAULT_FONT_SIZE,
        help="Base font size, including legends and optional plot titles.",
    )
    parser.add_argument(
        "--axis-title-font-size",
        type=positive_float,
        default=DEFAULT_AXIS_TITLE_FONT_SIZE,
        help="Font size of the x- and y-axis titles.",
    )
    parser.add_argument(
        "--axis-label-font-size",
        type=positive_float,
        default=DEFAULT_AXIS_LABEL_FONT_SIZE,
        help="Font size of the tick labels on both axes.",
    )
    parser.add_argument(
        "--bar-label-font-size",
        type=positive_float,
        default=DEFAULT_BAR_LABEL_FONT_SIZE,
        help="Font size of percentage labels above recurrence bars.",
    )

    parser.add_argument(
        "--figure-width",
        "--recurrence-width",
        "--lane-width",
        dest="figure_width",
        type=positive_float,
        default=DEFAULT_FIGURE_SIZE[0],
        help="Width of both figures in inches (old figure-specific names are aliases).",
    )
    parser.add_argument(
        "--figure-height",
        "--recurrence-height",
        "--lane-height",
        dest="figure_height",
        type=positive_float,
        default=DEFAULT_FIGURE_SIZE[1],
        help="Height of both figures in inches (old figure-specific names are aliases).",
    )

    parser.add_argument(
        "--recurrence-title",
        default=None,
        help="Optional recurrence-figure title. Omit for no title.",
    )
    parser.add_argument(
        "--lane-title",
        default=None,
        help="Optional directional-lane figure title. Omit for no title.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the figures interactively after saving.",
    )

    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    configure_matplotlib(
        args.font_size,
        args.axis_title_font_size,
        args.axis_label_font_size,
    )

    try:
        if args.figure in {"both", "recurrence"}:
            plot_recurrence(
                args.recurrence_csv,
                args.recurrence_output,
                metric=args.recurrence_metric,
                figsize=(args.figure_width, args.figure_height),
                dpi=args.dpi,
                title=args.recurrence_title,
                show_percentages=args.show_recurrence_percentages,
                bar_label_font_size=args.bar_label_font_size,
            )

        if args.figure in {"both", "lanes"}:
            plot_lanes(
                args.lane_csv,
                args.lane_output,
                bins=args.lane_bins,
                alpha=args.alpha,
                figsize=(args.figure_width, args.figure_height),
                dpi=args.dpi,
                title=args.lane_title,
            )

        if args.show:
            plt.show()
        else:
            plt.close("all")

    except (
        FileNotFoundError,
        PermissionError,
        ValueError,
        pd.errors.ParserError,
    ) as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
