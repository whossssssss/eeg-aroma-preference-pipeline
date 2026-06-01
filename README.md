# EEG Source Localization and Mediation Analysis Pipeline

This repository contains a modular Python pipeline for EEG data processing and statistical analysis in an olfactory preference experiment. The pipeline covers the main computational steps from EEGLAB `.set` files to sLORETA-based source reconstruction, regional spectral power extraction, bootstrap mediation analysis, linear mixed modeling, and visualization of interaction effects.

The repository is associated with the master's thesis:

**“Mediation analysis and neural network models for predicting group response to aromas using 3D reconstruction of brain activity.”**

Raw EEG recordings and subject-level experimental data are not included in this repository due to privacy and ethical restrictions.

---

## Project Structure

```text
SHN/
├── config.py                          # Central configuration: paths, parameters, channel names, ROI coordinates
├── utils.py                           # Utility functions: scent classification, log-power transformation
├── step1_generate_asc.py              # Step 1: Convert EEG segments to ASC files
├── step2_source_localization.py       # Step 2: sLORETA source localization and NIfTI generation
├── step3_extract_power.py             # Step 3: Regional power extraction from ROI masks
├── step4_mediation_analysis.py        # Step 4: Bootstrap mediation analysis and visualization
├── step5_interaction.py               # Step 5: Brain region × scent interaction analysis
├── step6_lmm_statistics.py            # Step 6: Multi-band LMM interaction statistics
├── step7_interaction_visualization.py # Step 7: Interaction regression visualization
├── requirements.txt                   # Python dependencies
└── README.md                          # Repository description
```

---

## Computational Workflow

```text
Step 1 ──→ Step 2 ──→ Step 3 ──┬──→ Step 4: Mediation analysis
                                ├──→ Step 5: ROI × scent interaction analysis
                                ├──→ Step 6: LMM statistics table
                                └──→ Step 7: Interaction visualization
```

**Steps 1 → 2 → 3 must be executed sequentially**, because each step uses the output of the previous one.

**Steps 4 → 7 can be executed independently** after the regional power table has been generated in Step 3.

---

## Step 1 — Generate ASC Files

```bash
python step1_generate_asc.py
```

| Item               | Description                                                                           |
| ------------------ | ------------------------------------------------------------------------------------- |
| Input              | EEGLAB `.set` file                                                                    |
| Processing         | Load raw EEG, resample to 125 Hz if required, and slice the signal into time segments |
| Output             | One `.asc` text matrix file per segment                                               |
| Main config fields | `SET_FILE`, `RESAMPLE_RATE`, `SEGMENTS`, `ASC_OUTPUT_DIR`                             |

The output files are saved in scientific notation to reduce the risk of numerical truncation of small EEG amplitudes.

---

## Step 2 — sLORETA Source Localization

```bash
python step2_source_localization.py
```

| Item               | Description                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------- |
| Input              | `.asc` files generated in Step 1                                                                           |
| Processing         | Bandpass filtering, inverse source reconstruction using sLORETA, Hilbert-based power estimation            |
| Output             | One `.nii.gz` file per segment and frequency band                                                          |
| Caching            | Source space, forward model, and inverse operator can be cached and reused                                 |
| Main config fields | `ASC_OUTPUT_DIR`, `NIFTI_OUTPUT_DIR`, `MNE_CACHE_DIR`, `SUBJECTS_DIR`, `SUBJECT`, `CH_NAMES`, `FREQ_BANDS` |

Default frequency bands:

| Band  | Frequency range |
| ----- | --------------- |
| Delta | 0.5–4 Hz        |
| Theta | 4–8 Hz          |
| Alpha | 8–15 Hz         |
| Beta  | 15–25 Hz        |
| Gamma | 25–50 Hz        |

If the frequency ranges are changed, spectral features must be recomputed and the statistical analyses should be rerun, because the model inputs will change.

---

## Step 3 — Regional Power Extraction

```bash
python step3_extract_power.py
```

| Item                | Description                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| Input               | `.nii.gz` source-power files from Step 2 and metadata table            |
| Processing          | Extract mean power from spherical ROI masks using `NiftiSpheresMasker` |
| Output              | Excel table with regional power features                               |
| Main output columns | `M_LF_Power` to `M_RP_Power`                                           |
| Stability measures  | Periodic autosave and memory cleanup                                   |

Nine regions of interest are used:

| Abbreviation | Region          | MNI coordinates `(x, y, z)` |
| ------------ | --------------- | --------------------------- |
| LF           | Left frontal    | `(-40, 35, 30)`             |
| MF           | Middle frontal  | `(0, 45, 20)`               |
| RF           | Right frontal   | `(40, 35, 30)`              |
| LT           | Left temporal   | `(-55, -10, 10)`            |
| MC           | Middle central  | `(0, -10, 50)`              |
| RT           | Right temporal  | `(55, -10, 10)`             |
| LP           | Left parietal   | `(-40, -60, 40)`            |
| MP           | Middle parietal | `(0, -60, 30)`              |
| RP           | Right parietal  | `(40, -60, 40)`             |

The ROI radius is set to 15 mm by default.

---

## Step 4 — Bootstrap Mediation Analysis

```bash
python step4_mediation_analysis.py
```

| Item                 | Description                                                                     |
| -------------------- | ------------------------------------------------------------------------------- |
| Input                | Regional power table from Step 3                                                |
| Processing           | Scent dummy coding, log-power transformation, bootstrap mediation analysis      |
| Method               | `pingouin.mediation_analysis`                                                   |
| Bootstrap iterations | 5000                                                                            |
| Output               | Full mediation results, significant pathways table, and composite visualization |
| Significance rule    | 95% confidence interval of the indirect effect does not include zero            |

The mediation model evaluates whether EEG-derived regional power may mediate the relationship between odor category and subjective hedonic rating.

---

## Step 5 — Brain Region × Scent Interaction Analysis

```bash
python step5_interaction.py
```

| Item       | Description                                                            |           |
| ---------- | ---------------------------------------------------------------------- | --------- |
| Input      | Regional power table from Step 3                                       |           |
| Model      | `Rating ~ Power * Scent + (1                                           | Subject)` |
| Processing | Test interaction effects between regional EEG power and scent category |           |
| Output     | Console output and Excel table with interaction statistics             |           |
| Main focus | Interaction term `Power × Scent`                                       |           |

This step is used to evaluate whether the association between EEG power and subjective rating depends on the odor category.

---

## Step 6 — Multi-band LMM Statistics Table

```bash
python step6_lmm_statistics.py
```

| Item                 | Description                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| Input                | Regional power tables from multiple frequency bands                                                 |
| Processing           | Extract LMM interaction coefficients, standard errors, t-values, p-values, and confidence intervals |
| Output               | APA-style Excel table                                                                               |
| Retained terms       | Statistical effects with `p < 0.10`                                                                 |
| Significance markers | `*** p < 0.001`, `** p < 0.01`, `* p < 0.05`, `† p < 0.10`                                          |

This step is intended for preparing compact result tables for manuscript or thesis inclusion.

---

## Step 7 — Interaction Visualization

```bash
python step7_interaction_visualization.py
```

| Item         | Description                                                                              |
| ------------ | ---------------------------------------------------------------------------------------- |
| Input        | Regional power table from Step 3                                                         |
| Processing   | Regression plots faceted by brain region                                                 |
| Highlighting | Target odor category is highlighted, other categories are shown as background references |
| Output       | High-resolution PNG figure                                                               |

This step is used to visualize frequency- and region-specific interaction patterns, especially for the odor category showing statistically significant LMM effects.

---

## Configuration

All paths and parameters are defined in `config.py`. When moving the pipeline to another computer or dataset, edit this file first.

Example configuration fields:

```python
SET_FILE = r"path/to/input/file.set"
ASC_OUTPUT_DIR = r"path/to/output/asc"
NIFTI_OUTPUT_DIR = r"path/to/output/nifti"
NIFTI_INPUT_FOLDER = r"path/to/input/nifti"
EXCEL_INPUT_PATH = r"path/to/metadata.xlsx"

SUBJECTS_DIR = r"path/to/freesurfer/subjects_dir"
SUBJECT = "fsaverage"
RESAMPLE_RATE = 125
```

Before running the scripts, replace all local example paths with actual paths on your machine.

---

## Console Output Convention

The scripts use consistent log prefixes:

| Prefix      | Meaning                                |
| ----------- | -------------------------------------- |
| `[INFO]`    | General progress information           |
| `[OK]`      | Individual task completed successfully |
| `[DONE]`    | Full processing step completed         |
| `[WARNING]` | Non-critical warning                   |
| `[ERROR]`   | Processing exception                   |
| `[MISSING]` | Missing input file                     |
| `[SAVE]`    | Intermediate result saved              |
| `[TEST]`    | Statistical test started               |
| `[RESULT]`  | Statistical result printed             |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/USER/eeg-aroma-preference-pipeline.git
cd eeg-aroma-preference-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit paths and parameters
# Open config.py and replace example paths with local paths.

# 4. Run preprocessing and feature extraction
python step1_generate_asc.py
python step2_source_localization.py
python step3_extract_power.py

# 5. Run statistical analyses and visualization
python step4_mediation_analysis.py
python step5_interaction.py
python step6_lmm_statistics.py
python step7_interaction_visualization.py
```

Replace `USER` with the actual GitHub username.

---

## Dependencies

The core dependencies are listed in `requirements.txt`.

Main packages:

* `mne` — EEG data processing and source localization
* `numpy` — numerical computing
* `pandas` — tabular data processing
* `scipy` — signal processing and Hilbert transform
* `nibabel` — NIfTI file I/O
* `nilearn` — spherical ROI masking
* `pingouin` — bootstrap mediation analysis
* `statsmodels` — linear mixed models
* `matplotlib` — visualization
* `seaborn` — statistical visualization
* `openpyxl` — Excel file I/O

---

## Data Availability

Raw EEG recordings, subject-level metadata, and intermediate files are not included in this repository due to privacy, ethical, and storage restrictions.

The repository contains only the Python scripts required to reproduce the computational pipeline when appropriate input EEG data and metadata are provided.

Generated files such as `.asc`, `.nii.gz`, `.xlsx`, `.csv`, and figure outputs should be stored locally and are excluded from version control.

---

## Reproducibility Notes

This repository provides a modular analysis pipeline rather than a fully automatic one-click system. The scripts allow the main processing stages to be reproduced under the same experimental protocol and data structure.

If the frequency bands, ROI coordinates, statistical model specification, or input data structure are changed, the corresponding features must be recomputed and the statistical analyses must be rerun.

---

## Repository Citation

If this repository is referenced in academic work, it may be cited as:

```text
Shi H. EEG source localization and mediation analysis pipeline for olfactory EEG data. GitHub repository, 2026.
Available at: https://github.com/whossssssss/eeg-aroma-preference-pipeline
```

---

## Author

Shi Haonan
Novosibirsk State University
Master's program in Applied Mathematics and Computer Science
