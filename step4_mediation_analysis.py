# -*- coding: utf-8 -*-
"""
Step 4: Bootstrap mediation analysis and publication-quality visualization.

This script performs a full non-parametric mediation analysis pipeline:
1. Reads the regional power Excel file.
2. Encodes scent categories as dummy variables.
3. Applies log10 transformation to correct positive skew.
4. Runs 5000-iteration bootstrap mediation (pingouin) for all
   Scent × Brain-Region paths.
5. Generates a composite figure with:
   A. Indirect effect heatmap
   B. Path-b coefficient heatmap
   C. Forest plot of the top 10 strongest mediation paths

Usage
-----
    python step4_mediation_analysis.py

Configuration
-------------
Edit ``config.py`` for file paths, bootstrap count, and significance
thresholds.
"""

# Set matplotlib backend to Agg (non-interactive, no GUI display)
import matplotlib

matplotlib.use('Agg')  # Must be called before importing matplotlib.pyplot

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    MEDIATION_INPUT_EXCEL,
    MEDIATION_OUTPUT_EXCEL,
    MEDIATION_SIG_EXCEL,
    MEDIATION_FIGURE,
    N_BOOTSTRAP,
    Y_COLUMN,
    ROI_NAMES,
    MIN_SAMPLE_SIZE,
)
from utils import categorize_scent, add_log_power_columns


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load and preprocess data
    # ------------------------------------------------------------------
    print("[INFO] Loading data...")
    df = pd.read_excel(MEDIATION_INPUT_EXCEL)
    df[Y_COLUMN] = pd.to_numeric(df[Y_COLUMN], errors="coerce")

    # Scent category dummy coding
    df["Scent_Category"] = df["Scent_Type"].apply(categorize_scent)
    dummy_df = pd.get_dummies(df["Scent_Category"], prefix="X", dtype=int)
    df = pd.concat([df, dummy_df], axis=1)
    X_cols = [col for col in dummy_df.columns if col != "X_Other"]

    # Log10 transformation of regional power
    M_cols = add_log_power_columns(df, ROI_NAMES)

    # ------------------------------------------------------------------
    # 2. Bootstrap mediation analysis
    # ------------------------------------------------------------------
    print(
        f"[INFO] Running {N_BOOTSTRAP}-iteration bootstrap mediation "
        f"for {len(X_cols)} scent predictors × {len(M_cols)} mediators..."
    )
    results = []

    for x_var in X_cols:
        for m_var in M_cols:
            temp_df = df[[x_var, m_var, Y_COLUMN]].dropna()
            if len(temp_df) < MIN_SAMPLE_SIZE:
                continue

            try:
                med = pg.mediation_analysis(
                    data=temp_df, x=x_var, m=m_var, y=Y_COLUMN,
                    n_boot=N_BOOTSTRAP,
                )
                a = med.iloc[0]
                b = med.iloc[1]
                ab = med.iloc[4]

                ci_low = ab["CI[2.5%]"]
                ci_high = ab["CI[97.5%]"]
                significant = not (ci_low <= 0 <= ci_high)

                results.append({
                    "Scent": x_var.replace("X_", ""),
                    "Brain_ROI": m_var.replace("Log_M_", "").replace("_Power", ""),
                    "a_coef": a["coef"],
                    "a_pval": a["pval"],
                    "b_coef": b["coef"],
                    "b_pval": b["pval"],
                    "ab_effect": ab["coef"],
                    "CI_low": ci_low,
                    "CI_high": ci_high,
                    "Significant": "YES" if significant else "NO",
                })
            except Exception:
                continue

    res_df = pd.DataFrame(results)

    # Fill missing ROI entries so the heatmap has no gaps
    full_index = pd.MultiIndex.from_product(
        [res_df["Scent"].unique(), ROI_NAMES],
        names=["Scent", "Brain_ROI"],
    )
    res_df = (
        res_df.set_index(["Scent", "Brain_ROI"])
        .reindex(full_index)
        .reset_index()
    )

    # ------------------------------------------------------------------
    # 3. Save results
    # ------------------------------------------------------------------
    res_df.to_excel(MEDIATION_OUTPUT_EXCEL, index=False)
    sig_df = res_df[res_df["Significant"] == "YES"]
    sig_df.to_excel(MEDIATION_SIG_EXCEL, index=False)
    print(
        f"[INFO] Analysis complete. "
        f"Found {len(sig_df)} significant mediation path(s)."
    )

    # ------------------------------------------------------------------
    # 4. Publication-quality visualization (Figure A + B + C)
    # ------------------------------------------------------------------
    print("[INFO] Generating publication figure...")

    # Configure seaborn style (works with Agg backend)
    sns.set_theme(style="white")

    # Create figure and subplots
    fig = plt.figure(figsize=(16, 11))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2])

    # --- Panel A: Indirect effect heatmap ---
    ax1 = fig.add_subplot(gs[0, 0])
    pivot_effect = res_df.pivot(
        index="Scent", columns="Brain_ROI", values="ab_effect"
    )
    sns.heatmap(
        pivot_effect, cmap="coolwarm", center=0, annot=True, fmt=".2f",
        ax=ax1, cbar_kws={"label": "Indirect Effect Size"},
    )
    ax1.set_title(
        "A. Mediation Effect (ab Path)",
        loc="left", fontsize=14, fontweight="bold",
    )
    ax1.set_ylabel("Scent Category", fontsize=12)
    ax1.set_xlabel("Brain Region", fontsize=12)

    # --- Panel B: Path-b coefficient heatmap ---
    ax2 = fig.add_subplot(gs[0, 1])
    pivot_b = res_df.pivot(
        index="Scent", columns="Brain_ROI", values="b_coef"
    )
    sns.heatmap(
        pivot_b, cmap="coolwarm", center=0, annot=True, fmt=".2f",
        ax=ax2, cbar_kws={"label": "b Coefficient"},
    )
    ax2.set_title(
        "B. Path b (Brain → Preference Rating)",
        loc="left", fontsize=14, fontweight="bold",
    )
    ax2.set_ylabel("")
    ax2.set_xlabel("Brain Region", fontsize=12)

    # --- Panel C: Forest plot of top 10 paths ---
    ax3 = fig.add_subplot(gs[1, :])
    df_plot = res_df.dropna().copy()
    df_plot["Path_Name"] = df_plot["Scent"] + " → " + df_plot["Brain_ROI"]
    df_plot["abs_effect"] = df_plot["ab_effect"].abs()
    df_plot = df_plot.sort_values("abs_effect", ascending=False).head(10)
    df_plot = df_plot.sort_values("abs_effect", ascending=True)

    df_plot["Color"] = np.where(
        (df_plot["CI_low"] > 0) | (df_plot["CI_high"] < 0),
        "#d62728",  # Red: significant
        "#1f77b4",  # Blue: non-significant
    )

    y_pos = np.arange(len(df_plot))
    ax3.axvline(0, color="black", linestyle="--", linewidth=1.5, zorder=2)

    for i, (_, row) in enumerate(df_plot.iterrows()):
        ax3.errorbar(
            x=row["ab_effect"], y=i,
            xerr=[[row["ab_effect"] - row["CI_low"]],
                  [row["CI_high"] - row["ab_effect"]]],
            fmt="o", color=row["Color"], markersize=9,
            elinewidth=2.5, capsize=6, capthick=2, zorder=3,
        )

    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(df_plot["Path_Name"], fontsize=12, fontweight="bold")
    ax3.set_xlabel(
        "Indirect Effect Size (ab) with 95% Confidence Interval", fontsize=12
    )
    ax3.set_title(
        "C. Forest Plot of Top 10 Strongest Mediation Paths",
        loc="left", fontsize=14, fontweight="bold",
    )

    # Zebra-stripe background for readability
    for i in range(len(y_pos)):
        if i % 2 == 0:
            ax3.axhspan(i - 0.5, i + 0.5, color="gray", alpha=0.08, zorder=1)

    sns.despine(ax=ax3, left=True, top=True, right=True)
    ax3.grid(axis="x", linestyle=":", alpha=0.6)

    fig.suptitle(
        "Figure 1. Global Mediation Analysis of Brain Oscillatory Power",
        fontsize=18, fontweight="bold", y=1.02,
    )

    # Use tight_layout and save (no plt.show())
    plt.tight_layout()
    plt.savefig(MEDIATION_FIGURE, dpi=600, bbox_inches="tight")
    plt.close(fig)  # Explicitly close the figure to free memory

    print(f"[DONE] Figure saved to: {MEDIATION_FIGURE}")


if __name__ == "__main__":
    main()