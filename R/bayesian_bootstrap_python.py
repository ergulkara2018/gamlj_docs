"""
Bayesian Bootstrapping Analysis - Social Media & Psychological Distress
========================================================================
Rubin (1981) Bayesian Bootstrap yontemi
Dirichlet dagilimi kullanilarak agirliklarin olusturulmasi
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("BAYESIAN BOOTSTRAPPING ANALIZI")
print("=" * 70)

# =============================================================================
# ASAMA 1: VERI YUKLEME
# =============================================================================

df = pd.read_csv('data/modeldata.csv', sep=';', encoding='utf-8')

# Sutun isimlerini temizle
df.columns = df.columns.str.strip().str.replace('\n', '').str.replace(' ', '')

print(f"\nVeri yuklendi: {len(df)} satir, {len(df.columns)} sutun")

# =============================================================================
# ASAMA 2: ALT OLCEK PUANLARININ HESAPLANMASI
# =============================================================================

# DASS-21 alt olcekleri
depression_items = ['DAS3', 'DAS5', 'DAS10', 'DAS13', 'DAS16', 'DAS17', 'DAS21']
anxiety_items = ['DAS2', 'DAS4', 'DAS7', 'DAS9', 'DAS15', 'DAS19', 'DAS20']
stress_items = ['DAS1', 'DAS6', 'DAS8', 'DAS11', 'DAS12', 'DAS14', 'DAS18']

# Shame and Guilt Scale
shame_items = ['SC1', 'SC3', 'SC5', 'SC7', 'SC9']
guilt_items = ['SC2', 'SC4', 'SC6', 'SC8', 'SC10']

# Self-Compassion Scale
self_compassion_items = [f'GS{i}' for i in range(1, 11)]

# Bergen Social Media Addiction Scale
bergen_items = [f'BERGEN{i}' for i in range(1, 7)]

# Social Support Scale
family_support_items = ['SOS1', 'SOS2', 'SOS3', 'SOS4']
friend_support_items = ['SOS5', 'SOS6', 'SOS7', 'SOS8']

# Cyber Victimization
cyber_victim_items = [f'CW{i}' for i in range(1, 11)]

def calculate_subscale(data, items):
    """Alt olcek puanlarini hesapla"""
    existing = [i for i in items if i in data.columns]
    if not existing:
        return pd.Series([np.nan] * len(data))
    return pd.to_numeric(data[existing].apply(pd.to_numeric, errors='coerce').mean(axis=1), errors='coerce')

# Alt olcekleri hesapla
df['Depression'] = calculate_subscale(df, depression_items)
df['Anxiety'] = calculate_subscale(df, anxiety_items)
df['Stress'] = calculate_subscale(df, stress_items)
df['Shame'] = calculate_subscale(df, shame_items)
df['Guilt'] = calculate_subscale(df, guilt_items)
df['SelfCompassion'] = calculate_subscale(df, self_compassion_items)
df['SocialMediaAddiction'] = calculate_subscale(df, bergen_items)
df['FamilySupport'] = calculate_subscale(df, family_support_items)
df['FriendSupport'] = calculate_subscale(df, friend_support_items)
df['CyberVictimization'] = calculate_subscale(df, cyber_victim_items)

# Analiz degiskenleri
analysis_vars = ['Depression', 'Anxiety', 'Stress', 'Shame', 'Guilt',
                 'SelfCompassion', 'SocialMediaAddiction',
                 'FamilySupport', 'FriendSupport', 'CyberVictimization']

# Tam veri seti
analysis_data = df[analysis_vars].dropna()
print(f"Analiz icin kullanilan gozlem sayisi: {len(analysis_data)}")

# =============================================================================
# ASAMA 3: BAYESIAN BOOTSTRAP FONKSIYONLARI
# =============================================================================

def dirichlet_weights(n):
    """Dirichlet(1,1,...,1) dagiliminden agirliklari cek"""
    weights = np.random.gamma(1, 1, n)
    return weights / weights.sum()

def bayesian_bootstrap_mean(data, n_iterations=4000):
    """Bayesian bootstrap ile ortalama tahminleri"""
    n = len(data)
    samples = np.zeros(n_iterations)

    for i in range(n_iterations):
        weights = dirichlet_weights(n)
        samples[i] = np.average(data, weights=weights)

    return samples

def bayesian_bootstrap_correlation(x, y, n_iterations=4000):
    """Bayesian bootstrap ile korelasyon tahminleri"""
    n = len(x)
    samples = np.zeros(n_iterations)

    for i in range(n_iterations):
        weights = dirichlet_weights(n)

        # Agirlikli ortalamalar
        mx = np.average(x, weights=weights)
        my = np.average(y, weights=weights)

        # Agirlikli kovaryans ve standart sapmalar
        cov_xy = np.sum(weights * (x - mx) * (y - my))
        sd_x = np.sqrt(np.sum(weights * (x - mx)**2))
        sd_y = np.sqrt(np.sum(weights * (y - my)**2))

        if sd_x > 0 and sd_y > 0:
            samples[i] = cov_xy / (sd_x * sd_y)
        else:
            samples[i] = 0

    return samples

def bayesian_bootstrap_regression(X, y, n_iterations=4000):
    """Bayesian bootstrap ile regresyon katsayilari"""
    n = len(y)
    n_predictors = X.shape[1]
    samples = np.zeros((n_iterations, n_predictors + 1))

    for i in range(n_iterations):
        weights = dirichlet_weights(n)
        sqrt_weights = np.sqrt(weights * n)

        # Agirlikli en kucuk kareler
        X_weighted = X * sqrt_weights[:, np.newaxis]
        y_weighted = y * sqrt_weights

        # Intercept ekle
        X_design = np.column_stack([np.ones(n) * sqrt_weights, X_weighted])

        try:
            beta = np.linalg.lstsq(X_design, y_weighted, rcond=None)[0]
            samples[i, :] = beta
        except:
            samples[i, :] = np.nan

    return samples

def hdi(samples, credible_mass=0.95):
    """Highest Density Interval hesapla"""
    sorted_samples = np.sort(samples)
    n = len(sorted_samples)
    ci_idx_inc = int(np.floor(credible_mass * n))
    n_cis = n - ci_idx_inc
    ci_widths = sorted_samples[ci_idx_inc:] - sorted_samples[:n_cis]
    min_idx = np.argmin(ci_widths)
    hdi_low = sorted_samples[min_idx]
    hdi_high = sorted_samples[min_idx + ci_idx_inc]
    return hdi_low, hdi_high

np.random.seed(42)
n_iterations = 4000

# =============================================================================
# ASAMA 4: BAYESIAN BOOTSTRAP - ORTALAMALAR
# =============================================================================

print("\n" + "=" * 70)
print("BAYESIAN BOOTSTRAP: ORTALAMALAR")
print("=" * 70)

means_results = []

for var in analysis_vars:
    print(f"\nAnaliz ediliyor: {var}")

    data = analysis_data[var].values
    samples = bayesian_bootstrap_mean(data, n_iterations)

    mean_est = np.mean(samples)
    sd_est = np.std(samples)
    ci_lower = np.percentile(samples, 2.5)
    ci_upper = np.percentile(samples, 97.5)
    hdi_lower, hdi_upper = hdi(samples)

    means_results.append({
        'Variable': var,
        'Mean': mean_est,
        'SD': sd_est,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper,
        'HDI_Lower': hdi_lower,
        'HDI_Upper': hdi_upper
    })

    print(f"  Ortalama: {mean_est:.3f}")
    print(f"  SD: {sd_est:.3f}")
    print(f"  95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
    print(f"  95% HDI: [{hdi_lower:.3f}, {hdi_upper:.3f}]")

means_df = pd.DataFrame(means_results)
means_df.to_csv('data/bayes_bootstrap_means.csv', index=False)
print("\nKaydedildi: data/bayes_bootstrap_means.csv")

# =============================================================================
# ASAMA 5: BAYESIAN BOOTSTRAP - KORELASYONLAR
# =============================================================================

print("\n" + "=" * 70)
print("BAYESIAN BOOTSTRAP: KORELASYONLAR")
print("=" * 70)

from itertools import combinations

var_pairs = list(combinations(analysis_vars, 2))
print(f"\nToplam {len(var_pairs)} korelasyon hesaplaniyor...")

cor_results = []

for idx, (var1, var2) in enumerate(var_pairs):
    x = analysis_data[var1].values
    y = analysis_data[var2].values

    samples = bayesian_bootstrap_correlation(x, y, n_iterations)

    mean_est = np.mean(samples)
    sd_est = np.std(samples)
    ci_lower = np.percentile(samples, 2.5)
    ci_upper = np.percentile(samples, 97.5)
    hdi_lower, hdi_upper = hdi(samples)

    cor_results.append({
        'Variable1': var1,
        'Variable2': var2,
        'Correlation': mean_est,
        'SD': sd_est,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper,
        'HDI_Lower': hdi_lower,
        'HDI_Upper': hdi_upper,
        'Prob_Positive': np.mean(samples > 0),
        'Prob_Negative': np.mean(samples < 0)
    })

    if (idx + 1) % 10 == 0:
        print(f"  Tamamlanan: {idx + 1}/{len(var_pairs)}")

cor_df = pd.DataFrame(cor_results)
cor_df.to_csv('data/bayes_bootstrap_correlations.csv', index=False)
print("\nKaydedildi: data/bayes_bootstrap_correlations.csv")

# =============================================================================
# ASAMA 6: BAYESIAN BOOTSTRAP - REGRESYON
# =============================================================================

print("\n" + "=" * 70)
print("BAYESIAN BOOTSTRAP: REGRESYON ANALIZI")
print("=" * 70)
print("Bagimli degisken: Depression")

predictors = ['Anxiety', 'Stress', 'Shame', 'Guilt', 'SelfCompassion',
              'SocialMediaAddiction', 'CyberVictimization']

X = analysis_data[predictors].values
y = analysis_data['Depression'].values

print("Regresyon katsayilari hesaplaniyor...")
reg_samples = bayesian_bootstrap_regression(X, y, n_iterations)

reg_results = []
var_names = ['Intercept'] + predictors

for i, var in enumerate(var_names):
    samples = reg_samples[:, i]
    samples = samples[~np.isnan(samples)]

    mean_est = np.mean(samples)
    sd_est = np.std(samples)
    ci_lower = np.percentile(samples, 2.5)
    ci_upper = np.percentile(samples, 97.5)
    hdi_lower, hdi_upper = hdi(samples)

    reg_results.append({
        'Predictor': var,
        'Coefficient': mean_est,
        'SD': sd_est,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper,
        'HDI_Lower': hdi_lower,
        'HDI_Upper': hdi_upper,
        'Prob_Positive': np.mean(samples > 0),
        'Prob_Negative': np.mean(samples < 0)
    })

reg_df = pd.DataFrame(reg_results)
reg_df.to_csv('data/bayes_bootstrap_regression.csv', index=False)
print("\nKaydedildi: data/bayes_bootstrap_regression.csv")

# =============================================================================
# ASAMA 7: SONUC RAPORU
# =============================================================================

print("\n" + "=" * 70)
print("BAYESIAN BOOTSTRAPPING ANALIZI - OZET")
print("=" * 70)

print(f"\nYontem: Rubin (1981) Bayesian Bootstrap")
print(f"Iterasyon sayisi: {n_iterations}")
print(f"Gozlem sayisi: {len(analysis_data)}")

print("\n--- TANIMLAYICI ISTATISTIKLER (Bayesian Bootstrap) ---")
print(means_df.to_string(index=False))

print("\n--- EN GUCLU KORELASYONLAR ---")
cor_sorted = cor_df.reindex(cor_df['Correlation'].abs().sort_values(ascending=False).index)
print(cor_sorted[['Variable1', 'Variable2', 'Correlation', 'CI_Lower', 'CI_Upper']].head(10).to_string(index=False))

print("\n--- REGRESYON KATSAYILARI ---")
print("-" * 80)
print(f"{'Degisken':<25} {'Mean':>10} {'SD':>10} {'CI_Lower':>12} {'CI_Upper':>12} {'P(b>0)':>10}")
print("-" * 80)
for _, row in reg_df.iterrows():
    print(f"{row['Predictor']:<25} {row['Coefficient']:>10.4f} {row['SD']:>10.4f} {row['CI_Lower']:>12.4f} {row['CI_Upper']:>12.4f} {row['Prob_Positive']:>10.4f}")

print("\n--- ANLAMLI REGRESYON KATSAYILARI ---")
print("(CI sifiri icermeyenler)")
sig_reg = reg_df[(reg_df['Predictor'] != 'Intercept') &
                  ((reg_df['CI_Lower'] > 0) | (reg_df['CI_Upper'] < 0))]
if len(sig_reg) > 0:
    print(sig_reg[['Predictor', 'Coefficient', 'CI_Lower', 'CI_Upper', 'Prob_Positive']].to_string(index=False))
else:
    print("Anlamli katsayi bulunamadi.")

print("\n" + "=" * 70)
print("ANALIZ TAMAMLANDI")
print("=" * 70)
print("\nOlusturulan dosyalar:")
print("  - data/bayes_bootstrap_means.csv")
print("  - data/bayes_bootstrap_correlations.csv")
print("  - data/bayes_bootstrap_regression.csv")
