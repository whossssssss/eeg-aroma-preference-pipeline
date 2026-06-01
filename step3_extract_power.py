# -*- coding: utf-8 -*-
"""
Step 3: Extract regional brain power from NIfTI source maps.

For each trial listed in the metadata Excel file, this script:
1. Locates the corresponding NIfTI file for the target frequency band.
2. Extracts mean power within 9 spherical ROIs (15 mm radius) using
   nilearn's NiftiSpheresMasker.
3. Writes the extracted values back into the Excel spreadsheet.

Memory management and periodic auto-saving are built in to ensure
robustness during long batch runs.

Usage
-----
    python step3_extract_power.py

Configuration
-------------
Edit ``config.py`` to set the NIfTI source folder, Excel file paths,
target frequency band, ROI definitions, and auto-save interval.
"""

import os
import gc
import warnings

import pandas as pd
from nilearn.maskers import NiftiSpheresMasker

from config import (
    NIFTI_INPUT_FOLDER,
    EXCEL_INPUT_PATH,
    TARGET_BAND,
    POWER_OUTPUT_EXCEL,
    BRAIN_REGIONS,
    ROI_NAMES,
    ROI_SPHERE_RADIUS,
    AUTOSAVE_INTERVAL,
)

warnings.filterwarnings("ignore")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Set up the spherical masker
    # ------------------------------------------------------------------
    coords_list = list(BRAIN_REGIONS.values())
    masker = NiftiSpheresMasker(
        seeds=coords_list, radius=ROI_SPHERE_RADIUS, allow_overlap=True
    )

    # ------------------------------------------------------------------
    # 2. Load metadata
    # ------------------------------------------------------------------
    df = pd.read_excel(EXCEL_INPUT_PATH)

    # Initialize power columns
    for name in ROI_NAMES:
        df[f"M_{name}_Power"] = None

    total = len(df)
    print(
        f"[INFO] Starting batch extraction for {total} trials.\n"
        f"       Band: {TARGET_BAND} | ROIs: {len(ROI_NAMES)} | "
        f"Auto-save every {AUTOSAVE_INTERVAL} trials."
    )

    # ------------------------------------------------------------------
    # 3. Iterate over trials
    # ------------------------------------------------------------------
    for index, row in df.iterrows():
        seg_id = str(row["Segment_ID"]).strip()
        subfolder = f"seg_{seg_id}"
        nii_filename = f"seg_{seg_id}_{TARGET_BAND}.nii.gz"
        nii_filepath = os.path.join(NIFTI_INPUT_FOLDER, subfolder, nii_filename)

        trial_num = index + 1

        if os.path.exists(nii_filepath):
            try:
                powers = masker.fit_transform(nii_filepath)[0]
                for i, name in enumerate(ROI_NAMES):
                    df.at[index, f"M_{name}_Power"] = powers[i]
                print(f"[OK]      Trial {trial_num}/{total} ({seg_id}): extraction successful.")
            except Exception as e:
                print(f"[ERROR]   Trial {trial_num}/{total} ({seg_id}): {e}")
        else:
            print(f"[MISSING] Trial {trial_num}/{total} ({seg_id}): file not found -> {nii_filename}")

        # Release unreferenced memory
        gc.collect()

        # Periodic checkpoint save
        if trial_num % AUTOSAVE_INTERVAL == 0 or trial_num == total:
            df.to_excel(POWER_OUTPUT_EXCEL, index=False)
            print(f"[SAVE]    Progress saved ({trial_num}/{total} trials).")

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    print(
        f"\n[DONE] Power extraction complete.\n"
        f"       Output saved to: {POWER_OUTPUT_EXCEL}"
    )


if __name__ == "__main__":
    main()
