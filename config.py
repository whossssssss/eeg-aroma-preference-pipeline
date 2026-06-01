# -*- coding: utf-8 -*-
"""
Centralized configuration for the EEG-to-Source-Localization pipeline.

All user-configurable paths, parameters, and constants are defined here.
Modify this file to adapt the pipeline to your local environment.
"""

import os

# =============================================================================
# 1. Raw EEG Input
# =============================================================================
SET_FILE = r"path/to/input/file.set"
RESAMPLE_RATE = 125  # Hz — target sampling rate after anti-alias resampling

# Time segments to extract (in seconds): [start, end]
SEGMENTS = [
    [837, 848], [964, 974], [1093, 1110],
    [1227, 1244], [1368, 1385], [1518, 1533],
]

# =============================================================================
# 2. Directory Layout
# =============================================================================
ASC_OUTPUT_DIR = r"path/to/output/asc"
NIFTI_OUTPUT_DIR = r"path/to/output/nifti"
MNE_CACHE_DIR = r"path/to/metadata.xlsx"

# =============================================================================
# 3. FreeSurfer / MNE Subject Configuration
# =============================================================================
SUBJECTS_DIR = r"path/to/mne_data"
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
# 7. Regional Power Extraction
# =============================================================================
NIFTI_INPUT_FOLDER = r"path/to/nii"
EXCEL_INPUT_PATH = r"path/to/xlsx"
TARGET_BAND = "gamma"
POWER_OUTPUT_EXCEL = r"path/to/xlsx"
AUTOSAVE_INTERVAL = 10  # Save progress every N trials

# =============================================================================
# 8. Mediation Analysis Parameters
# =============================================================================
MEDIATION_INPUT_EXCEL = r"path/to/xlsx"
MEDIATION_OUTPUT_EXCEL = r"path/to/xlsx"
MEDIATION_SIG_EXCEL = r"path/to/xlsx"
MEDIATION_FIGURE = r"path/to/result/png"
N_BOOTSTRAP = 5000
Y_COLUMN = "Y_Rating"
MIN_SAMPLE_SIZE = 15  # Minimum observations per mediation path

# =============================================================================
# 9. LMM Interaction Analysis
# =============================================================================
LMM_FILE_PATHS = {
    "Delta (0.5-4 Hz)": r"path/to/xlsx",
    "Gamma (25-50 Hz)": r"path/to/xlsx",
    "Beta (15-25 Hz)": r"path/to/xlsx",
}
LMM_TARGET_REGIONS = ["LF", "MC", "LP", "MP", "RP", "LT", "RT"]
LMM_OUTPUT_EXCEL = r"path/to/xlsx"

# =============================================================================
# 10. Interaction Visualization
# =============================================================================
VIS_INPUT_EXCEL = r"path/to/xlsx"
VIS_TARGET_REGIONS = ["LF", "MC", "LP", "MP", "RP"]
VIS_OUTPUT_FIGURE = r"path/to/result/png"
HIGHLIGHT_CATEGORY = "Spicy_Gourmand"

# =============================================================================
# 11. Ensure Required Directories Exist
# =============================================================================
for _dir in [ASC_OUTPUT_DIR, NIFTI_OUTPUT_DIR, MNE_CACHE_DIR]:
    os.makedirs(_dir, exist_ok=True)
