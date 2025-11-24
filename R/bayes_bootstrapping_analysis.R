# =============================================================================
# Bayesian Bootstrapping Analysis - Social Media & Psychological Distress
# =============================================================================
# Rubin (1981) tarafindan gelistirilen Bayesian Bootstrap yontemi
# Dirichlet dagilimi kullanilarak agirliklarin olusturulmasi

# Gerekli paketlerin yuklenmesi
required_packages <- c("bayesboot", "dplyr", "tidyr", "psych", "ggplot2",
                       "coda", "HDInterval", "corrplot")

install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org/")
  }
}

lapply(required_packages, install_if_missing)

# Paketleri yukle
library(bayesboot)
library(dplyr)
library(tidyr)
library(psych)
library(ggplot2)
library(coda)
library(HDInterval)
library(corrplot)

# =============================================================================
# ASAMA 1: VERI YUKLEME VE HAZIRLAMA
# =============================================================================

# Veriyi oku
data_path <- "data/modeldata.csv"
df <- read.csv(data_path, sep = ";", header = TRUE,
               stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# Degisken isimlerini temizle
names(df) <- gsub("\\s+", "", names(df))
names(df) <- gsub("\\.", "", names(df))

cat("\n=== VERI YUKLENDI ===\n")
cat("Satir sayisi:", nrow(df), "\n")

# =============================================================================
# ASAMA 2: ALT OLCEK PUANLARININ HESAPLANMASI
# =============================================================================

# DASS-21 alt olcekleri
depression_items <- c("DAS3", "DAS5", "DAS10", "DAS13", "DAS16", "DAS17", "DAS21")
anxiety_items <- c("DAS2", "DAS4", "DAS7", "DAS9", "DAS15", "DAS19", "DAS20")
stress_items <- c("DAS1", "DAS6", "DAS8", "DAS11", "DAS12", "DAS14", "DAS18")

# Shame and Guilt Scale
shame_items <- c("SC1", "SC3", "SC5", "SC7", "SC9")
guilt_items <- c("SC2", "SC4", "SC6", "SC8", "SC10")

# Self-Compassion Scale
self_compassion_items <- paste0("GS", 1:10)

# Bergen Social Media Addiction Scale
bergen_items <- paste0("BERGEN", 1:6)

# Social Support Scale
family_support_items <- c("SOS1", "SOS2", "SOS3", "SOS4")
friend_support_items <- c("SOS5", "SOS6", "SOS7", "SOS8")

# Cyber Victimization
cyber_victim_items <- paste0("CW", 1:10)

# Alt olcek puanlarini hesapla
calculate_subscale <- function(data, items) {
  existing_items <- items[items %in% names(data)]
  if (length(existing_items) == 0) {
    return(rep(NA, nrow(data)))
  }
  subset_data <- data[, existing_items, drop = FALSE]
  subset_data <- apply(subset_data, 2, as.numeric)
  rowMeans(subset_data, na.rm = TRUE)
}

# Alt olcekleri hesapla
df$Depression <- calculate_subscale(df, depression_items)
df$Anxiety <- calculate_subscale(df, anxiety_items)
df$Stress <- calculate_subscale(df, stress_items)
df$Shame <- calculate_subscale(df, shame_items)
df$Guilt <- calculate_subscale(df, guilt_items)
df$SelfCompassion <- calculate_subscale(df, self_compassion_items)
df$SocialMediaAddiction <- calculate_subscale(df, bergen_items)
df$FamilySupport <- calculate_subscale(df, family_support_items)
df$FriendSupport <- calculate_subscale(df, friend_support_items)
df$CyberVictimization <- calculate_subscale(df, cyber_victim_items)
df$SocialMediaTime <- as.numeric(df$TİMESOCİAL)

# Analiz icin degiskenler
analysis_vars <- c("Depression", "Anxiety", "Stress", "Shame", "Guilt",
                   "SelfCompassion", "SocialMediaAddiction",
                   "FamilySupport", "FriendSupport", "CyberVictimization")

# Tam veri seti
analysis_data <- df[, analysis_vars]
analysis_data <- na.omit(analysis_data)

cat("Analiz icin kullanilan gozlem sayisi:", nrow(analysis_data), "\n")

# =============================================================================
# ASAMA 3: BAYESIAN BOOTSTRAP - ORTALAMALAR
# =============================================================================

cat("\n=== BAYESIAN BOOTSTRAP: ORTALAMALAR ===\n")

set.seed(42)
n_iterations <- 4000

# Her degisken icin Bayesian bootstrap
bb_means_results <- list()

for (var in analysis_vars) {
  cat("\nAnaliz ediliyor:", var, "\n")

  # Bayesian bootstrap
  bb_result <- bayesboot(analysis_data[[var]],
                         statistic = mean,
                         R = n_iterations,
                         use.weights = FALSE)

  # Sonuclari kaydet
  bb_means_results[[var]] <- list(
    mean = mean(bb_result$V1),
    sd = sd(bb_result$V1),
    ci_lower = quantile(bb_result$V1, 0.025),
    ci_upper = quantile(bb_result$V1, 0.975),
    hdi_lower = hdi(bb_result$V1)[1],
    hdi_upper = hdi(bb_result$V1)[2],
    samples = bb_result$V1
  )

  cat("  Ortalama:", round(bb_means_results[[var]]$mean, 3), "\n")
  cat("  SD:", round(bb_means_results[[var]]$sd, 3), "\n")
  cat("  95% CI: [", round(bb_means_results[[var]]$ci_lower, 3), ", ",
      round(bb_means_results[[var]]$ci_upper, 3), "]\n")
  cat("  95% HDI: [", round(bb_means_results[[var]]$hdi_lower, 3), ", ",
      round(bb_means_results[[var]]$hdi_upper, 3), "]\n")
}

# =============================================================================
# ASAMA 4: BAYESIAN BOOTSTRAP - KORELASYONLAR
# =============================================================================

cat("\n=== BAYESIAN BOOTSTRAP: KORELASYONLAR ===\n")

# Korelasyon fonksiyonu
weighted_cor <- function(x, y, w = NULL) {
  if (is.null(w)) {
    return(cor(x, y))
  }
  w <- w / sum(w)
  mx <- sum(w * x)
  my <- sum(w * y)
  cov_xy <- sum(w * (x - mx) * (y - my))
  sd_x <- sqrt(sum(w * (x - mx)^2))
  sd_y <- sqrt(sum(w * (y - my)^2))
  cov_xy / (sd_x * sd_y)
}

# Tum degisken ciftleri icin Bayesian bootstrap korelasyonlar
var_pairs <- combn(analysis_vars, 2, simplify = FALSE)
bb_cor_results <- list()

cat("\nToplam", length(var_pairs), "korelasyon hesaplaniyor...\n")

for (i in seq_along(var_pairs)) {
  var1 <- var_pairs[[i]][1]
  var2 <- var_pairs[[i]][2]
  pair_name <- paste(var1, var2, sep = "_")

  # Dirichlet agirliklarla bootstrap
  cor_samples <- numeric(n_iterations)
  n <- nrow(analysis_data)

  for (j in 1:n_iterations) {
    # Dirichlet(1,1,...,1) dagiliminden agirliklari cek
    weights <- rgamma(n, 1, 1)
    weights <- weights / sum(weights)

    # Agirlikli korelasyon
    cor_samples[j] <- weighted_cor(analysis_data[[var1]],
                                    analysis_data[[var2]],
                                    weights)
  }

  bb_cor_results[[pair_name]] <- list(
    var1 = var1,
    var2 = var2,
    mean = mean(cor_samples),
    sd = sd(cor_samples),
    ci_lower = quantile(cor_samples, 0.025),
    ci_upper = quantile(cor_samples, 0.975),
    hdi_lower = hdi(cor_samples)[1],
    hdi_upper = hdi(cor_samples)[2],
    prob_positive = mean(cor_samples > 0),
    prob_negative = mean(cor_samples < 0),
    samples = cor_samples
  )

  if (i %% 10 == 0) {
    cat("  Tamamlanan:", i, "/", length(var_pairs), "\n")
  }
}

# =============================================================================
# ASAMA 5: BAYESIAN BOOTSTRAP - REGRESYON KATSAYILARI
# =============================================================================

cat("\n=== BAYESIAN BOOTSTRAP: REGRESYON ANALIZI ===\n")
cat("Bagimli degisken: Depression\n")

# Depression'u yordayan model
predictors <- c("Anxiety", "Stress", "Shame", "Guilt", "SelfCompassion",
                "SocialMediaAddiction", "CyberVictimization")

# Weighted regression fonksiyonu
weighted_lm_coef <- function(data, weights = NULL) {
  if (is.null(weights)) {
    weights <- rep(1, nrow(data))
  }

  formula <- as.formula(paste("Depression ~", paste(predictors, collapse = " + ")))
  model <- lm(formula, data = data, weights = weights)
  coef(model)
}

# Bayesian bootstrap regresyon
reg_samples <- matrix(NA, nrow = n_iterations, ncol = length(predictors) + 1)
colnames(reg_samples) <- c("Intercept", predictors)

n <- nrow(analysis_data)

cat("Regresyon katsayilari hesaplaniyor...\n")
for (j in 1:n_iterations) {
  # Dirichlet agirliklari
  weights <- rgamma(n, 1, 1)
  weights <- weights / sum(weights) * n  # Scale weights

  reg_samples[j, ] <- weighted_lm_coef(analysis_data, weights)

  if (j %% 500 == 0) {
    cat("  Iterasyon:", j, "/", n_iterations, "\n")
  }
}

# Regresyon sonuclari
bb_reg_results <- list()
for (var in colnames(reg_samples)) {
  samples <- reg_samples[, var]
  bb_reg_results[[var]] <- list(
    mean = mean(samples),
    sd = sd(samples),
    ci_lower = quantile(samples, 0.025),
    ci_upper = quantile(samples, 0.975),
    hdi_lower = hdi(samples)[1],
    hdi_upper = hdi(samples)[2],
    prob_positive = mean(samples > 0),
    prob_negative = mean(samples < 0)
  )
}

cat("\nRegresyon Katsayilari (Bayesian Bootstrap):\n")
cat("-" , rep("-", 70), "\n", sep = "")
cat(sprintf("%-20s %8s %8s %10s %10s %10s\n",
            "Degisken", "Mean", "SD", "CI_Lower", "CI_Upper", "P(b>0)"))
cat("-", rep("-", 70), "\n", sep = "")

for (var in names(bb_reg_results)) {
  res <- bb_reg_results[[var]]
  cat(sprintf("%-20s %8.3f %8.3f %10.3f %10.3f %10.3f\n",
              var, res$mean, res$sd, res$ci_lower, res$ci_upper, res$prob_positive))
}

# =============================================================================
# ASAMA 6: SONUCLARIN KAYDEDILMESI
# =============================================================================

cat("\n=== SONUCLAR KAYDEDILIYOR ===\n")

# 1. Ortalamalar tablosu
means_df <- data.frame(
  Variable = names(bb_means_results),
  Mean = sapply(bb_means_results, function(x) x$mean),
  SD = sapply(bb_means_results, function(x) x$sd),
  CI_Lower = sapply(bb_means_results, function(x) x$ci_lower),
  CI_Upper = sapply(bb_means_results, function(x) x$ci_upper),
  HDI_Lower = sapply(bb_means_results, function(x) x$hdi_lower),
  HDI_Upper = sapply(bb_means_results, function(x) x$hdi_upper),
  row.names = NULL
)
write.csv(means_df, "data/bayes_bootstrap_means.csv", row.names = FALSE)
cat("Kaydedildi: data/bayes_bootstrap_means.csv\n")

# 2. Korelasyonlar tablosu
cor_df <- data.frame(
  Variable1 = sapply(bb_cor_results, function(x) x$var1),
  Variable2 = sapply(bb_cor_results, function(x) x$var2),
  Correlation = sapply(bb_cor_results, function(x) x$mean),
  SD = sapply(bb_cor_results, function(x) x$sd),
  CI_Lower = sapply(bb_cor_results, function(x) x$ci_lower),
  CI_Upper = sapply(bb_cor_results, function(x) x$ci_upper),
  HDI_Lower = sapply(bb_cor_results, function(x) x$hdi_lower),
  HDI_Upper = sapply(bb_cor_results, function(x) x$hdi_upper),
  Prob_Positive = sapply(bb_cor_results, function(x) x$prob_positive),
  Prob_Negative = sapply(bb_cor_results, function(x) x$prob_negative),
  row.names = NULL
)
write.csv(cor_df, "data/bayes_bootstrap_correlations.csv", row.names = FALSE)
cat("Kaydedildi: data/bayes_bootstrap_correlations.csv\n")

# 3. Regresyon katsayilari tablosu
reg_df <- data.frame(
  Predictor = names(bb_reg_results),
  Coefficient = sapply(bb_reg_results, function(x) x$mean),
  SD = sapply(bb_reg_results, function(x) x$sd),
  CI_Lower = sapply(bb_reg_results, function(x) x$ci_lower),
  CI_Upper = sapply(bb_reg_results, function(x) x$ci_upper),
  HDI_Lower = sapply(bb_reg_results, function(x) x$hdi_lower),
  HDI_Upper = sapply(bb_reg_results, function(x) x$hdi_upper),
  Prob_Positive = sapply(bb_reg_results, function(x) x$prob_positive),
  Prob_Negative = sapply(bb_reg_results, function(x) x$prob_negative),
  row.names = NULL
)
write.csv(reg_df, "data/bayes_bootstrap_regression.csv", row.names = FALSE)
cat("Kaydedildi: data/bayes_bootstrap_regression.csv\n")

# =============================================================================
# ASAMA 7: GORSELLESTIRME
# =============================================================================

cat("\n=== GRAFIKLER OLUSTURULUYOR ===\n")

# 1. Posterior dagilimlar - Ortalamalar
pdf("data/bayes_bootstrap_means_plot.pdf", width = 14, height = 10)
par(mfrow = c(3, 4))
for (var in names(bb_means_results)) {
  hist(bb_means_results[[var]]$samples,
       main = var,
       xlab = "Ortalama",
       col = "steelblue",
       border = "white",
       breaks = 40)
  abline(v = bb_means_results[[var]]$mean, col = "red", lwd = 2)
  abline(v = c(bb_means_results[[var]]$ci_lower,
               bb_means_results[[var]]$ci_upper),
         col = "red", lwd = 1, lty = 2)
}
dev.off()
cat("Kaydedildi: data/bayes_bootstrap_means_plot.pdf\n")

# 2. Regresyon katsayilari grafiği
pdf("data/bayes_bootstrap_regression_plot.pdf", width = 12, height = 8)
par(mfrow = c(2, 4))
for (var in predictors) {
  samples <- reg_samples[, var]
  hist(samples,
       main = var,
       xlab = "Katsayi",
       col = ifelse(mean(samples) > 0, "darkgreen", "darkred"),
       border = "white",
       breaks = 40)
  abline(v = 0, col = "black", lwd = 2)
  abline(v = mean(samples), col = "blue", lwd = 2)
  abline(v = quantile(samples, c(0.025, 0.975)), col = "blue", lty = 2)
}
dev.off()
cat("Kaydedildi: data/bayes_bootstrap_regression_plot.pdf\n")

# 3. Forest plot - Regresyon
pdf("data/bayes_bootstrap_forest_plot.pdf", width = 10, height = 8)
reg_plot_df <- reg_df[reg_df$Predictor != "Intercept", ]
reg_plot_df$Predictor <- factor(reg_plot_df$Predictor,
                                 levels = rev(reg_plot_df$Predictor))

plot(reg_plot_df$Coefficient, 1:nrow(reg_plot_df),
     xlim = range(c(reg_plot_df$CI_Lower, reg_plot_df$CI_Upper)),
     ylim = c(0.5, nrow(reg_plot_df) + 0.5),
     pch = 19, cex = 1.5,
     xlab = "Regression Coefficient (95% CI)",
     ylab = "",
     yaxt = "n",
     main = "Bayesian Bootstrap Regression Coefficients\n(Predicting Depression)")

axis(2, at = 1:nrow(reg_plot_df), labels = reg_plot_df$Predictor, las = 1)
abline(v = 0, lty = 2, col = "gray50")

segments(reg_plot_df$CI_Lower, 1:nrow(reg_plot_df),
         reg_plot_df$CI_Upper, 1:nrow(reg_plot_df),
         lwd = 2)

points(reg_plot_df$Coefficient, 1:nrow(reg_plot_df),
       pch = 19, cex = 1.5,
       col = ifelse(reg_plot_df$CI_Lower > 0 | reg_plot_df$CI_Upper < 0,
                    "darkblue", "gray50"))
dev.off()
cat("Kaydedildi: data/bayes_bootstrap_forest_plot.pdf\n")

# =============================================================================
# ASAMA 8: OZET RAPOR
# =============================================================================

cat("\n")
cat("=" , rep("=", 70), "\n", sep = "")
cat("BAYESIAN BOOTSTRAPPING ANALIZI - OZET\n")
cat("=", rep("=", 70), "\n", sep = "")

cat("\nYontem: Rubin (1981) Bayesian Bootstrap\n")
cat("Iterasyon sayisi:", n_iterations, "\n")
cat("Gozlem sayisi:", nrow(analysis_data), "\n")

cat("\n--- EN GUCLU KORELASYONLAR ---\n")
cor_df_sorted <- cor_df[order(abs(cor_df$Correlation), decreasing = TRUE), ]
print(head(cor_df_sorted[, c("Variable1", "Variable2", "Correlation",
                              "CI_Lower", "CI_Upper")], 10))

cat("\n--- ANLAMLI REGRESYON KATSAYILARI ---\n")
cat("(CI sifiri icermeyenler)\n")
sig_reg <- reg_df[reg_df$Predictor != "Intercept" &
                   (reg_df$CI_Lower > 0 | reg_df$CI_Upper < 0), ]
print(sig_reg[, c("Predictor", "Coefficient", "CI_Lower", "CI_Upper", "Prob_Positive")])

cat("\n=== ANALIZ TAMAMLANDI ===\n")
cat("\nOlusturulan dosyalar:\n")
cat("  - data/bayes_bootstrap_means.csv\n")
cat("  - data/bayes_bootstrap_correlations.csv\n")
cat("  - data/bayes_bootstrap_regression.csv\n")
cat("  - data/bayes_bootstrap_means_plot.pdf\n")
cat("  - data/bayes_bootstrap_regression_plot.pdf\n")
cat("  - data/bayes_bootstrap_forest_plot.pdf\n")
