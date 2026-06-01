# -*- coding: utf-8 -*-
"""
Step 1: Generate sLORETA-compatible ASC files from raw EEG data.

This script loads a .set file (EEGLAB format), resamples to the target rate
(with built-in anti-aliasing), slices the specified time segments, and exports
each segment as a plain-text ASC matrix in scientific notation (%.12e) to
preserve the full precision of microvolt-scale signals.

Usage
-----
    python step1_generate_asc.py

Configuration
-------------
Edit ``config.py`` to set the input .set file path, output directory,
target sampling rate, and time segments.
"""

import os
import numpy as np
import mne

from config import (
    SET_FILE,
    ASC_OUTPUT_DIR,
    RESAMPLE_RATE,
    SEGMENTS,
)


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load raw EEG data
    # ------------------------------------------------------------------
    print(f"\n[INFO] Loading EEG data: {SET_FILE}")
    raw = mne.io.read_raw_eeglab(SET_FILE, preload=True, verbose=False)

    # ------------------------------------------------------------------
    # 2. Resample if the native rate differs from the target
    # ------------------------------------------------------------------
    if raw.info["sfreq"] != RESAMPLE_RATE:
        print(
            f"[INFO] Resampling to {RESAMPLE_RATE} Hz "
            "(MNE built-in method with anti-aliasing filter)..."
        )
        raw.resample(RESAMPLE_RATE)

    data = raw.get_data()  # shape: (n_channels, n_times)
    sfreq = raw.info["sfreq"]

    # ------------------------------------------------------------------
    # 3. Slice segments and export ASC files
    # ------------------------------------------------------------------
    generated_files = []
    total = len(SEGMENTS)

    for i, (start_sec, end_sec) in enumerate(SEGMENTS):
        start_sample = int(start_sec * sfreq)
        end_sample = int(end_sec * sfreq)

        if end_sample > data.shape[1]:
            print(
                f"[WARNING] Segment {start_sec}-{end_sec}s exceeds data "
                f"length ({data.shape[1]} samples). Skipping."
            )
            continue

        # Transpose so rows = time points, columns = channels
        segment_data = data[:, start_sample:end_sample].T
        filename = f"seg_{start_sec}_{end_sec}.asc"
        filepath = os.path.join(ASC_OUTPUT_DIR, filename)

        # Use scientific notation to prevent truncation of microvolt values
        np.savetxt(filepath, segment_data, delimiter=" ", fmt="%.12e")
        generated_files.append(filename)
        print(f"[{i + 1}/{total}] Generated: {filename}")

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    print(
        f"\n[DONE] ASC file generation complete. "
        f"{len(generated_files)}/{total} files written to:\n"
        f"       {ASC_OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
