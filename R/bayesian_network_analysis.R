# =============================================================================
# Bayesian Network Analysis - Social Media & Psychological Distress
# =============================================================================

# Gerekli paketlerin yuklenmesi
required_packages <- c("bnlearn", "qgraph", "dplyr", "tidyr", "psych",
                       "mice", "corrplot", "ggplot2", "Rgraphviz")

install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org/")
  }
}

lapply(required_packages, install_if_missing)

# Paketleri yukle
library(bnlearn)
library(qgraph)
library(dplyr)
library(tidyr)
library(psych)
library(mice)
library(corrplot)
library(ggplot2)

# =============================================================================
# ASAMA 1: VERI YUKLEME VE TEMIZLEME
# =============================================================================

# Veriyi oku (noktalı virgul ile ayrilmis)
data_path <- "data/modeldata.csv"
df <- read.csv(data_path, sep = ";", header = TRUE,
               stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# Degisken isimlerini temizle
names(df) <- gsub("\\s+", "", names(df))  # Bosluklari kaldir
names(df) <- gsub("\\.", "", names(df))   # Noktalari kaldir

# Veri yapisini incele
cat("\n=== VERI YAPISI ===\n")
cat("Satir sayisi:", nrow(df), "\n")
cat("Sutun sayisi:", ncol(df), "\n")
cat("\nDegisken isimleri:\n")
print(names(df))

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

# Alt olcek puanlarini hesapla (ortalama)
calculate_subscale <- function(data, items) {
  # Degiskenlerin var olup olmadigini kontrol et
  existing_items <- items[items %in% names(data)]
  if (length(existing_items) == 0) {
    warning(paste("Degiskenler bulunamadi:", paste(items, collapse = ", ")))
    return(rep(NA, nrow(data)))
  }
  # Sayisal degerlere donustur
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

# Sosyal medya kullanim suresi
df$SocialMediaTime <- as.numeric(df$TİMESOCİAL)

# Cinsiyet kodlamasi
df$Gender <- ifelse(df$gender == "Erkek", 0, 1)  # 0 = Erkek, 1 = Kadin

# Yas
df$Age <- as.numeric(df$age)

# =============================================================================
# ASAMA 3: NETWORK ANALIZI ICIN VERI SECIMI
# =============================================================================

# Network icin kullanilacak degiskenler
network_vars <- c("Depression", "Anxiety", "Stress",
                  "Shame", "Guilt", "SelfCompassion",
                  "SocialMediaAddiction", "FamilySupport", "FriendSupport",
                  "CyberVictimization", "SocialMediaTime", "Age")

# Network verisini olustur
network_data <- df[, network_vars]

# Eksik verileri kontrol et
cat("\n=== EKSIK VERI ANALIZI ===\n")
missing_summary <- sapply(network_data, function(x) sum(is.na(x)))
print(missing_summary)
cat("\nToplam eksik veri orani:",
    round(sum(is.na(network_data)) / (nrow(network_data) * ncol(network_data)) * 100, 2), "%\n")

# Eksik verileri listwise deletion ile kaldir (veya imputation yapilabilir)
network_data_complete <- na.omit(network_data)
cat("\nTam veri ile kalan gozlem sayisi:", nrow(network_data_complete), "\n")

# =============================================================================
# ASAMA 4: BETIMSEL ISTATISTIKLER
# =============================================================================

cat("\n=== BETIMSEL ISTATISTIKLER ===\n")
descriptives <- psych::describe(network_data_complete)
print(round(descriptives, 2))

# Korelasyon matrisi
cat("\n=== KORELASYON MATRISI ===\n")
cor_matrix <- cor(network_data_complete, use = "complete.obs")
print(round(cor_matrix, 2))

# Korelasyon gorsellestirmesi
pdf("data/correlation_plot.pdf", width = 12, height = 10)
corrplot(cor_matrix, method = "color", type = "upper",
         tl.col = "black", tl.srt = 45,
         addCoef.col = "black", number.cex = 0.7,
         title = "Korelasyon Matrisi")
dev.off()
cat("\nKorelasyon grafigi kaydedildi: data/correlation_plot.pdf\n")

# =============================================================================
# ASAMA 5: BAYESIAN NETWORK YAPI OGRENIMI
# =============================================================================

cat("\n=== BAYESIAN NETWORK ANALIZI ===\n")

# Veriyi sayisal matrise donustur
bn_data <- as.data.frame(lapply(network_data_complete, as.numeric))

# Yontem 1: Hill-Climbing Algorithm
cat("\n--- Hill-Climbing Algorithm ---\n")
bn_hc <- hc(bn_data, score = "bic-g")
cat("Ogrenen yapi (Hill-Climbing):\n")
print(bn_hc)

# Yontem 2: PC Algorithm (Constraint-based)
cat("\n--- PC Algorithm ---\n")
bn_pc <- pc.stable(bn_data, alpha = 0.05)
cat("Ogrenen yapi (PC):\n")
print(bn_pc)

# Yontem 3: TABU Search
cat("\n--- TABU Search ---\n")
bn_tabu <- tabu(bn_data, score = "bic-g")
cat("Ogrenen yapi (TABU):\n")
print(bn_tabu)

# Model karsilastirma (BIC skorlari)
cat("\n=== MODEL KARSILASTIRMA ===\n")
cat("Hill-Climbing BIC:", score(bn_hc, bn_data, type = "bic-g"), "\n")
cat("TABU Search BIC:", score(bn_tabu, bn_data, type = "bic-g"), "\n")

# En iyi modeli sec (dusuk BIC daha iyi)
best_bn <- bn_hc  # Hill-climbing genellikle iyi sonuc verir

# =============================================================================
# ASAMA 6: PARAMETRE TAHMINI
# =============================================================================

cat("\n=== PARAMETRE TAHMINI ===\n")

# Parametreleri tahmin et
fitted_bn <- bn.fit(best_bn, bn_data, method = "mle")

# Her dugum icin ozet
cat("\nDugum parametreleri:\n")
for (node in names(fitted_bn)) {
  cat("\n---", node, "---\n")
  print(fitted_bn[[node]])
}

# =============================================================================
# ASAMA 7: BOOTSTRAP VALIDASYONU
# =============================================================================

cat("\n=== BOOTSTRAP VALIDASYONU ===\n")

# Bootstrap ile edge stability
set.seed(123)
boot_strength <- boot.strength(bn_data, R = 500, algorithm = "hc",
                               algorithm.args = list(score = "bic-g"))

cat("\nEdge gucleri (strength > 0.5):\n")
significant_edges <- boot_strength[boot_strength$strength > 0.5 &
                                     boot_strength$direction >= 0.5, ]
print(significant_edges[order(-significant_edges$strength), ])

# Ortalama network
avg_bn <- averaged.network(boot_strength, threshold = 0.5)
cat("\nOrtalama network yapisi:\n")
print(avg_bn)

# =============================================================================
# ASAMA 8: NETWORK GORSELLESTIRME
# =============================================================================

cat("\n=== NETWORK GORSELLESTIRME ===\n")

# Edge listesi olustur
edges <- arcs(best_bn)
if (nrow(edges) > 0) {
  # Adjacency matrix olustur
  nodes <- network_vars
  adj_matrix <- matrix(0, nrow = length(nodes), ncol = length(nodes),
                       dimnames = list(nodes, nodes))

  for (i in 1:nrow(edges)) {
    from <- edges[i, "from"]
    to <- edges[i, "to"]
    if (from %in% nodes && to %in% nodes) {
      adj_matrix[from, to] <- 1
    }
  }

  # qgraph ile gorsellestir
  pdf("data/bayesian_network_plot.pdf", width = 14, height = 12)

  # Korelasyon tabanli network
  qgraph(cor_matrix,
         layout = "spring",
         labels = colnames(cor_matrix),
         title = "Psychological Variables Network (Correlation)",
         edge.labels = FALSE,
         vsize = 10,
         label.cex = 1.2,
         edge.color = "darkblue",
         posCol = "darkgreen",
         negCol = "red")

  dev.off()
  cat("Network grafigi kaydedildi: data/bayesian_network_plot.pdf\n")
}

# =============================================================================
# ASAMA 9: CENTRALITY MEASURES
# =============================================================================

cat("\n=== CENTRALITY OLCULERI ===\n")

# EBICglasso ile regularized network
library(qgraph)
glasso_result <- EBICglasso(cor_matrix, n = nrow(network_data_complete),
                            gamma = 0.5, threshold = TRUE)

# Network olustur ve centrality hesapla
network_obj <- qgraph(glasso_result,
                      layout = "spring",
                      labels = colnames(cor_matrix),
                      DoNotPlot = TRUE)

# Centrality indices
centrality_indices <- centrality(network_obj)

cat("\nStrength Centrality:\n")
strength_df <- data.frame(
  Variable = names(centrality_indices$OutDegree),
  Strength = centrality_indices$OutDegree
)
print(strength_df[order(-strength_df$Strength), ])

cat("\nCloseness Centrality:\n")
closeness_df <- data.frame(
  Variable = names(centrality_indices$Closeness),
  Closeness = centrality_indices$Closeness
)
print(closeness_df[order(-closeness_df$Closeness), ])

cat("\nBetweenness Centrality:\n")
betweenness_df <- data.frame(
  Variable = names(centrality_indices$Betweenness),
  Betweenness = centrality_indices$Betweenness
)
print(betweenness_df[order(-betweenness_df$Betweenness), ])

# Centrality plot
pdf("data/centrality_plot.pdf", width = 10, height = 8)
centralityPlot(network_obj, include = c("Strength", "Closeness", "Betweenness"))
dev.off()
cat("\nCentrality grafigi kaydedildi: data/centrality_plot.pdf\n")

# =============================================================================
# ASAMA 10: SONUCLARIN KAYDEDILMESI
# =============================================================================

cat("\n=== SONUCLAR KAYDEDILIYOR ===\n")

# Sonuclari kaydet
results <- list(
  descriptives = descriptives,
  correlation_matrix = cor_matrix,
  bn_structure_hc = bn_hc,
  bn_structure_tabu = bn_tabu,
  bn_fitted = fitted_bn,
  boot_strength = boot_strength,
  centrality = centrality_indices
)

saveRDS(results, "data/bn_analysis_results.rds")
cat("Sonuclar kaydedildi: data/bn_analysis_results.rds\n")

# CSV olarak da kaydet
write.csv(as.data.frame(descriptives), "data/descriptives.csv", row.names = TRUE)
write.csv(as.data.frame(cor_matrix), "data/correlation_matrix.csv", row.names = TRUE)
write.csv(significant_edges, "data/significant_edges.csv", row.names = FALSE)

cat("\n=== ANALIZ TAMAMLANDI ===\n")
cat("Olusturulan dosyalar:\n")
cat("  - data/correlation_plot.pdf\n")
cat("  - data/bayesian_network_plot.pdf\n")
cat("  - data/centrality_plot.pdf\n")
cat("  - data/bn_analysis_results.rds\n")
cat("  - data/descriptives.csv\n")
cat("  - data/correlation_matrix.csv\n")
cat("  - data/significant_edges.csv\n")
