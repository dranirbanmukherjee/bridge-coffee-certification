# =============================================================================
# 05_coffee_certification_estimate.R -- Coffee Certification Estimation (Study 1)
# =============================================================================
#
# Purpose: Reproduce Table 2. Per experiment (Fair Trade and Organic, separately)
#          fit four Gaussian brms models and report the deconfounded treatment
#          effect with 95% credible intervals:
#            oracle:   Pref ~ 0 + ComparisonCondition       (preregistered indicator)
#            wc:       Pref ~ 0 + Intercept + wc_diff        (word-count control)
#            bridge_1: Pref ~ 0 + Intercept + INTN1          (BRIDGE, 1 nuisance control)
#            bridge_2: Pref ~ 0 + Intercept + INTN1 + INTN2  (BRIDGE, 2 controls)
#          Naive (pooled) is derived from the Oracle cell means with sample-size
#          weights. Using ~ 0 + Intercept avoids brms centering; controls are not
#          mean-centered, so the intercept is the deconfounded treatment effect.
#          Models are cached as .rds; re-running loads the cache.
#
# Pipeline step 5 of 5 (Coffee Certification, Study 1).
# Input:  {precomputed,output}/{ft,org}_data_with_nuisance.csv  (from step 04)
# Output: console results table + output/fitted_models_separate.RData;
#         cached fits in {precomputed,output}/models_separate/
# Usage:  Rscript code/05_coffee_certification_estimate.R
#
# =============================================================================

rm(list = ls())
gc()

library(brms)
library(cmdstanr)
library(dplyr)

# CmdStan is auto-detected by cmdstanr (e.g., installed via cmdstanr::install_cmdstan()).
# To use a specific CmdStan install, set the CMDSTAN environment variable.
cmdstan_env <- Sys.getenv("CMDSTAN")
if (nzchar(cmdstan_env)) set_cmdstan_path(cmdstan_env)

#' Count Words in a Character Vector
#'
#' @param x Character vector of text strings.
#' @return Integer vector of word counts.
#' @keywords internal
count_words <- function(x) lengths(strsplit(trimws(x), "\\s+"))

# Resolve the study/bundle root from this script's own location (code/<this>.R)
# so it runs unchanged on any machine and from any working directory.
script_dir <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) NULL)
base_dir <- if (!is.null(script_dir)) dirname(script_dir) else getwd()

# Cached model fits: prefer a shipped precomputed copy, else the working output dir.
model_dir <- file.path(base_dir, "precomputed", "models_separate")
if (!dir.exists(model_dir)) model_dir <- file.path(base_dir, "output", "models_separate")
dir.create(model_dir, showWarnings = FALSE, recursive = TRUE)

#' Resolve a step-04 data file: prefer a shipped precomputed copy, else output/.
#' @param fname Character, file name to locate.
#' @return Character path to the located file.
#' @keywords internal
resolve_data <- function(fname) {
  p <- file.path(base_dir, "precomputed", fname)
  if (file.exists(p)) p else file.path(base_dir, "output", fname)
}

brm_args <- list(
  family = gaussian(),
  backend = "cmdstanr",
  chains = 4, cores = 4, iter = 2500, warmup = 1000,
  seed = 42, silent = 2, refresh = 0
)

#' Fit a brms Model or Load from Cache
#'
#' Checks for a cached .rds file; if found, loads it. Otherwise fits the model
#' via \code{brm()} and saves the result.
#'
#' @param name Character, model identifier used for the .rds filename.
#' @param formula A brms formula object.
#' @param data Data frame passed to \code{brm()}.
#' @param brm_args List of additional arguments forwarded to \code{brm()}.
#' @param model_dir Character, directory path for cached .rds files.
#' @return A fitted brmsfit object.
#' @keywords internal
fit_or_load <- function(name, formula, data, brm_args, model_dir) {
  path <- file.path(model_dir, paste0(name, ".rds"))
  if (file.exists(path)) {
    cat(sprintf("  Loading %s from cache\n", name))
    return(readRDS(path))
  }
  cat(sprintf("  Fitting %s: %s\n", name, deparse(formula)))
  model <- do.call(brm, c(list(formula = formula, data = data), brm_args))
  saveRDS(model, path)
  model
}

##############################################
# Load Data
##############################################

#' Load and Prepare Coffee Experiment Data
#'
#' Reads CSV, filters complete cases, recodes preference ratings, computes
#' word-count controls, and sets condition factor levels.
#'
#' @param file_path Character, path to the experiment CSV file.
#' @param condition_levels Character vector of ordered condition factor levels.
#' @return Data frame with columns Pref, wc_diff, wc2_diff, Intercept, and
#'   ComparisonCondition as a factor (levels in the supplied order).
#' @keywords internal
load_data <- function(file_path, condition_levels) {
  d <- read.csv(file_path, stringsAsFactors = FALSE)
  d <- subset(d, Q_TerminateFlag == "Complete")
  d$DVPref_Rating_1 <- as.numeric(d$DVPref_Rating_1)
  d$BaseOnLeft <- as.numeric(d$BaseOnLeft)
  d$Pref <- ifelse(d$BaseOnLeft == 1, d$DVPref_Rating_1 - 4, 8 - d$DVPref_Rating_1 - 4)
  d <- subset(d, !is.na(Pref) & !is.na(ComparisonCondition) & ComparisonCondition != "")
  d$nuisance_matched <- as.logical(d$nuisance_matched)
  d <- subset(d, nuisance_matched == TRUE)
  d$ComparisonCondition <- factor(d$ComparisonCondition, levels = condition_levels)
  d$wc_base <- count_words(d$Text_Base)
  d$wc_comparison <- count_words(d$Text_Comparison)
  d$wc_diff <- d$wc_comparison - d$wc_base
  d$wc2_diff <- d$wc_comparison^2 - d$wc_base^2
  d$Intercept <- 1
  d
}

cat("\n========== LOADING DATA ==========\n\n")

data_ft <- load_data(
  resolve_data("ft_data_with_nuisance.csv"),
  c("BaseFT", "ShortFT", "LongFT")
)
data_org <- load_data(
  resolve_data("org_data_with_nuisance.csv"),
  c("BaseOrganic", "ShortOrganic", "LongOrganic")
)

cat("FT N =", nrow(data_ft), "\n")
cat("Org N =", nrow(data_org), "\n")

##############################################
# Control variable means
##############################################

cat("\n========== CONTROL VARIABLE MEANS (not centered) ==========\n\n")

#' Report Control Variable Means to Console
#'
#' Prints mean values of wc_diff, wc2_diff, and all INTN columns.
#'
#' @param d Data frame with control variable columns.
#' @param label Character, experiment label for display (e.g. "FT", "Org").
#' @keywords internal
report_means <- function(d, label) {
  cat(sprintf("  %s wc_diff: mean=%.4f\n", label, mean(d$wc_diff)))
  cat(sprintf("  %s wc2_diff: mean=%.4f\n", label, mean(d$wc2_diff)))
  intn_cols <- grep("^INTN[0-9]+$", names(d), value = TRUE)
  for (col in intn_cols) {
    cat(sprintf("  %s %s: mean=%.6f\n", label, col, mean(d[[col]])))
  }
}

report_means(data_ft, "FT")
report_means(data_org, "Org")

##############################################
# Estimate all models
##############################################

cat("\n========== ESTIMATING MODELS ==========\n\n")

#' Fit All Four Models for One Experiment
#'
#' Fits oracle, word-count, and BRIDGE (1 and 2 control)
#' models, caching each as .rds.
#'
#' @param data Data frame from \code{load_data()}.
#' @param prefix Character, experiment prefix for filenames (e.g. "FT", "Org").
#' @param brm_args List of brms fitting arguments.
#' @param model_dir Character, directory for cached .rds files.
#' @return Named list of four fitted brmsfit objects.
#' @keywords internal
fit_experiment <- function(data, prefix, brm_args, model_dir) {
  intn_cols <- grep("^INTN[0-9]+$", names(data), value = TRUE)
  cat(sprintf("Available INTN columns: %d\n\n", length(intn_cols)))

  m <- list()
  m$oracle   <- fit_or_load(paste0(prefix, "_oracle"),
                             Pref ~ 0 + ComparisonCondition, data, brm_args, model_dir)
  m$wc       <- fit_or_load(paste0(prefix, "_wc"),
                             Pref ~ 0 + Intercept + wc_diff, data, brm_args, model_dir)
  m$bridge_1 <- fit_or_load(paste0(prefix, "_bridge_1"),
                             Pref ~ 0 + Intercept + INTN1, data, brm_args, model_dir)
  m$bridge_2 <- fit_or_load(paste0(prefix, "_bridge_2"),
                             Pref ~ 0 + Intercept + INTN1 + INTN2, data, brm_args, model_dir)
  m
}

cat("--- Fair Trade ---\n")
print(table(data_ft$ComparisonCondition))
ft_m <- fit_experiment(data_ft, "FT", brm_args, model_dir)

cat("\n--- Organic ---\n")
print(table(data_org$ComparisonCondition))
org_m <- fit_experiment(data_org, "Org", brm_args, model_dir)

cat("\nAll models estimated/loaded.\n")

##############################################
# Helpers
##############################################

#' Derive Cell-Mean and Pooled Posterior Draws from Oracle Model
#'
#' Extracts posterior draws for each condition and computes the sample-size
#' weighted pooled estimate (naive unconditional average).
#'
#' @param model A fitted brmsfit oracle model (Pref ~ 0 + ComparisonCondition).
#' @param data Data frame with ComparisonCondition factor.
#' @return Named list with elements \code{matched}, \code{short}, \code{long},
#'   and \code{pooled}, each a numeric vector of posterior draws.
#' @keywords internal
oracle_derived <- function(model, data) {
  draws <- as_draws_matrix(model)
  cond_levels <- levels(data$ComparisonCondition)
  cond_n <- table(data$ComparisonCondition)

  base_col  <- paste0("b_ComparisonCondition", cond_levels[grepl("Base", cond_levels)])
  short_col <- paste0("b_ComparisonCondition", cond_levels[grepl("Short", cond_levels)])
  long_col  <- paste0("b_ComparisonCondition", cond_levels[grepl("Long", cond_levels)])

  d_base  <- draws[, base_col]
  d_short <- draws[, short_col]
  d_long  <- draws[, long_col]
  d_pooled <- (d_base * cond_n[1] + d_short * cond_n[2] + d_long * cond_n[3]) / sum(cond_n)

  list(matched = d_base, short = d_short, long = d_long, pooled = d_pooled)
}

#' Extract Intercept Posterior Draws
#'
#' @param m A fitted brmsfit object.
#' @return Numeric vector of posterior draws for the intercept.
#' @keywords internal
get_int <- function(m) as_draws_matrix(m)[, "b_Intercept"]

#' Format Posterior Summary with Label
#'
#' @param x Numeric vector of posterior draws.
#' @param label Character, row label for display.
#' @return Character string: "label  mean [2.5%, 97.5%]".
#' @keywords internal
pfmt <- function(x, label) {
  sprintf("    %-25s %.3f [%.3f, %.3f]", label, mean(x),
          quantile(x, 0.025), quantile(x, 0.975))
}

#' Format Posterior Summary (No Label)
#'
#' @param x Numeric vector of posterior draws.
#' @return Character string: "mean [2.5%, 97.5%]".
#' @keywords internal
pfmt2 <- function(x) {
  sprintf("%.3f [%.3f, %.3f]", mean(x), quantile(x, 0.025), quantile(x, 0.975))
}

#' Format a Summary Table Row for FT and Org
#'
#' @param label Character, estimator name.
#' @param ft_draws Numeric vector of FT posterior draws.
#' @param org_draws Numeric vector of Org posterior draws.
#' @return Character string with label, FT summary, and Org summary.
#' @keywords internal
make_row <- function(label, ft_draws, org_draws) {
  sprintf("%-25s  %s  |  %s", label, pfmt2(ft_draws), pfmt2(org_draws))
}

##############################################
# Results
##############################################

sep <- paste(rep("=", 70), collapse = "")
cat(sprintf("\n\n%s\n", sep))
cat("  RESULTS [GAUSSIAN]\n")
cat(sprintf("%s\n\n", sep))

# Fixed effects
for (exp_label in c("FT", "Org")) {
  m_list <- if (exp_label == "FT") ft_m else org_m
  cat(sprintf("--- %s ---\n\n", exp_label))
  for (mname in names(m_list)) {
    cat(sprintf("  %s:\n", mname))
    print(round(fixef(m_list[[mname]]), 3))
    cat("\n")
  }
}

# Oracle-derived cell means and pooled
ft_oracle <- oracle_derived(ft_m$oracle, data_ft)
org_oracle <- oracle_derived(org_m$oracle, data_org)

cat("\nOracle cell means (FT):\n")
cat(pfmt(ft_oracle$matched, "Matched (benchmark)"), "\n")
cat(pfmt(ft_oracle$short, "Short"), "\n")
cat(pfmt(ft_oracle$long, "Long"), "\n")
cat(pfmt(ft_oracle$pooled, "Pooled (derived)"), "\n")

cat("\nOracle cell means (Org):\n")
cat(pfmt(org_oracle$matched, "Matched (benchmark)"), "\n")
cat(pfmt(org_oracle$short, "Short"), "\n")
cat(pfmt(org_oracle$long, "Long"), "\n")
cat(pfmt(org_oracle$pooled, "Pooled (derived)"), "\n")

# Diagnostic
cat(sprintf("\n  Diagnostic: FT sample mean = %.3f (oracle pooled = %.3f)\n",
            mean(data_ft$Pref), mean(ft_oracle$pooled)))
cat(sprintf("  Diagnostic: Org sample mean = %.3f (oracle pooled = %.3f)\n",
            mean(data_org$Pref), mean(org_oracle$pooled)))

# Summary table
cat("\n========== SUMMARY TABLE ==========\n\n")
cat(sprintf("%-25s  %-25s  |  %-25s\n", "Estimator", "FT [95% CI]", "Org [95% CI]"))
cat(paste(rep("-", 85), collapse = ""), "\n")
cat(make_row("Oracle (matched)", ft_oracle$matched, org_oracle$matched), "\n")
cat(make_row("Oracle (short)", ft_oracle$short, org_oracle$short), "\n")
cat(make_row("Oracle (long)", ft_oracle$long, org_oracle$long), "\n")
cat(make_row("Naive (pooled)", ft_oracle$pooled, org_oracle$pooled), "\n")
cat(make_row("Word Count", get_int(ft_m$wc), get_int(org_m$wc)), "\n")
cat(make_row("BRIDGE (1 ctrl)", get_int(ft_m$bridge_1), get_int(org_m$bridge_1)), "\n")
cat(make_row("BRIDGE (2 ctrl)", get_int(ft_m$bridge_2), get_int(org_m$bridge_2)), "\n")

# LOOIC
cat("\n  LOOIC:\n")
for (exp_label in c("FT", "Org")) {
  m_list <- if (exp_label == "FT") ft_m else org_m
  cat(sprintf("    %s:\n", exp_label))
  for (bname in c("bridge_1", "bridge_2")) {
    lr <- tryCatch(loo(m_list[[bname]]), error = function(e) {
      cat(sprintf("      %s: [loo failed: %s]\n", bname, e$message)); NULL
    })
    if (!is.null(lr)) {
      val <- lr$estimates["looic", "Estimate"]
      cat(sprintf("      %s: %.1f\n", bname, val))
    }
  }
}

# Convergence
cat("\n  Convergence:\n")
for (exp_label in c("FT", "Org")) {
  m_list <- if (exp_label == "FT") ft_m else org_m
  cat(sprintf("    %s:\n", exp_label))
  for (mname in names(m_list)) {
    s <- summary(m_list[[mname]])
    rhat <- max(s$fixed$Rhat, na.rm = TRUE)
    ess <- min(s$fixed$Bulk_ESS, na.rm = TRUE)
    cat(sprintf("      %-15s Rhat=%.3f  ESS=%d\n", mname, rhat, round(ess)))
  }
}

##############################################
# Posterior Differences (delta)
##############################################

cat("\n========== POSTERIOR DIFFERENCES ==========\n\n")

#' Print Posterior Difference Between Two Sets of Draws
#'
#' @param draws_a Numeric vector of posterior draws (minuend).
#' @param draws_b Numeric vector of posterior draws (subtrahend).
#' @param label Character, description of the comparison.
#' @keywords internal
post_diff <- function(draws_a, draws_b, label) {
  delta <- draws_a - draws_b
  cat(sprintf("  %-45s  delta = %.3f [%.3f, %.3f]\n", label,
              mean(delta), quantile(delta, 0.025), quantile(delta, 0.975)))
}

# BRIDGE vs Oracle matched
post_diff(get_int(ft_m$bridge_1), ft_oracle$matched,
          "FT: BRIDGE(1) - Oracle(matched)")
post_diff(get_int(org_m$bridge_1), org_oracle$matched,
          "Org: BRIDGE(1) - Oracle(matched)")

# WC vs Oracle matched (overcorrection)
post_diff(get_int(ft_m$wc), ft_oracle$matched,
          "FT: WC - Oracle(matched)")
post_diff(get_int(org_m$wc), org_oracle$matched,
          "Org: WC - Oracle(matched)")

##############################################
# Condition-Specific WC Estimates
##############################################

cat("\n========== CONDITION-SPECIFIC WC ESTIMATES ==========\n\n")

#' Print Condition-Specific Word-Count Regression Predictions
#'
#' For each condition level, computes the predicted preference at the
#' condition's mean wc_diff value.
#'
#' @param model A fitted brmsfit word-count model (Pref ~ 0 + Intercept + wc_diff).
#' @param data Data frame with ComparisonCondition factor and wc_diff column.
#' @param label Character, experiment label for display.
#' @keywords internal
wc_cond_estimates <- function(model, data, label) {
  draws <- as_draws_matrix(model)
  int_draws <- draws[, "b_Intercept"]
  slope_draws <- draws[, "b_wc_diff"]

  cond_levels <- levels(data$ComparisonCondition)
  wc_means <- tapply(data$wc_diff, data$ComparisonCondition, mean)

  cat(sprintf("  %s  (slope on wc_diff: %.4f [%.4f, %.4f]):\n", label,
              mean(slope_draws), quantile(slope_draws, 0.025),
              quantile(slope_draws, 0.975)))

  for (cond in cond_levels) {
    dwc <- wc_means[cond]
    pred <- int_draws + slope_draws * dwc
    cat(sprintf("    %-25s  %.3f [%.3f, %.3f]  (dwc = %.1f)\n",
                cond, mean(pred), quantile(pred, 0.025),
                quantile(pred, 0.975), dwc))
  }
  cat("\n")
}

wc_cond_estimates(ft_m$wc, data_ft, "FT")
wc_cond_estimates(org_m$wc, data_org, "Org")

##############################################
# Nuisance Control Correlations with wc_diff
##############################################

cat("\n========== NUISANCE CONTROL CORRELATIONS ==========\n\n")

for (exp_label in c("FT", "Org")) {
  d <- if (exp_label == "FT") data_ft else data_org
  intn_cols <- grep("^INTN[0-9]+$", names(d), value = TRUE)
  cat(sprintf("  %s (N=%d):\n", exp_label, nrow(d)))
  for (col in intn_cols) {
    r <- cor(d[[col]], d$wc_diff)
    cat(sprintf("    cor(%s, wc_diff) = %.4f\n", col, r))
  }
  cat("\n")
}

##############################################
# Save
##############################################

save(ft_m, org_m, data_ft, data_org,
     file = file.path(base_dir, "output/fitted_models_separate.RData"))

cat("\n========== SEPARATE ESTIMATION COMPLETE ==========\n")
