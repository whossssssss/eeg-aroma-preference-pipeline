# -*- coding: utf-8 -*-
"""
Step 6: Multi-band LMM interaction statistics extraction.

This script iterates over multiple frequency bands and brain regions,
fits Linear Mixed Models with Brain×Scent interaction terms, and
consolidates all significant (p < 0.10) interaction statistics into
a single APA-formatted Excel table suitable for direct inclusion in
a manuscript.

Usage
-----
    python step6_lmm_statistics.py

Configuration
-------------
Edit ``config.py`` to set file paths for each frequency band,
target ROIs, and output path.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from config import (
    LMM_FILE_PATHS,
    LMM_TARGET_REGIONS,
    LMM_OUTPUT_EXCEL,
    Y_COLUMN,
)
from utils import prepare_analysis_dataframe


def _significance_stars(p: float) -> str:
    """Return significance annotation for a p-value."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    elif p < 0.10:
        return "†"
    return ""


def main() -> None:
    all_results = []

    print("[INFO] Starting multi-band LMM interaction extraction...\n")

    for band_name, file_path in LMM_FILE_PATHS.items():
        print(f"  Processing band: {band_name}")
        try:
            df = pd.read_excel(file_path)
            analysis_df = prepare_analysis_dataframe(
                df, LMM_TARGET_REGIONS, Y_COLUMN
            )

            for roi in LMM_TARGET_REGIONS:
                log_col = f"Log_M_{roi}_Power"
                formula = f"Y_Rating ~ {log_col} * C(Scent_Category)"

                model = smf.mixedlm(
                    formula, analysis_df,
                    groups=analysis_df["Subject_ID"],
                )
                result = model.fit(disp=False)

                for term in result.pvalues.index:
                    if ":" in term and log_col in term:
                        clean_term = (
                            term
                            .replace("C(Scent_Category)[T.", "")
                            .replace("]", "")
                            .replace(log_col, f"{roi}_Power")
                        )
                        p_val = result.pvalues[term]
                        coef = result.params[term]
                        t_val = result.tvalues[term]

                        all_results.append({
                            "Frequency Band": band_name,
                            "Brain Region (ROI)": roi,
                            "Interaction Effect": clean_term,
                            "Coefficient (β)": round(coef, 4),
                            "t-value": round(t_val, 4),
                            "p-value": round(p_val, 4),
                            "Sig.": _significance_stars(p_val),
                        })

        except Exception as e:
            print(f"  [ERROR] Failed to process {band_name}: {e}")

    # ------------------------------------------------------------------
    # Compile and export
    # ------------------------------------------------------------------
    results_df = pd.DataFrame(all_results)

    # Keep only marginally significant or better (p < 0.10)
    results_df = results_df[results_df["p-value"] < 0.10]
    results_df = results_df.sort_values(
        by=["Frequency Band", "Brain Region (ROI)", "p-value"]
    )
    results_df.to_excel(LMM_OUTPUT_EXCEL, index=False)

    print(f"\n{'='*60}")
    print(f"[DONE] APA-formatted interaction table saved to:")
    print(f"       {LMM_OUTPUT_EXCEL}")
    print(f"       Total significant terms: {len(results_df)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
