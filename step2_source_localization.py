# -*- coding: utf-8 -*-
"""
Step 2: Source localization (sLORETA) and NIfTI export.

For each ASC segment file produced by Step 1, this script:
1. Loads the time-series matrix.
2. Bandpass-filters into each canonical frequency band.
3. Applies sLORETA source localization via MNE inverse operator.
4. Computes Hilbert envelope power in source space.
5. Saves the resulting volumetric power map as a compressed NIfTI (.nii.gz).

Heavy MNE objects (source space, forward model, inverse operator) are cached
on first run and reloaded from disk on subsequent runs.

Usage
-----
    python step2_source_localization.py

Configuration
-------------
Edit ``config.py`` to set ASC input folder, NIfTI output folder,
cache directory, channel layout, and frequency bands.
"""

import os
import numpy as np
import mne
from mne.minimum_norm import make_inverse_operator, apply_inverse_raw
from scipy.signal import hilbert
import nibabel as nib
from pathlib import Path

from config import (
    ASC_OUTPUT_DIR,
    NIFTI_OUTPUT_DIR,
    MNE_CACHE_DIR,
    SUBJECTS_DIR,
    SUBJECT,
    CH_NAMES,
    FREQ_BANDS,
    RESAMPLE_RATE,
)


def _build_info():
    """Create an MNE Info object with the specified channel montage."""
    info = mne.create_info(CH_NAMES, RESAMPLE_RATE, "eeg")
    montage = mne.channels.make_standard_montage("standard_1020")
    info.set_montage(montage)
    return info


def _get_or_create_source_space(src_path: str):
    """Load or compute the volume source space."""
    if os.path.exists(src_path):
        print("[INFO] Loading cached source space...")
        return mne.read_source_spaces(src_path)

    print("[INFO] Computing volume source space (pos=5.0 mm)...")
    src = mne.setup_volume_source_space(
        subject=SUBJECT,
        subjects_dir=SUBJECTS_DIR,
        pos=5.0,
        add_interpolator=True,
    )
    mne.write_source_spaces(src_path, src)
    return src


def _get_or_create_forward(fwd_path: str, info, src):
    """Load or compute the forward solution."""
    if os.path.exists(fwd_path):
        print("[INFO] Loading cached forward solution...")
        return mne.read_forward_solution(fwd_path)

    print("[INFO] Building BEM model and forward solution...")
    model = mne.make_bem_model(subject=SUBJECT, subjects_dir=SUBJECTS_DIR)
    bem = mne.make_bem_solution(model)
    fwd = mne.make_forward_solution(
        info, trans=SUBJECT, src=src, bem=bem, eeg=True, meg=False
    )
    mne.write_forward_solution(fwd_path, fwd)
    return fwd


def _get_or_create_inverse(inv_path: str, info, fwd):
    """
    Load or compute the inverse operator.

    A single-sample dummy RawArray is used to generate a valid EEG average
    reference projection, which is required by the inverse operator.
    """
    if os.path.exists(inv_path):
        print("[INFO] Loading cached inverse operator...")
        return mne.minimum_norm.read_inverse_operator(inv_path)

    print("[INFO] Creating inverse operator with average-reference projection...")
    dummy_data = np.zeros((len(CH_NAMES), 1))
    dummy_raw = mne.io.RawArray(dummy_data, info.copy(), verbose=False)
    dummy_raw.set_eeg_reference(projection=True, verbose=False)
    info_with_proj = dummy_raw.info

    noise_cov = mne.make_ad_hoc_cov(info_with_proj, verbose=False)
    inv = make_inverse_operator(
        info_with_proj, fwd, noise_cov, loose=1.0, depth=0.8, verbose=False
    )
    mne.minimum_norm.write_inverse_operator(inv_path, inv)
    return inv


def main() -> None:
    # ------------------------------------------------------------------
    # Environment setup
    # ------------------------------------------------------------------
    os.environ["SUBJECTS_DIR"] = str(Path(SUBJECTS_DIR))
    info = _build_info()

    # ------------------------------------------------------------------
    # Build / load MNE pipeline objects (cached)
    # ------------------------------------------------------------------
    src_path = os.path.join(MNE_CACHE_DIR, "volume-src.fif")
    fwd_path = os.path.join(MNE_CACHE_DIR, "forward-fwd.fif")
    inv_path = os.path.join(MNE_CACHE_DIR, "inverse-inv.fif")

    src = _get_or_create_source_space(src_path)
    fwd = _get_or_create_forward(fwd_path, info, src)
    inv = _get_or_create_inverse(inv_path, info, fwd)

    # Use the source space attached to the inverse for consistency
    src = inv["src"]

    # ------------------------------------------------------------------
    # Process each ASC file
    # ------------------------------------------------------------------
    asc_files = sorted(f for f in os.listdir(ASC_OUTPUT_DIR) if f.endswith(".asc"))
    if not asc_files:
        print("[WARNING] No ASC files found. Run step1_generate_asc.py first.")
        return

    print(f"\n[INFO] Found {len(asc_files)} ASC file(s) to process.")

    for asc_file in asc_files:
        print(f"\n{'='*60}")
        print(f"[INFO] Processing: {asc_file}")

        # Load raw numeric matrix
        data = np.loadtxt(os.path.join(ASC_OUTPUT_DIR, asc_file))
        if data.shape[1] == len(CH_NAMES):
            data = data.T  # Ensure shape is (channels, times)

        base_name = asc_file.replace(".asc", "")
        save_dir = os.path.join(NIFTI_OUTPUT_DIR, base_name)
        os.makedirs(save_dir, exist_ok=True)

        # --------------------------------------------------------------
        # Per-band analysis
        # --------------------------------------------------------------
        for band, (fmin, fmax) in FREQ_BANDS.items():
            print(f"  -> Band: {band} ({fmin}-{fmax} Hz)")

            # 1. Bandpass filter on raw numpy array
            filtered_data = mne.filter.filter_data(
                data.copy(), sfreq=RESAMPLE_RATE,
                l_freq=fmin, h_freq=fmax, verbose=False,
            )

            # 2. Wrap into MNE Raw object
            raw_band = mne.io.RawArray(filtered_data, info, verbose=False)

            # 3. Apply average reference projection
            raw_band.set_eeg_reference(projection=True, verbose=False)
            raw_band.apply_proj()

            # 4. sLORETA source localization
            stc_band = apply_inverse_raw(
                raw_band, inv,
                lambda2=1.0 / 9.0,
                method="sLORETA",
                pick_ori="vector",
                verbose=False,
            )

            # 5. Hilbert envelope power
            analytic = hilbert(stc_band.data, axis=2)
            power = np.abs(analytic) ** 2
            mean_power = power.mean(axis=2).sum(axis=1)

            print(f"     Mean source power: {np.mean(mean_power):.6e}")

            # 6. Write NIfTI volume
            stc_power = mne.VolSourceEstimate(
                data=mean_power[:, np.newaxis],
                vertices=stc_band.vertices,
                tmin=0, tstep=1, subject=SUBJECT,
            )
            img = stc_power.as_volume(src, mri_resolution=True)
            nifti_path = os.path.join(save_dir, f"{base_name}_{band}.nii.gz")
            nib.save(img, nifti_path)

    print(f"\n[DONE] Source localization and NIfTI export complete.")


if __name__ == "__main__":
    main()
