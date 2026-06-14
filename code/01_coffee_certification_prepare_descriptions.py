"""Define the 16 base coffee descriptions for the Coffee Certification study (Study 1).

These are the verbatim experiment stimuli for the Fair Trade and Organic
certification experiments. BRIDGE is trained on three focal attributes derived
from each description:
  - profile:    nutty_balanced / chocolatey_fullbodied (2 levels)
  - condition:  base / certified (2 levels; derived from `treatment` in step 03)
  - experiment: fairtrade / organic (2 levels)

Description length varies across three conditions (short / medium / long) to
create a text-length confound. Length is NOT a BRIDGE attribute; the nuisance
controls must discover it from the text embeddings.

Study design:
  - Fair Trade:  2 baseline + 6 certified = 8 descriptions
  - Organic:     2 baseline + 6 certified = 8 descriptions
  - Total:       16 unique base descriptions

Pipeline step 1 of 5 (Coffee Certification, Study 1).
Output: output/base_descriptions.pkl
Usage:  python code/01_coffee_certification_prepare_descriptions.py
"""
# pylint: disable=line-too-long  # Description strings are verbatim experiment stimuli

from pathlib import Path

import pandas as pd

# ============================================================
# FAIR TRADE EXPERIMENT DESCRIPTIONS (8)
# ============================================================

FAIRTRADE_DESCRIPTIONS = {
    # Profile 1: Nutty/Balanced
    "ft_base_nutty": {
        "description": "This coffee's nutty aroma and balanced taste form a smooth profile. The beans are sourced through conventional trade practices used commonly.",
        "treatment": "ft_baseline",
        "profile": "nutty_balanced",
        "length_condition": "medium",
        "experiment": "fairtrade",
        "word_count": 21,
    },
    "ft_short_nutty": {
        "description": "This fair-trade coffee is nutty and balanced, Fair Trade Certified\u2122.",
        "treatment": "fairtrade",
        "profile": "nutty_balanced",
        "length_condition": "short",
        "experiment": "fairtrade",
        "word_count": 10,
    },
    "ft_medium_nutty": {
        "description": "This fair-trade coffee's nutty aroma and balanced taste form a smooth profile. The beans are sourced under Fair Trade Certified\u2122 standards.",
        "treatment": "fairtrade",
        "profile": "nutty_balanced",
        "length_condition": "medium",
        "experiment": "fairtrade",
        "word_count": 21,
    },
    "ft_long_nutty": {
        "description": "This fair-trade coffee's nutty aroma and balanced taste form a smooth profile with subtle hazelnut notes and a velvety finish. The beans are sourced under Fair Trade Certified\u2122 standards that make trade more equitable, ensuring farmers, workers, and producers are paid fairly, work in safe conditions, and can invest in their communities.",
        "treatment": "fairtrade",
        "profile": "nutty_balanced",
        "length_condition": "long",
        "experiment": "fairtrade",
        "word_count": 52,
    },
    # Profile 2: Chocolatey/Full-bodied
    "ft_base_chocolatey": {
        "description": "This coffee's chocolatey aroma and full-bodied taste deliver a deep finish. The beans are sourced through conventional trade practices used commonly.",
        "treatment": "ft_baseline",
        "profile": "chocolatey_fullbodied",
        "length_condition": "medium",
        "experiment": "fairtrade",
        "word_count": 21,
    },
    "ft_short_chocolatey": {
        "description": "This fair-trade coffee is chocolatey and full-bodied, Fair Trade Certified\u2122.",
        "treatment": "fairtrade",
        "profile": "chocolatey_fullbodied",
        "length_condition": "short",
        "experiment": "fairtrade",
        "word_count": 10,
    },
    "ft_medium_chocolatey": {
        "description": "This fair-trade coffee's chocolatey aroma and full-bodied taste deliver a deep finish. The beans are sourced under Fair Trade Certified\u2122 standards.",
        "treatment": "fairtrade",
        "profile": "chocolatey_fullbodied",
        "length_condition": "medium",
        "experiment": "fairtrade",
        "word_count": 21,
    },
    "ft_long_chocolatey": {
        "description": "This fair-trade coffee's chocolatey aroma and full-bodied taste deliver a deep finish with subtle cocoa notes and a rich character. The beans are sourced under Fair Trade Certified\u2122 standards that make trade more equitable, ensuring farmers, workers, and producers are paid fairly, work in safe conditions, and can invest in their communities.",
        "treatment": "fairtrade",
        "profile": "chocolatey_fullbodied",
        "length_condition": "long",
        "experiment": "fairtrade",
        "word_count": 52,
    },
}


# ============================================================
# ORGANIC EXPERIMENT DESCRIPTIONS (8)
# ============================================================

ORGANIC_DESCRIPTIONS = {
    # Profile 1: Nutty/Balanced
    "org_base_nutty": {
        "description": "This coffee's nutty aroma and balanced taste form a smooth profile. The beans are grown following conventional agriculture practices, used in regular coffee production.",
        "treatment": "org_baseline",
        "profile": "nutty_balanced",
        "length_condition": "medium",
        "experiment": "organic",
        "word_count": 24,
    },
    "org_short_nutty": {
        "description": "This organic coffee is nutty and balanced, USDA Organic certified.",
        "treatment": "organic",
        "profile": "nutty_balanced",
        "length_condition": "short",
        "experiment": "organic",
        "word_count": 10,
    },
    "org_medium_nutty": {
        "description": "This organic coffee's nutty aroma and balanced taste form a smooth profile. The beans are grown following organic agriculture standards, and USDA Organic certified.",
        "treatment": "organic",
        "profile": "nutty_balanced",
        "length_condition": "medium",
        "experiment": "organic",
        "word_count": 24,
    },
    "org_long_nutty": {
        "description": "This organic coffee's nutty aroma and balanced taste create a smooth profile with a velvety, rounded finish and subtle hazelnut notes. The beans are grown according to organic agriculture standards and are USDA Organic certified, meaning they are cultivated without synthetic pesticides or chemical fertilizers, using natural methods that promote biodiversity and prioritize soil health.",
        "treatment": "organic",
        "profile": "nutty_balanced",
        "length_condition": "long",
        "experiment": "organic",
        "word_count": 55,
    },
    # Profile 2: Chocolatey/Full-bodied
    "org_base_chocolatey": {
        "description": "This coffee's chocolatey aroma and full-bodied taste deliver a deep finish. The beans are grown following conventional agriculture practices, used in regular coffee production.",
        "treatment": "org_baseline",
        "profile": "chocolatey_fullbodied",
        "length_condition": "medium",
        "experiment": "organic",
        "word_count": 24,
    },
    "org_short_chocolatey": {
        "description": "This organic coffee is chocolatey and full-bodied, USDA Organic certified.",
        "treatment": "organic",
        "profile": "chocolatey_fullbodied",
        "length_condition": "short",
        "experiment": "organic",
        "word_count": 10,
    },
    "org_medium_chocolatey": {
        "description": "This organic coffee's chocolatey aroma and full-bodied taste deliver a deep finish. The beans are grown following organic agriculture standards, and USDA Organic certified.",
        "treatment": "organic",
        "profile": "chocolatey_fullbodied",
        "length_condition": "medium",
        "experiment": "organic",
        "word_count": 24,
    },
    "org_long_chocolatey": {
        "description": "This organic coffee's chocolatey aroma and full-bodied taste deliver a deep finish with a robust, rich character and subtle cocoa notes. The beans are grown according to organic agriculture standards and are USDA Organic certified, meaning they are cultivated without synthetic pesticides or chemical fertilizers, using natural methods that promote biodiversity and prioritize soil health.",
        "treatment": "organic",
        "profile": "chocolatey_fullbodied",
        "length_condition": "long",
        "experiment": "organic",
        "word_count": 55,
    },
}


# Combined dictionary
ALL_DESCRIPTIONS = {**FAIRTRADE_DESCRIPTIONS, **ORGANIC_DESCRIPTIONS}


def create_base_manifest() -> pd.DataFrame:
    """Assemble the 16 base descriptions into a flat manifest DataFrame.

    Returns:
        One row per description, with columns:
        - description_id:   unique key (e.g. "ft_long_nutty")
        - description:      the verbatim stimulus text
        - treatment:        ft_baseline / org_baseline / fairtrade / organic
        - profile:          nutty_balanced / chocolatey_fullbodied
        - length_condition: short / medium / long
        - experiment:       fairtrade / organic
        - word_count:       number of words in the description
    """
    rows = [{"description_id": desc_id, **attrs}
            for desc_id, attrs in ALL_DESCRIPTIONS.items()]
    return pd.DataFrame(rows)


def validate_descriptions(df: pd.DataFrame) -> None:
    """Guard that the manifest matches the pre-registered 16-description design.

    This is a reproducibility self-check: it does not modify the data, but it
    fails loudly if the stimulus set ever drifts from the design reported in the
    paper (Web Appendix Section E). It also prints the realized cell counts so a
    reader can confirm the balance at a glance when the script is run.

    Args:
        df: manifest returned by create_base_manifest().

    Raises:
        AssertionError: if the experiment / treatment / profile structure
            deviates from the expected 16-description design.
    """
    # Total: 8 Fair Trade + 8 Organic = 16 base descriptions.
    assert len(df) == 16, f"Expected 16 descriptions, got {len(df)}"

    # Each experiment contributes exactly 8 descriptions.
    exp_counts = df["experiment"].value_counts()
    assert exp_counts.get("fairtrade", 0) == 8, "Expected 8 Fair Trade descriptions"
    assert exp_counts.get("organic", 0) == 8, "Expected 8 Organic descriptions"

    # Within each experiment: 2 conventional baselines + 6 certified variants.
    treatment_counts = df["treatment"].value_counts()
    assert treatment_counts.get("ft_baseline", 0) == 2
    assert treatment_counts.get("org_baseline", 0) == 2
    assert treatment_counts.get("fairtrade", 0) == 6
    assert treatment_counts.get("organic", 0) == 6

    # The two taste profiles are balanced across the full set (8 each).
    profile_counts = df["profile"].value_counts()
    assert profile_counts.get("nutty_balanced", 0) == 8
    assert profile_counts.get("chocolatey_fullbodied", 0) == 8

    # Echo the realized design so a reader can eyeball the balance on a run.
    print("  Validation passed: 16 descriptions")
    print(f"    Experiments: {dict(exp_counts)}")
    print(f"    Treatments:  {dict(treatment_counts)}")
    print(f"    Profiles:    {dict(profile_counts)}")
    for treatment in ["fairtrade", "organic"]:
        lengths = df[df["treatment"] == treatment]["length_condition"].value_counts()
        print(f"    {treatment.capitalize()} lengths: {dict(lengths)}")


if __name__ == "__main__":
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    manifest = create_base_manifest()
    validate_descriptions(manifest)

    output_path = output_dir / "base_descriptions.pkl"
    manifest.to_pickle(output_path)
    print(f"\nSaved {len(manifest)} base descriptions to {output_path}")
