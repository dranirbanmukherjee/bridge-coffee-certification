"""Map BRIDGE nuisance controls onto the experiment participant data (Study 1).

Reads the raw (de-identified) Qualtrics exports for the Fair Trade and Organic
experiments, matches each participant's base and comparison descriptions to the
16 original descriptions, looks up their BRIDGE nuisance controls, and writes
the nuisance difference (Comparison - Base) and the word-count difference. The
two resulting CSVs are the input to the Bayesian estimation in step 05; the
completion / validity / matched-row filtering happens there.

Pipeline step 4 of 5 (Coffee Certification, Study 1).
Inputs:  data/{Fair_Trade,Organic}_Coffee_Exp_Data_*.csv   (raw, de-identified)
         output/bridge_model/original_nuisance_controls.pkl (from step 03)
Outputs: output/{ft,org}_data_with_nuisance.csv
Usage:   python code/04_coffee_certification_merge_controls.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Raw, de-identified Qualtrics exports (paths are relative to the study root;
# run this script from the study/bundle root, as the other steps are run).
FT_RAW_PATH = "data/Fair_Trade_Coffee_Exp_Data_20251231.csv"
ORG_RAW_PATH = "data/Organic_Coffee_Exp_Data_20251230.csv"


def normalize_text(text: str) -> str:
    """Normalize text for matching (lowercase, strip, remove special chars)."""
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    for char in ['\u2122', '\u00ae', '\u00a9', '\u201a\u00f1\u00a2', '\u201a\u00e4\u00f3',
                 '\u00e2\u201e\u00a2', '\u00e2\u20ac\u2122']:
        text = text.replace(char, '')
    return text


def create_nuisance_lookup(nuisance_path: str) -> dict[str, np.ndarray]:
    """Build a lookup from normalized description text to its nuisance vector.

    Args:
        nuisance_path: Path to original_nuisance_controls.pkl (16 rows, from step 03).

    Returns:
        Dict mapping each normalized description string to its INTN nuisance array.
    """
    df = pd.read_pickle(nuisance_path)

    nuisance_cols = sorted(
        [c for c in df.columns if c.startswith("INTN")],
        key=lambda x: int(x.replace("INTN", "")),
    )

    lookup = {}
    for _, row in df.iterrows():
        normalized = normalize_text(row["description"])
        lookup[normalized] = np.array([row[c] for c in nuisance_cols])

    return lookup


def find_closest_description(
    query: str,
    lookup: dict[str, np.ndarray],
) -> np.ndarray | None:
    """Find matching description in lookup via exact or substring match.

    Args:
        query: Query description text to find.
        lookup: Dictionary of normalized descriptions to nuisance embeddings.

    Returns:
        Nuisance embedding array if found, None otherwise.
    """
    normalized_query = normalize_text(query)

    if normalized_query in lookup:
        return lookup[normalized_query]

    for key, value in lookup.items():
        if key in normalized_query or normalized_query in key:
            return value

    return None


def count_words(text: str) -> int:
    """Count words in text (whitespace split, matches manual counts)."""
    if pd.isna(text):
        return 0
    return len(str(text).strip().split())


def map_nuisance_to_experiment(
    exp_data: pd.DataFrame,
    lookup: dict[str, np.ndarray],
    text_base_col: str = "Text_Base",
    text_comp_col: str = "Text_Comparison",
    verbose: bool = True,
) -> pd.DataFrame:
    """Attach nuisance-control and word-count differences to the experiment data.

    For each participant, matches the base and comparison descriptions to the
    original descriptions, then records the nuisance difference (Comparison minus
    Base) and the word-count difference. Rows whose base AND comparison both
    match are flagged in `nuisance_matched`; step 05 keeps only those.

    Args:
        exp_data: experiment rows with the two description-text columns.
        lookup: normalized-description -> nuisance-array map (create_nuisance_lookup).
        text_base_col: name of the base-description text column.
        text_comp_col: name of the comparison-description text column.
        verbose: print match-rate statistics.

    Returns:
        Copy of exp_data with added columns INTN1..INTNk (Comparison - Base),
        nuisance_matched (bool), and wc_base / wc_comparison / wc_diff.
    """
    if verbose:
        print(f"  Lookup has {len(lookup)} descriptions")
        print(f"  Processing {len(exp_data)} observations...")

    n_dims = len(next(iter(lookup.values())))
    matched_base = 0
    matched_comp = 0
    nuisance_diff = np.zeros((len(exp_data), n_dims))
    match_flags = np.zeros(len(exp_data), dtype=bool)

    for i, (_, row) in enumerate(exp_data.iterrows()):
        base_nuisance = find_closest_description(row[text_base_col], lookup)
        comp_nuisance = find_closest_description(row[text_comp_col], lookup)
        if base_nuisance is not None:
            matched_base += 1
        if comp_nuisance is not None:
            matched_comp += 1
        if base_nuisance is not None and comp_nuisance is not None:
            nuisance_diff[i] = comp_nuisance - base_nuisance
            match_flags[i] = True

    if verbose:
        n = len(exp_data)
        print(f"  Matched base: {matched_base}/{n} ({100 * matched_base / n:.1f}%)")
        print(f"  Matched comp: {matched_comp}/{n} ({100 * matched_comp / n:.1f}%)")
        print(f"  Both matched: {match_flags.sum()}/{n} ({100 * match_flags.sum() / n:.1f}%)")

    result = exp_data.copy()
    # Nuisance difference columns (Comparison - Base), one per BRIDGE nuisance dim.
    for i in range(n_dims):
        result[f"INTN{i + 1}"] = nuisance_diff[:, i]
    result["nuisance_matched"] = match_flags

    # Word-count control (the conventional baseline against BRIDGE in Table 2).
    result["wc_base"] = result[text_base_col].apply(count_words)
    result["wc_comparison"] = result[text_comp_col].apply(count_words)
    result["wc_diff"] = result["wc_comparison"] - result["wc_base"]

    return result


def load_raw_data(file_path: str, verbose: bool = True) -> pd.DataFrame:
    """Load raw Qualtrics CSV, skipping metadata rows if present."""
    data = pd.read_csv(file_path)
    # Qualtrics exports may have 2 metadata rows (question text + import IDs).
    # Detect by checking if row 0 has a non-date StartDate (e.g. "Start Date").
    if len(data) > 0 and isinstance(data.iloc[0].get("StartDate"), str):
        first_start = data.iloc[0]["StartDate"]
        if "Date" in first_start or "ImportId" in first_start:
            data = data.iloc[2:].reset_index(drop=True)
            if verbose:
                print("  Skipped 2 Qualtrics metadata rows")
    if verbose:
        print(f"  Loaded {len(data)} rows from {Path(file_path).name}")
    return data


def run_merge(output_base: str = "output", verbose: bool = True) -> None:
    """Merge the single joint BRIDGE model's nuisance controls into both experiments.

    Args:
        output_base: output directory holding bridge_model/ and receiving the CSVs.
        verbose: print progress and a short summary.
    """
    output_base = Path(output_base)

    if verbose:
        print("\n=== Loading raw experiment data ===")
    ft_raw = load_raw_data(FT_RAW_PATH, verbose=verbose)
    org_raw = load_raw_data(ORG_RAW_PATH, verbose=verbose)

    # Nuisance controls from step 03 (prefer a shipped precomputed copy).
    nuisance_path = Path("precomputed/bridge_model/original_nuisance_controls.pkl")
    if not nuisance_path.exists():
        nuisance_path = output_base / "bridge_model" / "original_nuisance_controls.pkl"
    lookup = create_nuisance_lookup(str(nuisance_path))
    if verbose:
        print(f"\n  BRIDGE model: {len(lookup)} descriptions in lookup")

    for name, raw in [("FT", ft_raw), ("Org", org_raw)]:
        if verbose:
            print(f"\n=== {name} data + BRIDGE nuisance ===")
        merged = map_nuisance_to_experiment(raw, lookup, verbose=verbose)
        out_path = output_base / f"{name.lower()}_data_with_nuisance.csv"
        merged.to_csv(out_path, index=False)
        if verbose:
            n_matched = int(merged["nuisance_matched"].sum())
            print(f"  Saved {n_matched}/{len(merged)} matched rows to {out_path}")


if __name__ == "__main__":
    run_merge(output_base="output")
    print("\nMerge complete.")
