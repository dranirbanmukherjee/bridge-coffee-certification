#!/usr/bin/env Rscript
# =============================================================================
# check_results.R -- Validate Coffee Certification Results (Study 1)
# =============================================================================
#
# Purpose: Check the cached brms fits against the validated values in RESULTS.md
#          -- 20 fixed effects (Table 2), 4 LOOIC values, and the FT/Org sample
#          sizes. Reads only the cached .rds models; does NOT refit.
#
# Usage:  Rscript code/check_results.R   (run after step 05)
#
# =============================================================================

suppressPackageStartupMessages(library(brms))

#' Locate this script's own directory (robust under Rscript and source()).
#'
#' @return Character path to the directory containing this script.
#' @keywords internal
get_script_dir <- function() {
  cmd_args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", cmd_args, value = TRUE)
  if (length(file_arg) > 0) {
    # Rscript encodes spaces in --file= as "~+~"; decode before resolving.
    path <- gsub("~\\+~", " ", sub("^--file=", "", file_arg[1]))
    return(dirname(normalizePath(path)))
  }
  if (!is.null(sys.frame(1)$ofile)) {
    return(dirname(normalizePath(sys.frame(1)$ofile)))
  }
  getwd()
}
base_dir <- dirname(get_script_dir())  # script lives in code/, so the root is its parent

# Cached model fits: prefer a shipped precomputed copy, else the working output dir.
model_dir <- file.path(base_dir, "precomputed", "models_separate")
if (!dir.exists(model_dir)) model_dir <- file.path(base_dir, "output", "models_separate")

cat("COFFEE CERTIFICATION: RESULTS VALIDATION\n")
cat(rep("=", 55), "\n", sep="")

if (!dir.exists(model_dir)) stop("Model directory not found: ", model_dir)

# Ground truth from Results.md § Coffee Certification
# Fixed effects detail tables
ground_truth <- list(
  # FT oracle
  list(file="FT_oracle.rds", param="ComparisonConditionBaseFT", est=1.324, se=0.187),
  list(file="FT_oracle.rds", param="ComparisonConditionShortFT", est=0.155, se=0.191),
  list(file="FT_oracle.rds", param="ComparisonConditionLongFT", est=1.293, se=0.203),
  # FT wc
  list(file="FT_wc.rds", param="Intercept", est=0.796, se=0.120),
  list(file="FT_wc.rds", param="wc_diff", est=0.021, se=0.007),
  # FT bridge_1
  list(file="FT_bridge_1.rds", param="Intercept", est=1.242, se=0.126),
  list(file="FT_bridge_1.rds", param="INTN1", est=7.588, se=1.443),
  # FT bridge_2
  list(file="FT_bridge_2.rds", param="Intercept", est=1.288, se=0.205),
  list(file="FT_bridge_2.rds", param="INTN1", est=7.287, se=1.703),
  list(file="FT_bridge_2.rds", param="INTN2", est=0.595, se=2.000),
  # Org oracle
  list(file="Org_oracle.rds", param="ComparisonConditionBaseOrganic", est=0.970, se=0.212),
  list(file="Org_oracle.rds", param="ComparisonConditionShortOrganic", est=0.378, se=0.199),
  list(file="Org_oracle.rds", param="ComparisonConditionLongOrganic", est=1.255, se=0.183),
  # Org wc
  list(file="Org_wc.rds", param="Intercept", est=0.756, se=0.122),
  list(file="Org_wc.rds", param="wc_diff", est=0.018, se=0.006),
  # Org bridge_1
  list(file="Org_bridge_1.rds", param="Intercept", est=1.021, se=0.262),
  list(file="Org_bridge_1.rds", param="INTN1", est=-3.038, se=5.050),
  # Org bridge_2
  list(file="Org_bridge_2.rds", param="Intercept", est=0.951, se=0.249),
  list(file="Org_bridge_2.rds", param="INTN1", est=-0.067, se=4.968),
  list(file="Org_bridge_2.rds", param="INTN2", est=3.072, se=1.523)
)

# LOOIC ground truth
looic_truth <- list(
  list(file="FT_bridge_1.rds", label="FT bridge_1", val=1527.5),
  list(file="FT_bridge_2.rds", label="FT bridge_2", val=1529.3),
  list(file="Org_bridge_1.rds", label="Org bridge_1", val=1541.3),
  list(file="Org_bridge_2.rds", label="Org bridge_2", val=1539.1)
)

# Cache loaded models
loaded <- list()
n_checked <- 0
n_match <- 0
n_missing <- 0

cat("\n--- Fixed Effects ---\n\n")

for (gt in ground_truth) {
  fpath <- file.path(model_dir, gt$file)
  if (!file.exists(fpath)) {
    cat(sprintf("  MISSING: %s\n", gt$file))
    n_missing <- n_missing + 1
    next
  }

  if (is.null(loaded[[gt$file]])) {
    loaded[[gt$file]] <- readRDS(fpath)
  }
  fit <- loaded[[gt$file]]
  fe <- fixef(fit)

  if (!(gt$param %in% rownames(fe))) {
    cat(sprintf("  %-20s '%s' not found in %s\n", gt$file, gt$param, paste(rownames(fe), collapse=", ")))
    next
  }

  est <- fe[gt$param, "Estimate"]
  se <- fe[gt$param, "Est.Error"]
  ci_lo <- fe[gt$param, "Q2.5"]
  ci_hi <- fe[gt$param, "Q97.5"]

  n_checked <- n_checked + 1
  est_ok <- abs(round(est, 3) - gt$est) < 0.0015
  se_ok <- abs(round(se, 3) - gt$se) < 0.0015
  ok <- est_ok & se_ok
  if (ok) n_match <- n_match + 1

  cat(sprintf("  %-20s %-40s = %7.3f (SE=%6.3f) [%6.3f,%6.3f]  paper=%6.3f(%5.3f) %s\n",
              gt$file, gt$param, est, se, ci_lo, ci_hi, gt$est, gt$se,
              ifelse(ok, "OK", "MISMATCH")))
}

# LOOIC check
cat("\n--- LOOIC ---\n\n")
n_loo_checked <- 0
n_loo_match <- 0

for (lt in looic_truth) {
  fpath <- file.path(model_dir, lt$file)
  if (!file.exists(fpath)) { cat(sprintf("  MISSING: %s\n", lt$file)); next }

  if (is.null(loaded[[lt$file]])) loaded[[lt$file]] <- readRDS(fpath)
  fit <- loaded[[lt$file]]

  loo_obj <- tryCatch(loo(fit), error = function(e) NULL)
  if (!is.null(loo_obj)) {
    looic_val <- loo_obj$estimates["looic", "Estimate"]
    diff <- abs(round(looic_val, 1) - lt$val)
    ok <- diff < 0.15
    n_loo_checked <- n_loo_checked + 1
    if (ok) n_loo_match <- n_loo_match + 1
    cat(sprintf("  %-20s LOOIC = %.1f (paper: %.1f, diff: %.1f) %s\n",
                lt$label, looic_val, lt$val, diff, ifelse(ok, "OK", "MISMATCH")))
  } else {
    cat(sprintf("  %-20s LOO computation failed\n", lt$label))
  }
}

# Sample size check (read directly from the fitted models; no data file needed)
cat("\n--- Sample Sizes ---\n")
n_ft <- if (!is.null(loaded[["FT_oracle.rds"]])) nobs(loaded[["FT_oracle.rds"]]) else NA
n_org <- if (!is.null(loaded[["Org_oracle.rds"]])) nobs(loaded[["Org_oracle.rds"]]) else NA
cat(sprintf("  FT N = %s (expected 353) %s\n", n_ft,
            ifelse(!is.na(n_ft) && n_ft == 353, "OK", "MISMATCH")))
cat(sprintf("  Org N = %s (expected 352) %s\n", n_org,
            ifelse(!is.na(n_org) && n_org == 352, "OK", "MISMATCH")))

# Summary
cat(sprintf("\n=== SUMMARY: FE %d/%d match, LOOIC %d/%d match",
            n_match, n_checked, n_loo_match, n_loo_checked))
if (n_missing > 0) cat(sprintf(", %d files missing", n_missing))
if (n_match == n_checked && n_loo_match == n_loo_checked) {
  cat(" — ALL OK ===\n")
} else {
  cat(" — SOME MISMATCHES ===\n")
}
cat("\nDone.\n")
