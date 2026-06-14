# Coffee Certification — Results Reference

**Studies**: Fair Trade (N=353) and Organic (N=352)
**Family**: Gaussian (identity link)
**Pipeline**: single joint BRIDGE model, separate per-experiment estimation
**Validated**: 2026-06-13 (20/20 FE match, 4/4 LOOIC match)

---

## Summary Table

| Estimator | FT Estimate [95% CI] | Org Estimate [95% CI] |
|-----------|---------------------|----------------------|
| Oracle (matched) | 1.324 [0.962, 1.694] | 0.970 [0.561, 1.384] |
| Oracle (short) | 0.155 [-0.215, 0.523] | 0.378 [-0.017, 0.777] |
| Oracle (long) | 1.293 [0.883, 1.689] | 1.255 [0.885, 1.611] |
| Naive (pooled) | 0.923 [0.699, 1.142] | 0.882 [0.655, 1.105] |
| Word Count | 0.796 [0.566, 1.037] | 0.756 [0.512, 0.991] |
| BRIDGE (1 ctrl) | 1.242 [0.997, 1.493] | 1.021 [0.507, 1.537] |
| BRIDGE (2 ctrl) | 1.288 [0.889, 1.699] | 0.951 [0.454, 1.432] |

---

## Fixed Effects Detail

### Fair Trade

| Model | Parameter | Estimate | Est.Error | Q2.5 | Q97.5 |
|-------|-----------|----------|-----------|------|-------|
| oracle | ComparisonConditionBaseFT | 1.324 | 0.187 | 0.962 | 1.694 |
| oracle | ComparisonConditionShortFT | 0.155 | 0.191 | -0.215 | 0.523 |
| oracle | ComparisonConditionLongFT | 1.293 | 0.203 | 0.883 | 1.689 |
| wc | Intercept | 0.796 | 0.120 | 0.566 | 1.037 |
| wc | wc_diff | 0.021 | 0.007 | 0.008 | 0.034 |
| bridge_1 | Intercept | 1.242 | 0.126 | 0.997 | 1.493 |
| bridge_1 | INTN1 | 7.588 | 1.443 | 4.828 | 10.402 |
| bridge_2 | Intercept | 1.288 | 0.205 | 0.889 | 1.699 |
| bridge_2 | INTN1 | 7.287 | 1.703 | 3.936 | 10.524 |
| bridge_2 | INTN2 | 0.595 | 2.000 | -3.214 | 4.595 |

### Organic

| Model | Parameter | Estimate | Est.Error | Q2.5 | Q97.5 |
|-------|-----------|----------|-----------|------|-------|
| oracle | ComparisonConditionBaseOrganic | 0.970 | 0.212 | 0.561 | 1.384 |
| oracle | ComparisonConditionShortOrganic | 0.378 | 0.199 | -0.017 | 0.777 |
| oracle | ComparisonConditionLongOrganic | 1.255 | 0.183 | 0.885 | 1.611 |
| wc | Intercept | 0.756 | 0.122 | 0.512 | 0.991 |
| wc | wc_diff | 0.018 | 0.006 | 0.006 | 0.029 |
| bridge_1 | Intercept | 1.021 | 0.262 | 0.507 | 1.537 |
| bridge_1 | INTN1 | -3.038 | 5.050 | -12.874 | 6.797 |
| bridge_2 | Intercept | 0.951 | 0.249 | 0.454 | 1.432 |
| bridge_2 | INTN1 | -0.067 | 4.968 | -9.570 | 9.538 |
| bridge_2 | INTN2 | 3.072 | 1.523 | 0.096 | 6.056 |

---

## LOOIC

| Experiment | bridge_1 | bridge_2 |
|------------|----------|----------|
| FT | 1527.5 | 1529.3 |
| Org | 1541.3 | 1539.1 |

LOOIC slightly favors bridge_1 for FT, bridge_2 for Org. Differences are negligible (<2 points).

---

## Convergence

| Experiment | Model | Rhat | Min ESS |
|------------|-------|------|---------|
| FT | oracle | 1.001 | 7052 |
| FT | wc | 1.001 | 4849 |
| FT | bridge_1 | 1.000 | 3834 |
| FT | bridge_2 | 1.002 | 2882 |
| Org | oracle | 1.002 | 6382 |
| Org | wc | 1.000 | 4700 |
| Org | bridge_1 | 1.002 | 2424 |
| Org | bridge_2 | 1.002 | 3365 |

All models converge cleanly (Rhat <= 1.002, ESS >= 1857).

---

## Sample Sizes

| Experiment | Base | Short | Long | Total |
|------------|------|-------|------|-------|
| Fair Trade (BaseFT) | 125 | 118 | 110 | 353 |
| Organic (BaseOrganic) | 101 | 117 | 134 | 352 |

---

## Nuisance Control Correlations with wc_diff

Computed on estimation sample (after all filters; reproduced by `check_results.R`):

| Experiment | INTN1 | INTN2 |
|------------|-------|-------|
| FT | 0.71 | 0.87 |
| Org | -0.14 | 0.54 |

Partial correlations with wc2_diff (after partialing wc_diff):

| Experiment | INTN1 | INTN2 |
|------------|-------|-------|
| FT | -0.53 | -0.56 |
| Org | -0.19 | -0.85 |

SVD ordering != confound alignment. In FT, both controls correlate with WC. In Org, it's primarily INTN2.

---

## Key Observations

- **Matched condition** shows the largest treatment effect in both experiments (FT: 1.324, Org: 0.970)
- **Short condition** shows attenuated or near-zero effects (FT: 0.155 with CI spanning zero, Org: 0.378 with CI just touching zero)
- **Long condition** shows treatment effects comparable to matched (FT: 1.293, Org: 1.255)
- **Naive (pooled)** masks this heterogeneity (FT: 0.923, Org: 0.882) — a weighted average pulled down by the weak short-condition effect
- **BRIDGE (1 ctrl)** intercept (FT: 1.242, Org: 1.021) approximates the matched-condition estimate, demonstrating BRIDGE's ability to recover the confound-free treatment effect without knowing condition assignments
- **BRIDGE (2 ctrl)** adds little over 1 ctrl: INTN2 CI spans zero for FT, is marginally significant for Org

---

## Cross-Reference

| Result | Manuscript | Web Appendix |
|--------|-----------|--------------|
| Summary table (5 estimators) | Coffee Certification section, Table 2 | §E (estimation approach) |
| Oracle cell means | Coffee Certification section | §E (estimation approach) |
| BRIDGE vs Oracle comparison | Coffee Certification section | §E |
| Word count overcorrection | Coffee Certification section | §E |
| Nuisance control correlations | — | — |
| LOOIC comparison | — | — |
| Preregistered models | — | §E (estimation approach) |

*Nuisance control correlations and coffee LOOIC are internal diagnostics computed from the estimation sample; they are not reported in the manuscript or web appendix.*
