# -*- coding: utf-8 -*-
"""
Centralized configuration for the EEG-to-Source-Localization pipeline.

All user-configurable paths, parameters, and constants are defined here.
Modify this file to adapt the pipeline to your local environment.

Directory layout::

    SHN/                        # PROJECT_ROOT (where this config.py lives)
    ├── data/
    │   ├── raw/                # Raw EEG .set input files
    │   ├── asc/                # ASC intermediate files (Step 1 → Step 2)
    │   ├── nifti/              # NIfTI intermediate files (Step 2 → Step 3)
    │   ├── cache/              # MNE source-space / forward / inverse cache
    │   ├── mne_data/           # FreeSurfer subject directory (SUBJECTS_DIR)
    │   ├── metadata.xlsx       # Trial metadata (Step 3 input)
    │   ├── delta_power.xlsx    # Per-band power data (Step 6 input)
    │   ├── beta_power.xlsx
    │   └── gamma_power.xlsx
    └── output/
        ├── figures/            # Publication-quality figures
        └── results/            # Excel result tables
"""

import os

# =============================================================================
# 0. Project Root
# =============================================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Convenience helpers
_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# =============================================================================
# 1. Raw EEG Input
# =============================================================================
SET_FILE = os.path.join(_DATA_DIR, "raw", "input.set")
RESAMPLE_RATE = 125  # Hz — target sampling rate after anti-alias resampling

# Time segments to extract (in seconds): [start, end]
SEGMENTS = [
    [837, 848], [964, 974], [1093, 1110],
    [1227, 1244], [1368, 1385], [1518, 1533],
]

# =============================================================================
# 2. Directory Layout
# =============================================================================
ASC_OUTPUT_DIR = os.path.join(_DATA_DIR, "asc")
NIFTI_OUTPUT_DIR = os.path.join(_DATA_DIR, "nifti")
MNE_CACHE_DIR = os.path.join(_DATA_DIR, "cache")

# =============================================================================
# 3. FreeSurfer / MNE Subject Configuration
# =============================================================================
SUBJECTS_DIR = os.path.join(_DATA_DIR, "mne_data")
SUBJECT = "fsaverage"

# =============================================================================
# 4. EEG Channel Names (48-channel layout)
# =============================================================================
CH_NAMES = [
    "Pz", "FC2", "F7", "T7", "FT7", "FCz", "Fz", "FC4", "TP8", "CP1",
    "PO4", "P7", "F6", "AF4", "C5", "F2", "P4", "PO8", "T8", "F8",
    "POz", "AF8", "Fp2", "C1", "F1", "P3", "P8", "FC1", "F4", "O1",
    "P5", "P1", "FC3", "C3", "Fpz", "C6", "CP4", "FC6", "P2", "PO3",
    "CP2", "TP7", "P6", "FT8", "C4", "CP5", "C2", "CP3",
]

# =============================================================================
# 5. Frequency Bands of Interest
# =============================================================================
FREQ_BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 15),
    "beta": (15, 25),
    "gamma": (25, 50),
}

# =============================================================================
# 6. Brain ROI Definitions (MNI coordinates, mm)
# =============================================================================
BRAIN_REGIONS = {
    "LF": (-40, 35, 30),
    "MF": (0, 45, 20),
    "RF": (40, 35, 30),
    "LT": (-55, -10, 10),
    "MC": (0, -10, 50),
    "RT": (55, -10, 10),
    "LP": (-40, -60, 40),
    "MP": (0, -60, 30),
    "RP": (40, -60, 40),
}
ROI_NAMES = list(BRAIN_REGIONS.keys())

ROI_SPHERE_RADIUS = 15.0  # mm — radius for NiftiSpheresMasker

# =============================================================================
# 7. Regional Power Extraction (Step 3)
# =============================================================================
NIFTI_INPUT_FOLDER = os.path.join(_DATA_DIR, "nifti")
EXCEL_INPUT_PATH = os.path.join(_DATA_DIR, "metadata.xlsx")
TARGET_BAND = "gamma"
POWER_OUTPUT_EXCEL = os.path.join(_OUTPUT_DIR, "results", "power_extraction.xlsx")
AUTOSAVE_INTERVAL = 10  # Save progress every N trials

# =============================================================================
# 8. Mediation Analysis Parameters (Step 4)
# =============================================================================
MEDIATION_INPUT_EXCEL = os.path.join(_OUTPUT_DIR, "results", "power_extraction.xlsx")
MEDIATION_OUTPUT_EXCEL = os.path.join(_OUTPUT_DIR, "results", "mediation_results.xlsx")
MEDIATION_SIG_EXCEL = os.path.join(_OUTPUT_DIR, "results", "mediation_significant.xlsx")
MEDIATION_FIGURE = os.path.join(_OUTPUT_DIR, "figures", "mediation_analysis.png")
N_BOOTSTRAP = 5000
Y_COLUMN = "Y_Rating"
MIN_SAMPLE_SIZE = 15  # Minimum observations per mediation path

# =============================================================================
# 9. LMM Interaction Analysis (Step 6)
# =============================================================================
LMM_FILE_PATHS = {
    "Delta (1-4 Hz)": os.path.join(_DATA_DIR, "delta_power.xlsx"),
    "Gamma (30-50 Hz)": os.path.join(_DATA_DIR, "gamma_power.xlsx"),
    "Beta (15-25 Hz)": os.path.join(_DATA_DIR, "beta_power.xlsx"),
}
LMM_TARGET_REGIONS = ["LF", "MC", "LP", "MP", "RP", "LT", "RT"]
LMM_OUTPUT_EXCEL = os.path.join(_OUTPUT_DIR, "results", "lmm_interaction_stats.xlsx")

# =============================================================================
# 10. Interaction Visualization (Step 7)
# =============================================================================
VIS_INPUT_EXCEL = os.path.join(_DATA_DIR, "gamma_power.xlsx")
VIS_TARGET_REGIONS = ["LF", "MC", "LP", "MP", "RP"]
VIS_OUTPUT_FIGURE = os.path.join(_OUTPUT_DIR, "figures", "interaction_highlight.png")
HIGHLIGHT_CATEGORY = "Spicy_Gourmand"

# =============================================================================
# 11. Ensure Required Directories Exist (module‑load safe — dirs only)
# =============================================================================
_REQUIRED_DIRS = [
    os.path.join(_DATA_DIR, "raw"),
    ASC_OUTPUT_DIR,
    NIFTI_OUTPUT_DIR,
    MNE_CACHE_DIR,
    SUBJECTS_DIR,
    os.path.join(_OUTPUT_DIR, "results"),
    os.path.join(_OUTPUT_DIR, "figures"),
]

for _dir in _REQUIRED_DIRS:
    os.makedirs(_dir, exist_ok=True)
