"""Augment the 16 base coffee descriptions to 2,416 for BRIDGE training (Study 1).

Each base description is rewritten under three length strategies, creating a
text-length confound that BRIDGE's nuisance controls must absorb:
  - summarize:  condense to the essentials (shorter)
  - paraphrase: reword at roughly the same length
  - elaborate:  expand with richer sensory detail (longer)

50 variations per strategy x 3 strategies = 150 augmented; with the original
kept, that is 151 per base description, or 16 x 151 = 2,416 training rows.
Generation uses a local Qwen 2.5 32B model via ollama (see README for setup);
model responses are cached on disk, so re-runs are deterministic and do not
re-query the model.

Pipeline step 2 of 5 (Coffee Certification, Study 1).
Input:  output/base_descriptions.pkl       (from step 01)
Output: output/augmented_descriptions.pkl
Usage:  python code/02_coffee_certification_augment_descriptions.py
"""

from pathlib import Path

import pandas as pd

from bridge.augmentation import VariationStrategy, augment_descriptions_sync

SUMMARIZE = VariationStrategy(
    name="summarize",
    instruction=(
        "condense to the essential points, making it noticeably shorter"
        " while preserving key information"
    ),
    temperature=0.4,
    max_tokens=80,
)

PARAPHRASE = VariationStrategy(
    name="paraphrase",
    instruction=(
        "reword naturally at roughly the same length, varying sentence"
        " structure and word choice"
    ),
    temperature=0.5,
    max_tokens=150,
)

ELABORATE = VariationStrategy(
    name="elaborate",
    instruction=(
        "expand with richer sensory details and fuller sentences, making it"
        " noticeably longer without adding new factual claims"
    ),
    temperature=0.6,
    max_tokens=250,
)

LENGTH_STRATEGIES = [SUMMARIZE, PARAPHRASE, ELABORATE]

SYSTEM_PROMPT = (
    "You are a specialty coffee copywriter. Generate a variation of the"
    " product description.\n\n"
    "CRITICAL RULES:\n"
    '1. PRESERVE the EXACT certification status:\n'
    '   - If original mentions "Fair Trade Certified\u2122", your version'
    " MUST mention Fair Trade\n"
    '   - If original mentions "USDA Organic certified", your version'
    " MUST mention Organic/USDA\n"
    '   - If original mentions "conventional", your version should NOT'
    " mention any certifications\n"
    "2. PRESERVE the flavor profile (nutty/balanced OR"
    " chocolatey/full-bodied)\n"
    "3. DO NOT invent new facts, claims, or attributes not in the"
    " original\n"
    "4. You may adjust LENGTH as instructed (shorter, same, or longer)\n"
    "5. When elaborating, expand on HOW things are described (richer"
    " adjectives, sensory details) - not WHAT is described"
)


def augment_coffee_descriptions(
    base_df: pd.DataFrame,
    num_variations: int = 50,
    backend: str = "ollama",
    model: str = "qwen2.5:32b-instruct-q8_0",
    cache_path: str = "output/augmented_coffee.json",
    verbose: bool = True,
) -> pd.DataFrame:
    """Augment the base descriptions with the three length strategies.

    For each base description we request `num_variations` rewrites under each of
    the three strategies, then append the unmodified original. Generation is
    delegated to `bridge.augmentation.augment_descriptions_sync`, which caches
    model responses at `cache_path` so re-runs are deterministic.

    Args:
        base_df: manifest from step 01 (description + attribute columns).
        num_variations: rewrites per base description PER strategy (50 in the study).
        backend: augmentation backend ("ollama", as used in the study).
        model: the exact local model used in the study.
        cache_path: JSON cache of model responses (skips re-querying on re-run).
        verbose: print the augmentation plan and a summary of the result.

    Returns:
        One row per (augmented + original) description, carrying the inherited
        attribute columns plus `augmentation_strategy` and `is_original`.
    """
    n_strategies = len(LENGTH_STRATEGIES)
    total_per_base = num_variations * n_strategies
    total_augmented = len(base_df) * total_per_base

    if verbose:
        # Echo the plan before the (slow) generation call.
        print(f"Augmenting {len(base_df)} descriptions")
        print(f"  Strategies: {[s.name for s in LENGTH_STRATEGIES]}")
        print(f"  Variations per strategy: {num_variations}")
        print(f"  Augmented per base: {total_per_base} (+1 original = {total_per_base + 1})")
        n_total = total_augmented + len(base_df)
        print(f"  Target: {total_augmented} augmented + {len(base_df)} originals = {n_total} total")

    result = augment_descriptions_sync(
        base_descriptions=base_df["description"].tolist(),
        num_variations=num_variations,
        strategies=LENGTH_STRATEGIES,
        backend=backend,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        base_attributes={
            "treatment": base_df["treatment"].tolist(),
            "profile": base_df["profile"].tolist(),
            "length_condition": base_df["length_condition"].tolist(),
            "experiment": base_df["experiment"].tolist(),
            "description_id": base_df["description_id"].tolist(),
        },
        cache_path=cache_path,
        verbose=verbose,
    )

    # One row per generated variation, inheriting its base description's attributes.
    augmented_rows = []
    for i, (desc, base_idx, strategy) in enumerate(zip(
        result.descriptions, result.base_indices, result.strategy_names
    )):
        base_row = base_df.iloc[base_idx]
        augmented_rows.append({
            "description": desc,
            "augmented_id": f"{base_row['description_id']}_{strategy}_{i}",
            "base_description_id": base_row["description_id"],
            "treatment": base_row["treatment"],
            "profile": base_row["profile"],
            "length_condition": base_row["length_condition"],
            "experiment": base_row["experiment"],
            "augmentation_strategy": strategy,
            "is_original": False,
        })

    # Append the 16 unmodified originals; step 03 recovers their nuisance
    # controls via the is_original mask.
    for _, row in base_df.iterrows():
        augmented_rows.append({
            "description": row["description"],
            "augmented_id": row["description_id"],
            "base_description_id": row["description_id"],
            "treatment": row["treatment"],
            "profile": row["profile"],
            "length_condition": row["length_condition"],
            "experiment": row["experiment"],
            "augmentation_strategy": "original",
            "is_original": True,
        })

    df = pd.DataFrame(augmented_rows)

    if verbose:
        # Summarize the realized augmentation for the run log.
        print("\nAugmentation complete:")
        print(f"  Total: {len(df)}  (originals: {df['is_original'].sum()}, "
              f"augmented: {(~df['is_original']).sum()})")
        print(f"  By experiment: {dict(df['experiment'].value_counts())}")
        print(f"  By strategy:   {dict(df['augmentation_strategy'].value_counts())}")

    return df


if __name__ == "__main__":
    # Read step 01's output; prefer a shipped precomputed copy when present.
    base_path = Path("precomputed/base_descriptions.pkl")
    if not base_path.exists():
        base_path = Path("output/base_descriptions.pkl")
    input_df = pd.read_pickle(base_path)
    print(f"Loaded {len(input_df)} base descriptions from {base_path}")

    augmented_df = augment_coffee_descriptions(input_df)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "augmented_descriptions.pkl"
    augmented_df.to_pickle(output_path)
    print(f"\nSaved {len(augmented_df)} descriptions to {output_path}")
