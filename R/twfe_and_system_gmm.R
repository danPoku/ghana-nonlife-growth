# =============================================================================
# R replication of the headline TWFE models + System GMM robustness check
# Run AFTER the Python pipeline (needs data/processed/*.csv).
# Usage (from repo root):  Rscript R/twfe_and_system_gmm.R
#
# STATUS: written without access to R; untested. Step 1 should reproduce the
# Python coefficients (see outputs/tables/regressions.csv). If it does not,
# stop and investigate before trusting Step 2.
# =============================================================================

pkgs <- c("plm", "lmtest", "sandwich")
missing <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(missing)) install.packages(missing, repos = "https://cloud.r-project.org")
suppressPackageStartupMessages({ library(plm); library(lmtest); library(sandwich) })

dir.create("outputs/tables", showWarnings = FALSE, recursive = TRUE)
sink("outputs/tables/R_results.txt", split = TRUE)

# -----------------------------------------------------------------------------
# Step 1: replicate two-way FE (estimation sample already winsorised in Python)
# -----------------------------------------------------------------------------
est <- read.csv("data/processed/estimation_sample.csv")
pest <- pdata.frame(est, index = c("insurer_id", "year"))

for (y in c("LR_w", "ER_w", "CR_w")) {
  # Year effects as explicit dummies so HC1 counts them, while insurer effects
  # (nested in the insurer clusters) are not counted: the D12 convention, matching
  # Python (linearmodels, count_effects=False) and Stata xtreg/reghdfe.
  f <- as.formula(paste(y, "~ g_L1_w + RET + ln_gwp_L1 + LEV_net_L1_w + factor(year)"))
  m <- plm(f, data = pest, model = "within", effect = "individual")
  cat("\n==== TWFE (M1)", y, " | insurer-clustered SEs ====\n")
  ct <- coeftest(m, vcov = vcovHC(m, method = "arellano", type = "HC1", cluster = "group"))
  print(ct[!grepl("^factor\\(year\\)", rownames(ct)), , drop = FALSE])
}
# With this convention R's clustered SEs equal Python's (outputs/tables/regressions.csv).

# -----------------------------------------------------------------------------
# Step 2: System GMM (Blundell & Bond, 1998) as a robustness check
# -----------------------------------------------------------------------------
# Uses the full master panel so lags are available; same sample rules:
# 2015-2022 (IFRS 4), start-up years excluded, winsorised at 1st/99th pct.
pm <- read.csv("data/processed/panel_master.csv")
pm <- subset(pm, year >= 2015 & year <= 2022 & !as.logical(startup))
wins <- function(x, p = c(.01, .99)) {
  q <- quantile(x, p, na.rm = TRUE); pmin(pmax(x, q[1]), q[2])
}
for (v in c("LR", "ER", "CR", "g", "LEV_net")) pm[[v]] <- wins(pm[[v]])
pm$ln_gwp <- log(pm$gwp)
pp <- pdata.frame(pm, index = c("insurer_id", "year"))

# Specification: Y_it on Y_i,t-1, g_i,t-1, RET_it, lnGWP_i,t-1, LEV_i,t-1.
# Lagged growth treated as predetermined (GMM-instrumented with deeper lags).
# collapse = TRUE limits instrument proliferation (Roodman, 2009): with
# N = 29 insurers the instrument count must stay well below N.
for (y in c("LR", "ER", "CR")) {
  f <- as.formula(paste0(
    y, " ~ lag(", y, ", 1) + lag(g, 1) + RET + lag(ln_gwp, 1) + lag(LEV_net, 1) | ",
    "lag(", y, ", 2:3) + lag(g, 2:3) | RET + lag(ln_gwp, 1) + lag(LEV_net, 1)"))
  g <- tryCatch(
    pgmm(f, data = pp, effect = "twoways", model = "twosteps",
         transformation = "ld", collapse = TRUE),
    error = function(e) { cat("\npgmm failed for", y, ":", conditionMessage(e), "\n"); NULL })
  if (!is.null(g)) {
    cat("\n==== System GMM", y, "(two-step, Windmeijer-robust SEs) ====\n")
    print(summary(g, robust = TRUE))
    cat("Insurers:", length(unique(pm$insurer_id)),
        "-- check the instrument count in the summary stays well below this.\n")
  }
}
# Report for each model: AR(1) should reject, AR(2) should NOT reject;
# Hansen/Sargan p-value should be comfortably above 0.10 but not ~1.00
# (p near 1 signals too many instruments). If AR(2) rejects, deepen lags to 3:4.

sink()
cat("\nSaved: outputs/tables/R_results.txt\n")
