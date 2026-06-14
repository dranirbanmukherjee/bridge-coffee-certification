# BRIDGE Reproducibility Bundle: Coffee Certification Experiments

This bundle reproduces the Coffee Certification Experiments (Study 1) from the
manuscript. It demonstrates the complete BRIDGE pipeline — from description
augmentation through nuisance-control extraction to Bayesian estimation — on a
parsimonious application where certification treatments are embedded in product
text and confounded with description length.

The code here is the same code used to produce the reported results: each script
runs end-to-end, and shipped `precomputed/` artifacts let you reproduce the
headline table without a GPU or an LLM.

**Preregistrations**: Fair Trade — aspredicted.org/7dt3ev.pdf; Organic — aspredicted.org/fz6y8h.pdf

---

## Quick Start (5 minutes)

To reproduce the reported results (Table 2 in the manuscript), run the R
estimation script — it loads the cached Bayesian models and pre-computed data:

```bash
cd 02_Coffee_Certification
Rscript code/05_coffee_certification_estimate.R   # prints the full results table
Rscript code/check_results.R                      # validates against RESULTS.md
```

No Python or BRIDGE installation required for the Quick Start.

---

## Setup

- **R** (4.3+) with packages: `brms`, `cmdstanr`, `dplyr`
- **Python** (3.14+) — only needed to re-run the BRIDGE pipeline (Steps 1–4)

Install the `bridge` package (for Steps 1–4) from its public repository:

```bash
pip install "git+https://github.com/dranirbanmukherjee/bridge.git"
```

The augmentation step (Step 2) additionally needs a local language model:

```bash
# Install ollama (https://ollama.com), then pull the model used in the study:
ollama pull qwen2.5:32b-instruct-q8_0
```

---

## What This Bundle Contains

```
02_Coffee_Certification/
├── README.md
├── RESULTS.md                          # Validated results reference (Table 2 + LOOIC)
├── code/
│   ├── 01_coffee_certification_prepare_descriptions.py  # Step 1: 16 base descriptions
│   ├── 02_coffee_certification_augment_descriptions.py  # Step 2: augment to 2,416 via LLM
│   ├── 03_coffee_certification_train_bridge.py          # Step 3: train BRIDGE, extract controls
│   ├── 04_coffee_certification_merge_controls.py        # Step 4: map controls to experiment data
│   ├── 05_coffee_certification_estimate.R               # Step 5: Bayesian estimation (Table 2)
│   └── check_results.R                                  # Validate fits against RESULTS.md
├── data/                               # Raw, de-identified Qualtrics exports
│   ├── Fair_Trade_Coffee_Exp_Data_20251231.csv
│   └── Organic_Coffee_Exp_Data_20251230.csv
└── precomputed/                        # Pre-built outputs (skip Steps 1–4)
    ├── base_descriptions.pkl           # 16 base coffee descriptions
    ├── augmented_descriptions.pkl      # 2,416 augmented descriptions
    ├── bridge_model/                   # Trained BRIDGE model + nuisance controls
    ├── ft_data_with_nuisance.csv       # FT experiment data + BRIDGE/word-count controls
    ├── org_data_with_nuisance.csv      # Org experiment data + BRIDGE/word-count controls
    └── models_separate/                # Cached Bayesian model fits (.rds)
```

Fresh runs write to an `output/` directory (git-ignored); each step prefers a
shipped `precomputed/` copy when present, so any step can be run independently.

**Sample sizes**: the raw exports hold all responses; estimation filters to the
completed, matched observations reported in the manuscript — **N = 353** (Fair
Trade) and **N = 352** (Organic).

**File formats**: `.pkl` for Python-internal handoffs, `.csv` at the Python→R
boundary (the estimation step reads the `*_data_with_nuisance.csv` files).

---

## Pipeline Overview

Run each step from the bundle root (`02_Coffee_Certification/`).

### Step 1 — Define base descriptions
```bash
python code/01_coffee_certification_prepare_descriptions.py
```
Builds 16 base coffee descriptions (8 Fair Trade, 8 Organic) varying by
certification framing, flavor profile, and description length.
**Output**: `output/base_descriptions.pkl`

### Step 2 — Augment descriptions
```bash
python code/02_coffee_certification_augment_descriptions.py
```
Uses a local Qwen 2.5 32B model to generate 150 variations per base description
(50 each for summarize / paraphrase / elaborate), yielding 2,416 training rows.
Responses are cached, so re-runs are deterministic. *(Requires ollama; ~2–5 h.)*
**Output**: `output/augmented_descriptions.pkl`

### Step 3 — Train BRIDGE
```bash
python code/03_coffee_certification_train_bridge.py
```
Trains the BRIDGE network on three attributes (profile, condition, experiment),
selecting the architecture with Optuna (50 trials), and extracts the orthogonal
nuisance controls for the 16 originals via the SVD elbow criterion.
**Output**: `output/bridge_model/`

### Step 4 — Map nuisance controls to experiment data
```bash
python code/04_coffee_certification_merge_controls.py
```
Reads the raw Qualtrics exports, matches each participant's base/comparison
descriptions to the 16 originals, and writes the nuisance-control difference
(Comparison − Base) and the word-count difference.
**Output**: `output/{ft,org}_data_with_nuisance.csv`

### Step 5 — Bayesian estimation
```bash
Rscript code/05_coffee_certification_estimate.R
```
Fits four Gaussian models per experiment and prints Table 2:
- **Oracle**: condition indicators → matched / shorter / longer cell means (and a sample-size-weighted *Naive (pooled)*)
- **Word Count**: controls for the word-count difference
- **BRIDGE (1 control)** and **BRIDGE (2 controls)**: use the BRIDGE-derived nuisance controls

Cached models load instantly; re-fitting from scratch takes ~15 minutes.

---

## Key Results (Table 2)

| Estimator | Fair Trade [95% CI] | Organic [95% CI] |
|-----------|---------------------|-------------------|
| Oracle (matched) | 1.32 [0.96, 1.69] | 0.97 [0.56, 1.38] |
| Oracle (short)   | 0.16 [−0.22, 0.52] | 0.38 [−0.02, 0.78] |
| Oracle (long)    | 1.29 [0.88, 1.69] | 1.26 [0.89, 1.61] |
| Naive (pooled)   | 0.92 [0.70, 1.14] | 0.88 [0.66, 1.11] |
| Word Count       | 0.80 [0.57, 1.04] | 0.76 [0.51, 0.99] |
| BRIDGE (1 ctrl)  | 1.24 [1.00, 1.49] | 1.02 [0.51, 1.54] |
| BRIDGE (2 ctrl)  | 1.29 [0.89, 1.70] | 0.95 [0.45, 1.43] |

BRIDGE recovers the matched-condition (Oracle) benchmark without observing the
experimental conditions. The Word Count model overcorrects because the effect of
text length on preference is nonlinear. Full per-parameter values are in
`RESULTS.md`.

---

## Citation

> Behavioral Research Through Interpretable, Dimensionality-reduced Generative AI
> Embeddings (BRIDGE): A Method to Incorporate Real-World Stimuli in Consumer
> Experiments
>
> Anirban Mukherjee, Hannah H. Chang, and Sachin Gupta

## Authors

- **Anirban Mukherjee** (anirban@avyayamholdings.com) — Principal, Avyayam Holdings
- **Hannah H. Chang** (hannahchang@smu.edu.sg; *corresponding author*) — Associate Professor of Marketing, Lee Kong Chian School of Business, Singapore Management University
- **Sachin Gupta** — Henrietta Johnson Louis Professor of Marketing, SC Johnson College of Business, Cornell University

## Acknowledgments

This research was supported by the Ministry of Education (MOE), Singapore, under its Academic Research Fund (AcRF) Tier 2 Grant, No. MOE-T2EP40124-0005.

## License

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/). Copyright (c) 2025 Anirban Mukherjee, Hannah H. Chang, and Sachin Gupta. See [LICENSE](LICENSE) for the full text.
