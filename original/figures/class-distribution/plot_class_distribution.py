import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


def generate_color_palette(n_colors):
    """
    Generate a visually distinct color palette with n colors.

    Args:
        n_colors (int): Number of colors to generate

    Returns:
        list: List of color strings
    """
    if n_colors <= 10:
        # Use tab10 colormap for up to 10 colors
        cmap = plt.cm.get_cmap('tab10')
        return [mcolors.rgb2hex(cmap(i)) for i in range(n_colors)]
    else:
        # Use hsv colormap for more colors
        cmap = plt.cm.get_cmap('hsv')
        return [mcolors.rgb2hex(cmap(i / n_colors)) for i in range(n_colors)]


def plot_sensor_distribution(
    input_csv,
    output_image,
    thresholds=(1000, 5000),
    highlight_range=(1510, 1620),
    highlight_label="Dredged channel region",
    dpi=800,
    margins=0.05,
    figsize=(12, 6),
    title="Class instance distribution by threshold distance ranges",
    xlabel="Channel number",
    ylabel="10s-window data frame count",
    max_threshold_column="30000",
):
    """
    Creates and saves a figure based on sensor data in the input CSV.

    Args:
        input_csv (str): Path to input CSV file
        output_image (str): Path to save output image
        thresholds (tuple/list): List of threshold values to plot
        highlight_range (tuple): Sensor range to highlight (start, end)
        highlight_label (str): Label for highlighted region
        dpi (int): DPI for output image
        margins (float): Plot margins
        figsize (tuple): Figure size (width, height)
        title (str): Plot title
        xlabel (str): X-axis label
        ylabel (str): Y-axis label
        max_threshold_column (str): Column name for maximum threshold (total counts)
    """
    # Load the CSV file
    try:
        data = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found: {input_csv}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    # Extract sensor numbers (first column)
    sensor_numbers = data.iloc[:, 0]

    # Get available threshold columns from CSV
    available_columns = [col for col in data.columns if col != data.columns[0]]

    # Sort thresholds to ensure proper order
    thresholds = sorted(thresholds)

    # Validate that requested thresholds exist in CSV
    missing_thresholds = []
    for thresh in thresholds:
        if str(thresh) not in available_columns:
            missing_thresholds.append(thresh)

    if missing_thresholds:
        print(f"Error: The following thresholds are not available in the CSV: {missing_thresholds}")
        print(f"Available thresholds in CSV: {available_columns}")
        sys.exit(1)

    # Validate max_threshold_column exists
    if max_threshold_column not in available_columns:
        print(f"Error: Max threshold column '{max_threshold_column}' not found in CSV")
        print(f"Available columns: {available_columns}")
        sys.exit(1)

    # Get total counts (maximum threshold column)
    total_counts = data[max_threshold_column]

    # Build the data series for stacked plot
    # We need n_thresholds + 1 regions:
    # - Below first threshold
    # - Between each pair of consecutive thresholds
    # - Above last threshold

    data_series = []
    labels = []

    # First region: below first threshold
    first_thresh = thresholds[0]
    counts_below_first = data[str(first_thresh)]
    data_series.append(counts_below_first)
    labels.append(f"Below {first_thresh}m")

    # Middle regions: between consecutive thresholds
    for i in range(len(thresholds) - 1):
        lower_thresh = thresholds[i]
        upper_thresh = thresholds[i + 1]

        counts_below_upper = data[str(upper_thresh)]
        counts_below_lower = data[str(lower_thresh)]
        counts_between = counts_below_upper - counts_below_lower

        data_series.append(counts_between)
        labels.append(f"Between {lower_thresh}m and {upper_thresh}m")

    # Last region: above last threshold
    last_thresh = thresholds[-1]
    counts_below_last = data[str(last_thresh)]
    counts_above_last = total_counts - counts_below_last
    data_series.append(counts_above_last)
    labels.append(f"Above {last_thresh}m")

    # Generate color palette
    n_regions = len(data_series)
    colors = generate_color_palette(n_regions)

    # Create the plot
    plt.figure(figsize=figsize)

    # Create the stacked plot
    plt.stackplot(
        sensor_numbers,
        *data_series,
        labels=labels,
        colors=colors,
        edgecolor="black",
        linewidth=0.5,
    )

    # Highlight the specified range (drawn on top with higher zorder)
    if highlight_range:
        plt.axvspan(
            highlight_range[0],
            highlight_range[1],
            facecolor="yellow",
            alpha=0.35,
            label=highlight_label,
            zorder=100,  # High zorder to draw on top of stackplot
            edgecolor='orange',
            linewidth=2,
        )

    # Add labels, title, and legend
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Adjust legend position based on number of items
    if n_regions <= 6:
        plt.legend(loc="upper left", fontsize=9)
    else:
        plt.legend(loc="upper left", fontsize=8, ncol=2)

    # Add grid for better readability
    plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Adjust margins
    plt.margins(x=margins, y=margins)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_image)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

    # Save the figure
    try:
        plt.savefig(output_image, dpi=dpi, bbox_inches="tight")
        plt.close()
        print(f"✓ Figure saved successfully to: {output_image}")
        print(f"✓ Plotted {n_regions} regions using thresholds: {thresholds}")
        print(f"✓ Image resolution: {dpi} DPI")
    except Exception as e:
        print(f"Error saving figure: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a sensor distribution plot with customizable thresholds.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default thresholds (1000, 5000)
  python3 plot_class_distribution.py input.csv output.png

  # Use custom thresholds
  python3 plot_class_distribution.py input.csv output.png --thresholds 1000 2000 3000 4000 5000

  # Disable highlight region
  python3 plot_class_distribution.py input.csv output.png --no-highlight

  # Customize highlight range and label
  python3 plot_class_distribution.py input.csv output.png --highlight_range 1440 1690 --highlight_label "Model 250"

  # High-resolution output
  python3 plot_class_distribution.py input.csv output.png --dpi 1200 --figsize 16 8
        """
    )

    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to the input CSV file containing sensor distribution data."
    )
    parser.add_argument(
        "output_image",
        type=str,
        help="Path to save the output image (PNG, JPG, PDF, etc.)."
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=int,
        default=[1000, 5000],
        help="List of threshold values to plot (default: 1000 5000). These must match column names in the CSV."
    )
    parser.add_argument(
        "--max-threshold-column",
        type=str,
        default="30000",
        help="Column name for the maximum threshold representing total counts (default: 30000)."
    )
    parser.add_argument(
        "--highlight_range",
        nargs=2,
        type=int,
        default=[1440, 1690],
        help="Sensor range to highlight with yellow background (default: 1440 1690). Use --no-highlight to disable."
    )
    parser.add_argument(
        "--highlight_label",
        type=str,
        default="Ship channel",
        help="Label for the highlighted region (default: 'Ship channel')."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=800,
        help="DPI (dots per inch) for the output image (default: 800)."
    )
    parser.add_argument(
        "--margins",
        type=float,
        default=0.05,
        help="Margins for the plot (default: 0.05)."
    )
    parser.add_argument(
        "--figsize",
        nargs=2,
        type=float,
        default=[12, 6],
        help="Figure size as width height in inches (default: 12 6)."
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Class instance distribution by threshold distance ranges",
        help="Title of the plot."
    )
    parser.add_argument(
        "--xlabel",
        type=str,
        default="Channel number",
        help="Label for the X-axis."
    )
    parser.add_argument(
        "--ylabel",
        type=str,
        default="10s-window data frame count",
        help="Label for the Y-axis."
    )
    parser.add_argument(
        "--no-highlight",
        action="store_true",
        help="Disable highlighting of sensor range."
    )

    args = parser.parse_args()

    # Print configuration
    print("=" * 70)
    print("Vessel Distribution Plotter")
    print("=" * 70)
    print(f"Input CSV:        {args.input_csv}")
    print(f"Output Image:     {args.output_image}")
    print(f"Thresholds:       {sorted(args.thresholds)}")
    print(f"Highlight Range:  {args.highlight_range if not args.no_highlight else 'Disabled'}")
    print(f"Figure Size:      {args.figsize[0]} x {args.figsize[1]} inches")
    print(f"DPI:              {args.dpi}")
    print("=" * 70)

    plot_sensor_distribution(
        input_csv=args.input_csv,
        output_image=args.output_image,
        thresholds=args.thresholds,
        highlight_range=args.highlight_range if not args.no_highlight else None,
        highlight_label=args.highlight_label,
        dpi=args.dpi,
        margins=args.margins,
        figsize=tuple(args.figsize),
        title=args.title,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        max_threshold_column=args.max_threshold_column,
    )


if __name__ == "__main__":
    main()
