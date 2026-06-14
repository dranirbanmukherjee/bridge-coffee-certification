"""Train the joint BRIDGE model on the 2,416 augmented coffee descriptions (Study 1).

A single BRIDGE model is trained on three focal attributes:
  - profile:    nutty_balanced / chocolatey_fullbodied (2 levels)
  - condition:  base / certified (2 levels; derived from `treatment`)
  - experiment: fairtrade / organic (2 levels)

The architecture is selected by Optuna (50 trials), which searches the
Matryoshka truncation level (`mask_size`) and the layer widths. The model
reported in the paper used mask_size=512 with 14 units per attribute (Web
Appendix Section E). After training, the nuisance controls for the 16 original
(un-augmented) descriptions are extracted for the regression in step 05.

Pipeline step 3 of 5 (Coffee Certification, Study 1).
Input:  output/augmented_descriptions.pkl   (from step 02)
Output: output/bridge_model/  (model + representations + original_nuisance_controls.pkl)
Usage:  python code/03_coffee_certification_train_bridge.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from bridge import BRIDGEConfig, BRIDGEPipeline


def make_config(num_nuisance_dims: int | None = None) -> BRIDGEConfig:
    """Create BRIDGE config for gemma embeddings, Optuna searches mask_size."""
    return BRIDGEConfig(
        embedding_backend="gemma",
        embedding_model="google/embeddinggemma-300m",
        embedding_dim=768,
        # No mask_size or fixed_mask_size — let Optuna search [128, 256, 512, 768]
        num_nuisance_dims=num_nuisance_dims,
        nuisance_method="svd",
    )


def extract_original_nuisance(
    augmented_df: pd.DataFrame,
    nuisance_path: str,
    output_path: str,
    expected_originals: int,
    verbose: bool = True,
) -> pd.DataFrame:
    """Extract nuisance controls for original descriptions from saved embeddings.

    Uses is_original mask to index into nuisance_embedding.npy, avoiding
    recomputation of SVD via transform().

    Args:
        augmented_df: The augmented DataFrame (with is_original column).
        nuisance_path: Path to nuisance_embedding.npy from pipeline.export().
        output_path: Where to save original_nuisance_controls.pkl.
        expected_originals: Expected number of original descriptions (16).
        verbose: If True, print progress and statistics.

    Returns:
        DataFrame with original descriptions and their INTN columns.

    Raises:
        AssertionError: If counts don't match expectations or NaN found.
    """
    nuisance_embeddings = np.load(nuisance_path)

    original_mask = augmented_df["is_original"].values
    n_originals = original_mask.sum()

    if verbose:
        print(f"  Nuisance embedding shape: {nuisance_embeddings.shape}")
        print(f"  Original descriptions: {n_originals}")

    assert n_originals == expected_originals, (
        f"Expected {expected_originals} originals, got {n_originals}"
    )
    assert len(augmented_df) == nuisance_embeddings.shape[0], (
        f"Row count mismatch: augmented_df has {len(augmented_df)}, "
        f"nuisance has {nuisance_embeddings.shape[0]}"
    )

    original_df = augmented_df[original_mask].copy()
    original_nuisance = nuisance_embeddings[original_mask]

    num_dims = original_nuisance.shape[1]
    nuisance_cols = [f"INTN{i+1}" for i in range(num_dims)]

    for i, col in enumerate(nuisance_cols):
        original_df[col] = original_nuisance[:, i]

    # Use base_description_id as the canonical description_id
    if "base_description_id" in original_df.columns:
        original_df["description_id"] = original_df["base_description_id"]

    output_cols = [
        "description_id",
        "description",
        "treatment",
        "profile",
        "experiment",
        "length_condition",
    ] + nuisance_cols

    output_df = original_df[output_cols].copy()
    output_df.to_pickle(output_path)

    if verbose:
        print(f"  Saved {len(output_df)} original nuisance controls to {output_path}")
        print(f"  Nuisance dimensions: {num_dims}")
        for col in nuisance_cols[:3]:
            print(f"    {col}: mean={output_df[col].mean():.4f}, std={output_df[col].std():.4f}")
        if num_dims > 3:
            print(f"    ... ({num_dims - 3} more dimensions)")

    # Validate
    assert not output_df[nuisance_cols].isna().any().any(), "NaN in nuisance columns"

    return output_df


def train_bridge(
    augmented_path: Path,
    output_dir: Path,
    tune: bool = True,
    n_trials: int = 50,
    verbose: bool = True,
) -> BRIDGEPipeline:
    """Train the joint BRIDGE model and extract the originals' nuisance controls.

    Args:
        augmented_path: Path to augmented_descriptions.pkl (from step 02).
        output_dir: Directory for the model, representations, and nuisance controls.
        tune: If True, select the architecture with Optuna (as in the paper).
        n_trials: Number of Optuna trials (50 in the study).
        verbose: Print data summaries and training progress.

    Returns:
        The fitted BRIDGEPipeline.

    Raises:
        SystemExit: if `augmented_path` does not exist.
    """
    if not augmented_path.exists():
        print(f"ERROR: {augmented_path} not found. Run step 02 (augment) first.")
        sys.exit(1)

    augmented_df = pd.read_pickle(augmented_path)

    # Collapse the 4-level `treatment` into the binary certification condition
    # that BRIDGE actually learns (both baselines are conventional -> "base").
    augmented_df["condition"] = augmented_df["treatment"].map({
        "ft_baseline": "base",
        "org_baseline": "base",
        "fairtrade": "certified",
        "organic": "certified",
    })

    data = augmented_df.reset_index(drop=True)
    labels = {
        "profile": data["profile"].values,
        "condition": data["condition"].values,
        "experiment": data["experiment"].values,
    }

    if verbose:
        print(f"Loaded {len(data)} descriptions from {augmented_path}")
        print(f"  Originals: {int(data['is_original'].sum())}")
        for attr in ["profile", "condition", "experiment"]:
            vals = pd.Series(labels[attr])
            print(f"  {attr}: {sorted(vals.unique())} ({vals.nunique()} levels)")
        # Confirm the design is balanced across the learned attributes.
        print("\n  experiment x condition:")
        print(pd.crosstab(data["experiment"], data["condition"]))
        print("\n  profile x condition:")
        print(pd.crosstab(data["profile"], data["condition"]))

    # Train the single joint model; the architecture is chosen by Optuna.
    pipeline = BRIDGEPipeline(
        attributes=["profile", "condition", "experiment"],
        config=make_config(),
        output_dir=str(output_dir),
        verbose=verbose,
    )
    pipeline.fit(
        descriptions=data["description"].tolist(),
        labels=labels,
        tune=tune,
        n_trials=n_trials,
        use_cached_model=False,
    )
    pipeline.export()
    if verbose:
        print(f"\n  Representations exported to {output_dir}")

    # Recover nuisance controls for the 16 original descriptions; these INTN
    # columns are merged into the experiment data in step 04.
    extract_original_nuisance(
        augmented_df=data,
        nuisance_path=str(output_dir / "representations" / "nuisance_embedding.npy"),
        output_path=str(output_dir / "original_nuisance_controls.pkl"),
        expected_originals=16,
        verbose=verbose,
    )
    return pipeline


if __name__ == "__main__":
    # Prefer a shipped precomputed copy of step 02's output when present.
    augmented = Path("precomputed/augmented_descriptions.pkl")
    if not augmented.exists():
        augmented = Path("output/augmented_descriptions.pkl")

    model_dir = Path("output/bridge_model")
    model_dir.mkdir(parents=True, exist_ok=True)

    train_bridge(augmented, model_dir, tune=True, n_trials=50)
