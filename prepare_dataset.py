"""
prepare_dataset.py

Converts a raw, per-case symptom dataset (one row per patient/case, disease
name in the first column, 0/1 columns for every symptom) into the
aggregated disease-level probability table the Symptom Checker app expects:

    disease,prior,symptom_1,symptom_2,...

where `prior` = (case count for that disease) / (total cases), and each
symptom value = P(symptom present | disease), estimated as the fraction
of that disease's cases where the symptom column was 1.

Usage:
    python prepare_dataset.py <input_raw_csv> [output_csv]

Example:
    python prepare_dataset.py Final_Augmented_dataset_Diseases_and_Symptoms.csv dataset.csv

If your raw file uses a different column name for the disease label (not
"diseases" or "disease"), pass it with --label-col:

    python prepare_dataset.py raw.csv dataset.csv --label-col condition
"""

import argparse
import sys

import pandas as pd

EPS = 0.01  # floor/ceiling so no probability is exactly 0 or 1 (breaks log scoring)


def clamp(series):
    return series.clip(lower=EPS, upper=1 - EPS)


def main():
    parser = argparse.ArgumentParser(description="Aggregate a raw case-level symptom dataset into disease-level probabilities.")
    parser.add_argument("input_csv", help="Path to the raw per-case CSV")
    parser.add_argument("output_csv", nargs="?", default="dataset.csv", help="Where to write the aggregated CSV (default: dataset.csv)")
    parser.add_argument("--label-col", default=None, help="Name of the disease/label column, if not auto-detected")
    parser.add_argument("--min-cases", type=int, default=1, help="Drop diseases with fewer than this many cases (default: 1, keep all)")
    args = parser.parse_args()

    print(f"Reading {args.input_csv} ...")
    df = pd.read_csv(args.input_csv)

    label_col = args.label_col
    if label_col is None:
        for candidate in ("diseases", "disease", "condition", "label"):
            if candidate in df.columns:
                label_col = candidate
                break
    if label_col is None:
        label_col = df.columns[0]
        print(f"Could not auto-detect a disease column; assuming the first column '{label_col}'.")
    else:
        print(f"Using '{label_col}' as the disease column.")

    symptom_cols = [c for c in df.columns if c != label_col]
    print(f"Found {df[label_col].nunique()} diseases and {len(symptom_cols)} symptom columns across {len(df)} rows.")

    # Coerce symptom columns to numeric 0/1 in case of stray strings/blanks
    df[symptom_cols] = df[symptom_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    counts = df[label_col].value_counts()
    keep_diseases = counts[counts >= args.min_cases].index
    if len(keep_diseases) < df[label_col].nunique():
        dropped = df[label_col].nunique() - len(keep_diseases)
        print(f"Dropping {dropped} disease(s) with fewer than {args.min_cases} case(s).")
    df = df[df[label_col].isin(keep_diseases)]

    total_cases = len(df)
    grouped = df.groupby(label_col)
    prior = grouped.size() / total_cases
    symptom_probs = grouped[symptom_cols].mean()
    symptom_probs = symptom_probs.apply(clamp)

    out = symptom_probs.copy()
    out.insert(0, "prior", clamp(prior))
    out.index.name = "disease"
    out = out.reset_index()

    out.to_csv(args.output_csv, index=False)
    print(f"Wrote {len(out)} diseases x {len(symptom_cols)} symptoms to {args.output_csv}")


if __name__ == "__main__":
    sys.exit(main())
