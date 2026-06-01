# -*- coding: utf-8 -*-
"""
Step 7: Publication-quality interaction highlight visualization.

This script generates a multi-panel FacetGrid regression plot that:
- Highlights the specified scent category (e.g. Spicy_Gourmand) in bold red.
- Renders all other categories as faded gray background lines.
- Facets by brain region to show region-specific neural coding patterns.

Usage
-----
    python step7_interaction_visualization.py

Configuration
-------------
Edit ``config.py`` to set input Excel, target ROIs, highlight category,
and output figure path.
"""

# Set matplotlib backend to Agg (non-interactive, no GUI display)
import matplotlib

matplotlib.use('Agg')  # Must be called before importing matplotlib.pyplot

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    VIS_INPUT_EXCEL,
    VIS_TARGET_REGIONS,
    VIS_OUTPUT_FIGURE,
    HIGHLIGHT_CATEGORY,
    Y_COLUMN,
)
from utils import categorize_scent


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load and prepare data
    # ------------------------------------------------------------------
    print("[INFO] Loading data for interaction visualization...")
    df = pd.read_excel(VIS_INPUT_EXCEL)

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.4)
    plt.rcParams["font.family"] = "sans-serif"

    df[Y_COLUMN] = pd.to_numeric(df[Y_COLUMN], errors="coerce")
    df["Scent_Category"] = df["Scent_Type"].apply(categorize_scent)

    # Reshape to long format
    frames = []
    for roi in VIS_TARGET_REGIONS:
        log_col = f"Log_M_{roi}_Power"
        df[log_col] = np.log10(
            pd.to_numeric(df[f"M_{roi}_Power"], errors="coerce") + 1e-6
        )
        temp = df[["Subject_ID", Y_COLUMN, "Scent_Category", log_col]].copy()
        temp.columns = ["Subject_ID", Y_COLUMN, "Scent_Category", "Power"]
        temp["ROI"] = roi
        frames.append(temp)

    plot_df = pd.concat(frames).dropna()

    # ------------------------------------------------------------------
    # 2. Build the FacetGrid
    # ------------------------------------------------------------------
    print("[INFO] Generating interaction highlight figure...")

    # Create the FacetGrid
    g = sns.FacetGrid(
        plot_df,
        col="ROI",
        col_order=VIS_TARGET_REGIONS,
        hue="Scent_Category",
        height=5,
        aspect=0.8,
        sharex=False,
    )

    def _regplot(x, y, color, label, **kwargs):
        """Custom regplot: highlight target category, fade the rest."""
        ax = plt.gca()
        data = kwargs.pop("data")
        if label == HIGHLIGHT_CATEGORY:
            # Highlight category in bold red
            sns.regplot(
                x=x, y=y, data=data, ax=ax, color="#E74C3C",
                ci=None, scatter=False,
                line_kws={"linewidth": 4, "zorder": 10, "label": label},
            )
            # Also add scatter points for the highlighted category
            ax.scatter(
                data[x], data[y],
                color="#E74C3C", alpha=0.6, s=30,
                edgecolors="white", linewidth=0.5, zorder=5
            )
        else:
            # Other categories in faded gray
            sns.regplot(
                x=x, y=y, data=data, ax=ax, color="#BDC3C7",
                ci=None, scatter=False,
                line_kws={
                    "linewidth": 1.5, "alpha": 0.5,
                    "zorder": 1, "label": label,
                },
            )
            # Add scatter points for other categories (very faded)
            ax.scatter(
                data[x], data[y],
                color="#95A5A6", alpha=0.3, s=20,
                edgecolors="none", zorder=1
            )

    # Apply the custom regplot to all facets
    g.map_dataframe(_regplot, x="Power", y=Y_COLUMN)

    # ------------------------------------------------------------------
    # 3. Styling and legend
    # ------------------------------------------------------------------
    g.set_titles("{col_name} Region", fontweight="bold", size=16)
    g.set_axis_labels("Log₁₀ Power (a.u.)", "Preference Rating", size=14)

    for ax in g.axes.flat:
        ax.tick_params(labelsize=12)
        ax.grid(True, alpha=0.3)
        # Add horizontal line at zero for reference
        ax.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.5, zorder=0)

    # Handle legend
    handles, labels = g.axes.flat[0].get_legend_handles_labels()

    # Remove duplicates while preserving order
    unique_labels = []
    unique_handles = []
    for handle, label in zip(handles, labels):
        if label not in unique_labels:
            unique_labels.append(label)
            unique_handles.append(handle)

    # Create preferred order for legend
    preferred_order = [
        HIGHLIGHT_CATEGORY, "Citrus", "Floral",
        "Woody_Pine", "Herbal_Mint", "Other",
    ]

    # Create ordered handles and labels
    ordered_handles = []
    ordered_labels = []
    for cat in preferred_order:
        if cat in unique_labels:
            idx = unique_labels.index(cat)
            ordered_handles.append(unique_handles[idx])
            ordered_labels.append(unique_labels[idx])

    # Add any remaining categories not in preferred order
    for handle, label in zip(unique_handles, unique_labels):
        if label not in ordered_labels:
            ordered_handles.append(handle)
            ordered_labels.append(label)

    # Add legend
    g.fig.legend(
        ordered_handles, ordered_labels,
        title="Scent Category",
        title_fontsize=13,
        fontsize=11,
        loc="center right",
        bbox_to_anchor=(1.12, 0.5),
        frameon=True,
        fancybox=True,
        shadow=True,
    )

    # Adjust layout
    plt.subplots_adjust(top=0.85, right=0.88, left=0.08, bottom=0.08)

    # Add main title
    category_display = HIGHLIGHT_CATEGORY.replace('_', '/')
    g.fig.suptitle(
        f"Frequency-Specific Neural Coding Reversal:\nFocus on {category_display}",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )

    # Add subtitle with explanation
    g.fig.text(
        0.5, 0.98,
        "Regression lines show brain-power to preference relationships across scent categories",
        ha="center",
        fontsize=10,
        style="italic",
        alpha=0.7
    )

    # ------------------------------------------------------------------
    # 4. Save the figure (no display)
    # ------------------------------------------------------------------
    print(f"[INFO] Saving figure to: {VIS_OUTPUT_FIGURE}")

    # Ensure output directory exists
    import os
    output_dir = os.path.dirname(VIS_OUTPUT_FIGURE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"[INFO] Created output directory: {output_dir}")

    # Save with high resolution
    try:
        g.savefig(VIS_OUTPUT_FIGURE, dpi=600, bbox_inches="tight")
        print(f"[SUCCESS] Interaction highlight figure saved to: {VIS_OUTPUT_FIGURE}")
    except Exception as e:
        print(f"[ERROR] Failed to save figure: {e}")
        # Try saving as PNG with different settings
        try:
            alt_filename = VIS_OUTPUT_FIGURE.replace('.png', '_alt.png')
            g.savefig(alt_filename, dpi=300, bbox_inches="tight", format='png')
            print(f"[INFO] Saved alternative version to: {alt_filename}")
        except Exception as e2:
            print(f"[ERROR] Alternative save also failed: {e2}")

    # Close all figures to free memory
    plt.close('all')

    print("[DONE] Interaction visualization completed")


if __name__ == "__main__":
    main()