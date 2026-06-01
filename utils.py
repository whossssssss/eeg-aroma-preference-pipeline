# -*- coding: utf-8 -*-
"""
Shared utility functions for the EEG analysis pipeline.

Contains reusable helpers for scent categorization, data preprocessing,
and log-power transformation.
"""

import numpy as np
import pandas as pd


def categorize_scent(text: str) -> str:
    """
    Classify a scent description (in Russian) into one of six categories.

    Parameters
    ----------
    text : str
        Raw scent description string.

    Returns
    -------
    str
        One of: 'Citrus', 'Floral', 'Woody_Pine', 'Spicy_Gourmand',
        'Herbal_Mint', or 'Other'.
    """
    text = str(text).lower()
    if "цитрусовые" in text:
        return "Citrus"
    elif "цветочные" in text:
        return "Floral"
    elif any(kw in text for kw in ("хвойные", "древесные", "землистые")):
        return "Woody_Pine"
    elif any(kw in text for kw in ("пряные", "гурманские", "сладкий")):
        return "Spicy_Gourmand"
    elif any(kw in text for kw in ("травянистые", "мятные", "медицинские")):
        return "Herbal_Mint"
    else:
        return "Other"


def add_log_power_columns(
    df: pd.DataFrame,
    regions: list[str],
    epsilon: float = 1e-6,
) -> list[str]:
    """
    Create log10-transformed power columns for the specified brain regions.

    For each region name ``roi``, the function reads column ``M_{roi}_Power``,
    applies ``log10(value + epsilon)`` and stores the result in
    ``Log_M_{roi}_Power``.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame (modified in-place).
    regions : list of str
        Region abbreviations, e.g. ``['LF', 'MF', 'RF', ...]``.
    epsilon : float, optional
        Small constant added before log to avoid log(0). Default 1e-6.

    Returns
    -------
    list of str
        Column names of the newly created log-power columns.
    """
    log_cols = []
    for roi in regions:
        raw_col = f"M_{roi}_Power"
        log_col = f"Log_M_{roi}_Power"
        df[log_col] = np.log10(
            pd.to_numeric(df[raw_col], errors="coerce") + epsilon
        )
        log_cols.append(log_col)
    return log_cols


def prepare_analysis_dataframe(
    df: pd.DataFrame,
    regions: list[str],
    y_col: str = "Y_Rating",
) -> pd.DataFrame:
    """
    Prepare a clean analysis DataFrame with scent categories and log-power.

    Steps performed:
    1. Coerce ``y_col`` to numeric.
    2. Add scent category column via :func:`categorize_scent`.
    3. Create log10-power columns for each region.
    4. Select relevant columns and drop rows with missing values.

    Parameters
    ----------
    df : pd.DataFrame
        Raw input DataFrame.
    regions : list of str
        Brain region abbreviations.
    y_col : str, optional
        Name of the dependent-variable column. Default ``'Y_Rating'``.

    Returns
    -------
    pd.DataFrame
        Cleaned subset ready for statistical modeling.
    """
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df["Scent_Category"] = df["Scent_Type"].apply(categorize_scent)
    log_cols = add_log_power_columns(df, regions)
    keep_cols = ["Subject_ID", y_col, "Scent_Category"] + log_cols
    return df[keep_cols].dropna()
