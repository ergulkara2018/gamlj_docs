#!/usr/bin/env python3
# =============================================================================
# Cinsiyet Gruplarina Gore Karsilastirma Analizi
# =============================================================================

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("CINSIYET GRUPLARINA GORE KARSILASTIRMA ANALIZI")
print("=" * 70)

# =============================================================================
# VERI YUKLEME VE HAZIRLAMA
# =============================================================================

df = pd.read_csv("data/modeldata.csv", sep=";", encoding="utf-8")
df.columns = df.columns.str.strip().str.replace('\n', '').str.replace(' ', '')

# Alt olcekleri hesapla
def calculate_subscale(data, items):
    existing = [i for i in items if i in data.columns]
    if len(existing) == 0:
        return pd.Series([np.nan] * len(data))
    subset = data[existing].apply(pd.to_numeric, errors='coerce')
    return subset.mean(axis=1)

# Alt olcekler
df['Depression'] = calculate_subscale(df, ["DAS3", "DAS5", "DAS10", "DAS13", "DAS16", "DAS17", "DAS21"])
df['Anxiety'] = calculate_subscale(df, ["DAS2", "DAS4", "DAS7", "DAS9", "DAS15", "DAS19", "DAS20"])
df['Stress'] = calculate_subscale(df, ["DAS1", "DAS6", "DAS8", "DAS11", "DAS12", "DAS14", "DAS18"])
df['Shame'] = calculate_subscale(df, ["SC1", "SC3", "SC5", "SC7", "SC9"])
df['Guilt'] = calculate_subscale(df, ["SC2", "SC4", "SC6", "SC8", "SC10"])
df['SelfCompassion'] = calculate_subscale(df, [f"GS{i}" for i in range(1, 11)])
df['SocialMediaAddiction'] = calculate_subscale(df, [f"BERGEN{i}" for i in range(1, 7)])
df['FamilySupport'] = calculate_subscale(df, ["SOS1", "SOS2", "SOS3", "SOS4"])
df['FriendSupport'] = calculate_subscale(df, ["SOS5", "SOS6", "SOS7", "SOS8"])
df['CyberVictimization'] = calculate_subscale(df, [f"CW{i}" for i in range(1, 11)])

time_col = [c for c in df.columns if 'TIME' in c.upper() or 'SOC' in c.upper()]
if time_col:
    df['SocialMediaTime'] = pd.to_numeric(df[time_col[0]], errors='coerce')
df['Age'] = pd.to_numeric(df['age'], errors='coerce')

# Analiz degiskenleri
network_vars = ['Depression', 'Anxiety', 'Stress', 'Shame', 'Guilt',
                'SelfCompassion', 'SocialMediaAddiction',
                'FamilySupport', 'FriendSupport', 'CyberVictimization',
                'SocialMediaTime', 'Age']

# Cinsiyet gruplari
male_df = df[df['gender'] == 'Erkek'][network_vars].dropna()
female_df = df[df['gender'].isin(['Kadın', 'Kadin'])][network_vars].dropna()

print(f"\nErkek sayisi: {len(male_df)}")
print(f"Kadin sayisi: {len(female_df)}")

# =============================================================================
# BETIMSEL ISTATISTIKLER
# =============================================================================

print("\n" + "=" * 70)
print("BETIMSEL ISTATISTIKLER - CINSIYET KARSILASTIRMASI")
print("=" * 70)

desc_comparison = []
for var in network_vars:
    male_mean = male_df[var].mean()
    male_std = male_df[var].std()
    female_mean = female_df[var].mean()
    female_std = female_df[var].std()

    desc_comparison.append({
        'Variable': var,
        'Male_Mean': round(male_mean, 2),
        'Male_SD': round(male_std, 2),
        'Female_Mean': round(female_mean, 2),
        'Female_SD': round(female_std, 2),
        'Difference': round(female_mean - male_mean, 2)
    })

desc_df = pd.DataFrame(desc_comparison)
print("\n" + desc_df.to_string(index=False))

# =============================================================================
# T-TEST KARSILASTIRMASI
# =============================================================================

print("\n" + "=" * 70)
print("BAGIMSIZ ORNEKLEM T-TESTI SONUCLARI")
print("=" * 70)

ttest_results = []
for var in network_vars:
    # Levene testi (varyans homojenligi)
    levene_stat, levene_p = stats.levene(male_df[var], female_df[var])

    # T-test (equal_var durumuna gore)
    equal_var = levene_p > 0.05
    t_stat, t_p = stats.ttest_ind(male_df[var], female_df[var], equal_var=equal_var)

    # Cohen's d (etki buyuklugu)
    pooled_std = np.sqrt(((len(male_df)-1)*male_df[var].std()**2 +
                          (len(female_df)-1)*female_df[var].std()**2) /
                         (len(male_df) + len(female_df) - 2))
    cohens_d = (female_df[var].mean() - male_df[var].mean()) / pooled_std

    # Etki buyuklugu yorumu
    if abs(cohens_d) < 0.2:
        effect_size = "Kucuk"
    elif abs(cohens_d) < 0.5:
        effect_size = "Orta"
    elif abs(cohens_d) < 0.8:
        effect_size = "Buyuk"
    else:
        effect_size = "Cok Buyuk"

    # Anlamlilik
    sig = "***" if t_p < 0.001 else "**" if t_p < 0.01 else "*" if t_p < 0.05 else ""

    ttest_results.append({
        'Variable': var,
        't': round(t_stat, 2),
        'p': round(t_p, 4),
        'Sig': sig,
        "Cohen's d": round(cohens_d, 2),
        'Effect': effect_size
    })

ttest_df = pd.DataFrame(ttest_results)
print("\n" + ttest_df.to_string(index=False))
print("\n* p < .05, ** p < .01, *** p < .001")

# Anlamli farkliliklari ayir
significant_diff = ttest_df[ttest_df['Sig'] != '']
print("\n--- ANLAMLI FARKLILIKLAR ---")
if len(significant_diff) > 0:
    print(significant_diff.to_string(index=False))
else:
    print("Anlamli farklilik bulunamadi.")

# =============================================================================
# MANN-WHITNEY U TESTI (NON-PARAMETRIK)
# =============================================================================

print("\n" + "=" * 70)
print("MANN-WHITNEY U TESTI SONUCLARI (Non-parametrik)")
print("=" * 70)

mw_results = []
for var in network_vars:
    u_stat, u_p = stats.mannwhitneyu(male_df[var], female_df[var], alternative='two-sided')

    # r etki buyuklugu
    n = len(male_df) + len(female_df)
    z = stats.norm.ppf(u_p/2)
    r = abs(z) / np.sqrt(n)

    sig = "***" if u_p < 0.001 else "**" if u_p < 0.01 else "*" if u_p < 0.05 else ""

    mw_results.append({
        'Variable': var,
        'U': round(u_stat, 0),
        'p': round(u_p, 4),
        'Sig': sig,
        'r': round(r, 2)
    })

mw_df = pd.DataFrame(mw_results)
print("\n" + mw_df.to_string(index=False))

# =============================================================================
# KORELASYON KARSILASTIRMASI
# =============================================================================

print("\n" + "=" * 70)
print("KORELASYON MATRISI KARSILASTIRMASI")
print("=" * 70)

male_cor = male_df.corr()
female_cor = female_df.corr()

print("\n--- EN BUYUK KORELASYON FARKLILIKLARI ---")
cor_diff = []
for i, var1 in enumerate(network_vars):
    for j, var2 in enumerate(network_vars):
        if i < j:
            male_r = male_cor.loc[var1, var2]
            female_r = female_cor.loc[var1, var2]
            diff = female_r - male_r

            cor_diff.append({
                'Variable1': var1,
                'Variable2': var2,
                'Male_r': round(male_r, 2),
                'Female_r': round(female_r, 2),
                'Difference': round(diff, 2),
                'Abs_Diff': abs(diff)
            })

cor_diff_df = pd.DataFrame(cor_diff).sort_values('Abs_Diff', ascending=False)
print(cor_diff_df.head(15).to_string(index=False))

# =============================================================================
# GRUP BAZLI CENTRALITY KARSILASTIRMASI
# =============================================================================

print("\n" + "=" * 70)
print("CENTRALITY KARSILASTIRMASI")
print("=" * 70)

import networkx as nx

def calculate_network_centrality(data, label):
    cor_matrix = data.corr()
    G = nx.Graph()

    for var in network_vars:
        G.add_node(var)

    # Anlamli korelasyonlari ekle
    n = len(data)
    for i, var1 in enumerate(network_vars):
        for j, var2 in enumerate(network_vars):
            if i < j:
                r = cor_matrix.loc[var1, var2]
                t_stat = r * np.sqrt((n-2) / (1 - r**2))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-2))
                if p_value < 0.05 and abs(r) > 0.1:
                    G.add_edge(var1, var2, weight=abs(r))

    strength = dict(G.degree(weight='weight'))
    return {var: round(strength.get(var, 0), 3) for var in network_vars}

male_centrality = calculate_network_centrality(male_df, "Male")
female_centrality = calculate_network_centrality(female_df, "Female")

centrality_comp = []
for var in network_vars:
    centrality_comp.append({
        'Variable': var,
        'Male_Strength': male_centrality[var],
        'Female_Strength': female_centrality[var],
        'Difference': round(female_centrality[var] - male_centrality[var], 3)
    })

centrality_comp_df = pd.DataFrame(centrality_comp).sort_values('Male_Strength', ascending=False)
print("\n" + centrality_comp_df.to_string(index=False))

# =============================================================================
# GORSELLESTIRME
# =============================================================================

print("\n" + "=" * 70)
print("GORSELLESTIRME")
print("=" * 70)

import matplotlib.pyplot as plt
import seaborn as sns

# 1. Grup Ortalamalarinin Karsilastirilmasi
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(network_vars))
width = 0.35

male_means = [male_df[var].mean() for var in network_vars]
female_means = [female_df[var].mean() for var in network_vars]

bars1 = ax.bar(x - width/2, male_means, width, label='Erkek', color='steelblue', alpha=0.8)
bars2 = ax.bar(x + width/2, female_means, width, label='Kadın', color='coral', alpha=0.8)

# Anlamli farkliliklari isle
for i, var in enumerate(network_vars):
    if var in significant_diff['Variable'].values:
        ax.annotate('*', xy=(i, max(male_means[i], female_means[i]) + 0.1),
                   ha='center', fontsize=14, fontweight='bold')

ax.set_xlabel('Degiskenler', fontsize=12)
ax.set_ylabel('Ortalama', fontsize=12)
ax.set_title('Cinsiyet Gruplarina Gore Degisken Ortalamalari', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(network_vars, rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('data/gender_comparison_means.png', dpi=150)
plt.close()
print("Kaydedildi: data/gender_comparison_means.png")

# 2. Korelasyon Matrisleri Yan Yana
fig, axes = plt.subplots(1, 2, figsize=(20, 8))

# Erkek
mask = np.triu(np.ones_like(male_cor, dtype=bool))
sns.heatmap(male_cor, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, ax=axes[0], cbar_kws={"shrink": 0.8},
            annot_kws={"size": 8})
axes[0].set_title('Erkek (n={})'.format(len(male_df)), fontsize=14, fontweight='bold')

# Kadin
sns.heatmap(female_cor, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, ax=axes[1], cbar_kws={"shrink": 0.8},
            annot_kws={"size": 8})
axes[1].set_title('Kadın (n={})'.format(len(female_df)), fontsize=14, fontweight='bold')

plt.suptitle('Cinsiyet Gruplarina Gore Korelasyon Matrisleri', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('data/gender_correlation_comparison.png', dpi=150)
plt.close()
print("Kaydedildi: data/gender_correlation_comparison.png")

# 3. Network Grafikleri
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

def draw_network(data, ax, title, label):
    cor_matrix = data.corr()
    G = nx.Graph()

    for var in network_vars:
        G.add_node(var)

    n = len(data)
    for i, var1 in enumerate(network_vars):
        for j, var2 in enumerate(network_vars):
            if i < j:
                r = cor_matrix.loc[var1, var2]
                t_stat = r * np.sqrt((n-2) / (1 - r**2))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-2))
                if p_value < 0.05 and abs(r) > 0.1:
                    G.add_edge(var1, var2, weight=abs(r), correlation=r)

    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Dugum boyutlari
    strength = dict(G.degree(weight='weight'))
    node_sizes = [strength.get(v, 0.1) * 400 + 300 for v in G.nodes()]

    # Kenar renkleri ve kalinliklari
    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        r = G[u][v].get('correlation', 0)
        edge_colors.append('green' if r > 0 else 'red')
        edge_widths.append(abs(r) * 3)

    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                          node_color='lightblue', alpha=0.9)
    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths,
                          edge_color=edge_colors, alpha=0.6)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight='bold')

    ax.set_title(f'{title}\n(n={len(data)})', fontsize=14, fontweight='bold')
    ax.axis('off')

draw_network(male_df, axes[0], 'Erkek Network', 'male')
draw_network(female_df, axes[1], 'Kadın Network', 'female')

plt.suptitle('Cinsiyet Gruplarina Gore Network Grafikleri\n(Yesil=Pozitif, Kirmizi=Negatif)',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('data/gender_network_comparison.png', dpi=150)
plt.close()
print("Kaydedildi: data/gender_network_comparison.png")

# 4. Centrality Karsilastirmasi
fig, ax = plt.subplots(figsize=(12, 8))

x = np.arange(len(network_vars))
width = 0.35

male_str = [male_centrality[var] for var in network_vars]
female_str = [female_centrality[var] for var in network_vars]

# Sırala
sorted_idx = np.argsort(male_str)[::-1]
sorted_vars = [network_vars[i] for i in sorted_idx]
male_str_sorted = [male_str[i] for i in sorted_idx]
female_str_sorted = [female_str[i] for i in sorted_idx]

bars1 = ax.barh(np.arange(len(sorted_vars)) + width/2, male_str_sorted, width,
                label='Erkek', color='steelblue', alpha=0.8)
bars2 = ax.barh(np.arange(len(sorted_vars)) - width/2, female_str_sorted, width,
                label='Kadın', color='coral', alpha=0.8)

ax.set_xlabel('Strength Centrality', fontsize=12)
ax.set_ylabel('Degiskenler', fontsize=12)
ax.set_title('Cinsiyet Gruplarina Gore Strength Centrality', fontsize=14, fontweight='bold')
ax.set_yticks(np.arange(len(sorted_vars)))
ax.set_yticklabels(sorted_vars)
ax.legend()
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('data/gender_centrality_comparison.png', dpi=150)
plt.close()
print("Kaydedildi: data/gender_centrality_comparison.png")

# =============================================================================
# CSV KAYDETME
# =============================================================================

desc_df.to_csv('data/gender_descriptives.csv', index=False)
ttest_df.to_csv('data/gender_ttest_results.csv', index=False)
mw_df.to_csv('data/gender_mannwhitney_results.csv', index=False)
cor_diff_df.to_csv('data/gender_correlation_differences.csv', index=False)
centrality_comp_df.to_csv('data/gender_centrality_comparison.csv', index=False)

print("\nCSV dosyalari kaydedildi.")

# =============================================================================
# OZET
# =============================================================================

print("\n" + "=" * 70)
print("ANALIZ OZETI")
print("=" * 70)

print(f"""
ORNEKLEM:
- Erkek: {len(male_df)}
- Kadin: {len(female_df)}
- Toplam: {len(male_df) + len(female_df)}

ANLAMLI CINSIYET FARKLILIKLARI (p < .05):
""")

if len(significant_diff) > 0:
    for _, row in significant_diff.iterrows():
        var = row['Variable']
        male_m = desc_df[desc_df['Variable']==var]['Male_Mean'].values[0]
        female_m = desc_df[desc_df['Variable']==var]['Female_Mean'].values[0]
        direction = "Kadinlar daha yuksek" if female_m > male_m else "Erkekler daha yuksek"
        d_value = row["Cohen's d"]
        print(f"  - {var}: {direction} (d = {d_value})")
else:
    print("  Anlamli farklilik bulunamadi.")

print(f"""
EN BUYUK KORELASYON FARKLILIKLARI:
""")
for _, row in cor_diff_df.head(5).iterrows():
    print(f"  - {row['Variable1']} <-> {row['Variable2']}: Erkek={row['Male_r']}, Kadin={row['Female_r']} (fark={row['Difference']})")

print(f"""
OLUSTURULAN DOSYALAR:
- data/gender_comparison_means.png
- data/gender_correlation_comparison.png
- data/gender_network_comparison.png
- data/gender_centrality_comparison.png
- data/gender_descriptives.csv
- data/gender_ttest_results.csv
- data/gender_mannwhitney_results.csv
- data/gender_correlation_differences.csv
- data/gender_centrality_comparison.csv

ANALIZ TAMAMLANDI!
""")
