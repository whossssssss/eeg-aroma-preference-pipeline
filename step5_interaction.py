# -*- coding: utf-8 -*-
"""
Step 5: Brain × Scent interaction analysis.

This script tests whether the relationship between brain region power and
preference ratings is modulated by scent category using Linear Mixed Models.

For each ROI, fits:
    Y_Rating ~ Log_Power * C(Scent_Category) + (1 | Subject_ID)

Usage
-----
    python step5_interaction_analysis.py

Configuration
-------------
Edit ``config.py`` to set input file paths and region lists.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

from config import (
    MEDIATION_INPUT_EXCEL,
    ROI_NAMES,
    Y_COLUMN,
)
from utils import prepare_analysis_dataframe


def run_interaction_test(analysis_df: pd.DataFrame) -> list[dict]:
    """
    Test Brain-Region × Scent-Category interaction effects on ratings.

    For each ROI, fits:
        Y_Rating ~ Log_Power * C(Scent_Category) + (1 | Subject_ID)
    """
    print("\n" + "=" * 60)
    print("[TEST] Brain Region × Scent Category Interaction Effects")
    print("=" * 60)

    findings = []

    for roi in ROI_NAMES:
        log_col = f"Log_M_{roi}_Power"
        formula = f"Y_Rating ~ {log_col} * C(Scent_Category)"

        try:
            model = smf.mixedlm(
                formula, analysis_df,
                groups=analysis_df["Subject_ID"],
            )
            result = model.fit(disp=False)

            interaction_terms = [
                t for t in result.pvalues.index if ":" in t
            ]
            has_sig = False
            for term in interaction_terms:
                if result.pvalues[term] < 0.05:
                    has_sig = True
                    findings.append({
                        "ROI": roi,
                        "Term": term,
                        "p-value": result.pvalues[term],
                    })

            status = "SIGNIFICANT interaction found!" if has_sig else "No significant interaction."
            print(f"  {roi}: {status}")

        except Exception:
            pass  # Skip models that fail to converge

    if findings:
        print(
            f"\n[RESULT] {len(findings)} significant interaction term(s) detected."
        )
    else:
        print("\n[RESULT] No significant interactions found across all ROIs.")

    return findings


def main() -> None:
    # ------------------------------------------------------------------
    # Load and prepare data
    # ------------------------------------------------------------------
    print("[INFO] Loading data and preparing analysis DataFrame...")
    df = pd.read_excel(MEDIATION_INPUT_EXCEL)
    analysis_df = prepare_analysis_dataframe(df, ROI_NAMES, Y_COLUMN)

    # ------------------------------------------------------------------
    # Run statistical tests
    # ------------------------------------------------------------------
    run_interaction_test(analysis_df)

    print("\n[DONE] Interaction analysis complete.")


if __name__ == "__main__":
    main()