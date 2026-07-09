# ===========================================================================
# 06_coffee_certification_descriptives.R -- Sample & manipulation-check statistics
#
# Purpose: Reproduces the descriptive and manipulation-check statistics reported
#   in Web Appendix Section E for both experiments (Fair Trade, Organic): sample
#   size, mean age, gender distribution, the two scale reliabilities (Cronbach's
#   alpha for the 3-item task-involvement scale and the 4-item mood scale), and
#   the one-way ANOVAs verifying that involvement and mood do not differ across
#   the framing-length conditions. These are sample-description / manipulation-
#   check numbers (not the focal Table 2 estimates), computed deterministically
#   from the de-identified participant exports in data/.
#
# Usage: Rscript code/06_coffee_certification_descriptives.R   (run from bundle root)
# ===========================================================================

# --- Self-locate the bundle root so data/ resolves regardless of cwd -------
get_script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    path <- sub("^--file=", "", file_arg[1])
    path <- gsub("~+~", " ", path, fixed = TRUE)  # Rscript encodes spaces as ~+~
    return(dirname(normalizePath(path)))
  }
  getwd()
}
data_dir <- file.path(dirname(get_script_dir()), "data")

# --- Cronbach's raw alpha (equals psych::alpha()$total$raw_alpha; verified) -
raw_alpha <- function(items) {
  items <- items[stats::complete.cases(items), , drop = FALSE]
  k <- ncol(items)
  (k / (k - 1)) * (1 - sum(apply(items, 2, var)) / var(rowSums(items)))
}

# --- Compute + print the Web Appendix Section E statistics for one experiment
describe_experiment <- function(csv_path, label) {
  d <- read.csv(csv_path, header = TRUE, stringsAsFactors = FALSE)

  # Inclusion (mirrors the estimation sample): completed responses with a valid
  # recoded preference and a valid framing-length condition.
  d <- subset(d, Q_TerminateFlag == "Complete")
  d <- d[!duplicated(d$ResponseId), ]
  d$DVPref_Rating_1 <- as.numeric(d$DVPref_Rating_1)
  d$BaseOnLeft <- as.numeric(d$BaseOnLeft)
  d$Pref_Base_vs_Comp <- ifelse(d$BaseOnLeft == 1,
                                d$DVPref_Rating_1 - 4,
                                8 - d$DVPref_Rating_1 - 4)
  d <- subset(d, !is.na(Pref_Base_vs_Comp))
  d <- subset(d, !is.na(ComparisonCondition) & ComparisonCondition != "")

  inv <- data.frame(lapply(d[, c("Emp1_1", "emp2_1", "Involved_1")],
                           function(x) as.numeric(as.character(x))))
  mood <- data.frame(lapply(d[, c("Mood_1", "Mood_2", "Mood_3", "Mood_4")],
                            function(x) as.numeric(as.character(x))))
  d$Scenario <- as.factor(d$Scenario)
  d$Involvement <- rowMeans(inv, na.rm = TRUE)
  d$Mood <- rowMeans(mood, na.rm = TRUE)

  cat("\n========== ", label, " (Web Appendix Section E) ==========\n", sep = "")
  cat("N                              :", nrow(d), "\n")
  cat("Mean age                       :", round(mean(as.numeric(d$Age_1), na.rm = TRUE), 1), "\n")
  cat("Gender (%) [1=women 2=men 3=non-binary 4=prefer-not-say]:\n")
  print(round(prop.table(table(d$Gender)) * 100, 1))
  cat("Cronbach's alpha, involvement  :", round(raw_alpha(inv), 3), "\n")
  cat("Cronbach's alpha, mood         :", round(raw_alpha(mood), 3), "\n")
  cat("\nOne-way ANOVA: involvement ~ condition\n")
  print(summary(aov(Involvement ~ Scenario, data = d)))
  cat("One-way ANOVA: mood ~ condition\n")
  print(summary(aov(Mood ~ Scenario, data = d)))
  invisible(d)
}

describe_experiment(file.path(data_dir, "Fair_Trade_Coffee_Exp_Data_20251231.csv"),
                    "Experiment 1: Fair Trade")
describe_experiment(file.path(data_dir, "Organic_Coffee_Exp_Data_20251230.csv"),
                    "Experiment 2: Organic")
