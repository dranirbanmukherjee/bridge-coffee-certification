# BRIDGE Reproducibility Bundle: Coffee Certification Experiments

This bundle reproduces the Coffee Certification Experiments from the manuscript
([`BRIDGE_Preprint.pdf`](BRIDGE_Preprint.pdf); Experiment 1: fair trade;
Experiment 2: organic). It demonstrates the complete
BRIDGE pipeline — from description augmentation through nuisance-control
extraction to Bayesian estimation — on a parsimonious application where
certification treatments are embedded in product text and deliberately
confounded with description length.

The code here is the same code used to produce the reported results: each script
runs end-to-end, and shipped `precomputed/` artifacts let you reproduce the
headline table without a GPU or an LLM.

**Preregistrations**: Fair Trade — aspredicted.org/7dt3ev.pdf; Organic — aspredicted.org/fz6y8h.pdf

---

## Quick Start (5 minutes)

To reproduce the reported results (Table 2 in the manuscript), run the R
estimation script — it loads the cached Bayesian models and pre-computed data:

```bash
cd bridge-coffee-certification    # (the folder is 02_Coffee_Certification in the OSF deposit)
Rscript code/05_coffee_certification_estimate.R   # prints the full results table
Rscript code/check_results.R                      # validates against RESULTS.md
```

No Python or BRIDGE installation required for the Quick Start.

---

## Setup

- **R** (4.3+) with packages: `brms`, `cmdstanr`, `dplyr`
- **Python** (3.14+) — only needed to re-run the BRIDGE pipeline (Steps 1–4)

Install the `bridge` package (for Steps 1–4) from its public repository, pinned to the version used in the paper:

```bash
pip install "git+https://github.com/dranirbanmukherjee/bridge.git@v0.2.0"
```

If you obtained this bundle via the [OSF data deposit](https://osf.io/5d6kx/), the
identical package source sits alongside the bundle and installs offline:

```bash
pip install ../bridge_package
```

The augmentation step (Step 2) additionally needs a local language model:

```bash
# Install ollama (https://ollama.com), then pull the model used in the study:
ollama pull qwen2.5:32b-instruct-q8_0
```

---

## What This Bundle Contains

```
bridge-coffee-certification/        # (= 02_Coffee_Certification/ in the OSF deposit)
├── README.md
├── BRIDGE_Preprint.pdf                 # Manuscript preprint (includes web appendix)
├── RESULTS.md                          # Validated results reference (Table 2 + LOOIC)
├── code/
│   ├── 01_coffee_certification_prepare_descriptions.py  # Step 1: 16 base descriptions
│   ├── 02_coffee_certification_augment_descriptions.py  # Step 2: augment to 2,416 via LLM
│   ├── 03_coffee_certification_train_bridge.py          # Step 3: train BRIDGE, extract controls
│   ├── 04_coffee_certification_merge_controls.py        # Step 4: map controls to experiment data
│   ├── 05_coffee_certification_estimate.R               # Step 5: Bayesian estimation (Table 2)
│   ├── 06_coffee_certification_descriptives.R           # Sample + manipulation checks (WA §E)
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
In the archived research deposit of this bundle, `output/` ships populated from
the authors' verification re-run; `precomputed/` remains the authoritative source
and every step prefers it when both copies exist.

**Sample sizes**: the raw exports hold all responses; estimation filters to the
completed, matched observations reported in the manuscript — **N = 353** (Fair
Trade) and **N = 352** (Organic).

**Survey instruments**: the Qualtrics files for both experiments
(`Coffee_fairtrade_cert_JMR.qsf`, `Coffee_organic_cert_JMR.qsf`) are not included in
this repository; they are in `00_Survey_Instruments/` in the
[OSF deposit](https://osf.io/5d6kx/).

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
Responses are cached to `output/augmented_coffee.json` as they are generated, so an
interrupted run resumes deterministically. A fresh run with no cache produces *new*
variations — the augmentation strategies sample at temperature 0.3–0.9 and no seed is
passed to the model — so the shipped `precomputed/augmented_descriptions.pkl` is the
authoritative record of the augmentations used in the paper.
*(Requires ollama; ~2–5 h.)*
**Output**: `output/augmented_descriptions.pkl`

### Step 3 — Train BRIDGE
```bash
python code/03_coffee_certification_train_bridge.py
```
Trains the BRIDGE network on three attributes (profile, condition, experiment),
selecting the architecture with Optuna (50 trials), and extracts the orthogonal
nuisance controls for the 16 originals via the SVD elbow criterion. *(Downloads
the gated `google/embeddinggemma-300m` encoder from Hugging Face — requires a
logged-in HF account with the Gemma license accepted; GPU/Apple-silicon recommended.)*
**Output**: `output/bridge_model/`

### Step 4 — Map nuisance controls to experiment data
```bash
python code/04_coffee_certification_merge_controls.py
```
Reads the raw Qualtrics exports, matches each participant's base/comparison
descriptions to the 16 originals, and writes the nuisance-control difference
(Comparison − Base) and the word-count difference. The CSVs carry all five extracted
nuisance components (`INTN1`–`INTN5`, in SVD order); the reported models use only the
first one or two (Step 5).
**Output**: `output/{ft,org}_data_with_nuisance.csv`

### Step 5 — Bayesian estimation
```bash
Rscript code/05_coffee_certification_estimate.R
```
Fits four Gaussian models per experiment and prints the full results table
(manuscript Table 2, plus the two-control BRIDGE variant noted there):
- **Naïve** (fit internally as the `oracle` model — a legacy internal key, unrelated to
  the "Oracle" of the paper's Monte Carlo simulations, where that name denotes the
  infeasible gold-standard estimator): a single Bayesian linear regression with condition indicators — the manuscript's Specification 1, which uses the medium-length condition as reference (matched = β̂₀, shorter = β̂₀ + β̂₁, longer = β̂₀ + β̂₂). The script fits the equivalent cell-means form (`Pref ~ 0 + ComparisonCondition`), whose coefficients are those three treatment effects directly; a sample-size-weighted *Naïve (pooled)* is derived from them
- **Word Count**: controls for the word-count difference
- **BRIDGE (1 control)** and **BRIDGE (2 controls)**: use the BRIDGE-derived nuisance controls

Cached models load instantly; re-fitting from scratch takes ~15 minutes.

An optional descriptives script (`code/06_coffee_certification_descriptives.R`)
reports sample composition and condition counts; it is not part of the Table 2
pipeline.

**Reproducibility note:** all models fit with a fixed seed (`seed = 42`, cmdstanr
backend, 4 chains), so refits reproduce the reported estimates exactly given the same
software versions. The shipped `precomputed/` fits are the authoritative record, and
`check_results.R` validates the reported numbers against them without refitting.

---

## Key Results (Table 2)

| Estimator | Fair Trade [95% CI] | Organic [95% CI] |
|-----------|---------------------|-------------------|
| Naïve (matched) | 1.32 [0.96, 1.69] | 0.97 [0.56, 1.38] |
| Naïve (shorter)  | 0.16 [−0.22, 0.52] | 0.38 [−0.02, 0.78] |
| Naïve (longer)   | 1.29 [0.88, 1.69] | 1.26 [0.89, 1.61] |
| Naïve (pooled)   | 0.92 [0.70, 1.14] | 0.88 [0.66, 1.11] |
| Word Count       | 0.80 [0.57, 1.04] | 0.76 [0.51, 0.99] |
| BRIDGE (1 ctrl)  | 1.24 [1.00, 1.49] | 1.02 [0.51, 1.54] |
| BRIDGE (2 ctrl)  | 1.29 [0.89, 1.70] | 0.95 [0.45, 1.43] |

BRIDGE recovers treatment effects comparable to the length-matched benchmark
without knowledge of the experimental conditions. The Word Count model
overcorrects at the matched condition: a standard word-count covariate does not
adequately capture the relationship between description length and preference.
The manuscript's Table 2 reports the one-control model as "BRIDGE"; its table
note records that results with two nuisance controls are similar (the
*BRIDGE (2 ctrl)* row above). Full per-parameter values are in `RESULTS.md`.

---

## Related Resources

- [**bridge**](https://github.com/dranirbanmukherjee/bridge) — the BRIDGE Python
  package used by Steps 1–4 of this pipeline (pinned to `v0.2.0` above).
- [**OSF deposit**](https://osf.io/5d6kx/) — the full replication package for all
  studies in the paper, of which this bundle is one component.

---

## Citation

> Behavioral Research Through Interpretable, Dimensionality-reduced Generative AI
> Embeddings (BRIDGE): A Method to Incorporate Real-World Stimuli in Consumer
> Experiments
>
> Anirban Mukherjee, Hannah H. Chang, and Sachin Gupta
>
> *Journal of Marketing Research*, 2026. https://doi.org/10.1177/00222437261484068

The manuscript preprint (including the web appendix) ships with this bundle as
[`BRIDGE_Preprint.pdf`](BRIDGE_Preprint.pdf) and is also available on
[SSRN](https://ssrn.com/abstract=5296429).

## Authors

- [**Anirban Mukherjee**](https://www.anirbanmukherjee.com) (anirban@avyayamholdings.com) — Principal, Avyayam Holdings
- [**Hannah H. Chang**](https://profhannahchang.github.io) (hannahchang@smu.edu.sg; *corresponding author*) — Associate Professor of Marketing, Lee Kong Chian School of Business, Singapore Management University
- [**Sachin Gupta**](https://business.cornell.edu/faculty-research/faculty/sg248/) (sg248@cornell.edu) — Henrietta Johnson Louis Professor of Marketing, SC Johnson College of Business, Cornell University

## Acknowledgments

This research was supported by the Ministry of Education (MOE), Singapore, under its Academic Research Fund (AcRF) Tier 2 Grant, No. MOE-T2EP40124-0005.

## License

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/). Copyright (c) 2025 Anirban Mukherjee, Hannah H. Chang, and Sachin Gupta. See [LICENSE](LICENSE) for the full text.
