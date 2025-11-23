#!/usr/bin/env python3
# =============================================================================
# Bayesian Network Analysis - Social Media & Psychological Distress
# Python Implementation
# =============================================================================

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# ASAMA 1: VERI YUKLEME
# =============================================================================

print("=" * 60)
print("BAYESIAN NETWORK ANALIZI")
print("=" * 60)

# Veriyi oku
data_path = "data/modeldata.csv"
df = pd.read_csv(data_path, sep=";", encoding="utf-8")

# Sutun isimlerini temizle
df.columns = df.columns.str.strip().str.replace('\n', '').str.replace(' ', '')

print(f"\nVeri boyutu: {df.shape[0]} satir, {df.shape[1]} sutun")
print(f"\nDegiskenler: {list(df.columns)[:20]}...")

# =============================================================================
# ASAMA 2: ALT OLCEK PUANLARININ HESAPLANMASI
# =============================================================================

print("\n" + "=" * 60)
print("ALT OLCEK PUANLARI HESAPLANIYOR...")
print("=" * 60)

# DASS-21 alt olcekleri
depression_items = ["DAS3", "DAS5", "DAS10", "DAS13", "DAS16", "DAS17", "DAS21"]
anxiety_items = ["DAS2", "DAS4", "DAS7", "DAS9", "DAS15", "DAS19", "DAS20"]
stress_items = ["DAS1", "DAS6", "DAS8", "DAS11", "DAS12", "DAS14", "DAS18"]

# Shame and Guilt
shame_items = ["SC1", "SC3", "SC5", "SC7", "SC9"]
guilt_items = ["SC2", "SC4", "SC6", "SC8", "SC10"]

# Self-Compassion
self_compassion_items = [f"GS{i}" for i in range(1, 11)]

# Bergen Social Media Addiction
bergen_items = [f"BERGEN{i}" for i in range(1, 7)]

# Social Support
family_support_items = ["SOS1", "SOS2", "SOS3", "SOS4"]
friend_support_items = ["SOS5", "SOS6", "SOS7", "SOS8"]

# Cyber Victimization
cyber_victim_items = [f"CW{i}" for i in range(1, 11)]

def calculate_subscale(data, items):
    """Alt olcek puanini hesapla (ortalama)"""
    existing = [i for i in items if i in data.columns]
    if len(existing) == 0:
        return pd.Series([np.nan] * len(data))
    subset = data[existing].apply(pd.to_numeric, errors='coerce')
    return subset.mean(axis=1)

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

# Diger degiskenler
# TİMESOCİAL sutununu bul
time_col = [c for c in df.columns if 'TIME' in c.upper() or 'SOC' in c.upper()]
if time_col:
    df['SocialMediaTime'] = pd.to_numeric(df[time_col[0]], errors='coerce')
else:
    df['SocialMediaTime'] = np.nan

df['Age'] = pd.to_numeric(df['age'], errors='coerce')
df['Gender'] = df['gender'].map({'Erkek': 0, 'Kadın': 1, 'Kadin': 1})

print("Alt olcekler hesaplandi:")
print("- Depression, Anxiety, Stress (DASS-21)")
print("- Shame, Guilt")
print("- SelfCompassion, SocialMediaAddiction")
print("- FamilySupport, FriendSupport")
print("- CyberVictimization")

# =============================================================================
# ASAMA 3: NETWORK VERISI HAZIRLAMA
# =============================================================================

network_vars = ['Depression', 'Anxiety', 'Stress', 'Shame', 'Guilt',
                'SelfCompassion', 'SocialMediaAddiction',
                'FamilySupport', 'FriendSupport', 'CyberVictimization',
                'SocialMediaTime', 'Age']

network_data = df[network_vars].copy()

# Eksik veri analizi
print("\n" + "=" * 60)
print("EKSIK VERI ANALIZI")
print("=" * 60)

missing = network_data.isnull().sum()
print("\nDegisken bazinda eksik veri:")
print(missing)
print(f"\nToplam eksik veri orani: {network_data.isnull().sum().sum() / network_data.size * 100:.2f}%")

# Eksik verileri kaldir
network_complete = network_data.dropna()
print(f"\nTam veri ile kalan gozlem: {len(network_complete)}")

# =============================================================================
# ASAMA 4: BETIMSEL ISTATISTIKLER
# =============================================================================

print("\n" + "=" * 60)
print("BETIMSEL ISTATISTIKLER")
print("=" * 60)

descriptives = network_complete.describe().T
descriptives['skewness'] = network_complete.skew()
descriptives['kurtosis'] = network_complete.kurtosis()
print(descriptives.round(2))

# Kaydet
descriptives.to_csv("data/descriptives_python.csv")
print("\nBetimsel istatistikler kaydedildi: data/descriptives_python.csv")

# =============================================================================
# ASAMA 5: KORELASYON MATRISI
# =============================================================================

print("\n" + "=" * 60)
print("KORELASYON MATRISI")
print("=" * 60)

cor_matrix = network_complete.corr()
print(cor_matrix.round(2))

# Kaydet
cor_matrix.to_csv("data/correlation_matrix_python.csv")
print("\nKorelasyon matrisi kaydedildi: data/correlation_matrix_python.csv")

# =============================================================================
# ASAMA 6: BAYESIAN NETWORK ANALIZI
# =============================================================================

print("\n" + "=" * 60)
print("BAYESIAN NETWORK ANALIZI")
print("=" * 60)

try:
    from pgmpy.estimators import HillClimbSearch, BicScore, K2Score
    from pgmpy.estimators import PC
    from pgmpy.models import BayesianNetwork
    from pgmpy.estimators import MaximumLikelihoodEstimator

    # Veriyi hazirla
    bn_data = network_complete.copy()

    # Hill-Climbing ile yapi ogrenimi
    print("\n--- Hill-Climbing Algorithm ---")
    hc = HillClimbSearch(bn_data)
    best_model_hc = hc.estimate(scoring_method=BicScore(bn_data))

    print("Ogrenen kenarlar (edges):")
    edges_hc = list(best_model_hc.edges())
    for edge in edges_hc:
        print(f"  {edge[0]} -> {edge[1]}")

    print(f"\nToplam kenar sayisi: {len(edges_hc)}")

    # PC Algorithm
    print("\n--- PC Algorithm ---")
    try:
        pc = PC(bn_data)
        pc_model = pc.estimate(variant="stable", max_cond_vars=4, significance_level=0.05)
        edges_pc = list(pc_model.edges())
        print(f"PC ile bulunan kenar sayisi: {len(edges_pc)}")
    except Exception as e:
        print(f"PC algorithm hatasi: {e}")
        edges_pc = []

    # Bayesian Network modeli olustur
    print("\n--- Model Olusturma ---")
    model = BayesianNetwork(edges_hc)
    model.fit(bn_data, estimator=MaximumLikelihoodEstimator)

    print("Model basariyla olusturuldu!")
    print(f"Dugumler: {model.nodes()}")
    print(f"Kenarlar: {model.edges()}")

    # Kenarlari kaydet
    edges_df = pd.DataFrame(edges_hc, columns=['From', 'To'])
    edges_df.to_csv("data/bn_edges_python.csv", index=False)
    print("\nKenarlar kaydedildi: data/bn_edges_python.csv")

except ImportError:
    print("pgmpy yuklu degil. Korelasyon tabanli network analizi yapiliyor...")
    edges_hc = []

# =============================================================================
# ASAMA 7: KORELASYON TABANLI NETWORK (ALTERNATIF)
# =============================================================================

print("\n" + "=" * 60)
print("KORELASYON TABANLI NETWORK ANALIZI")
print("=" * 60)

# Anlamli korelasyonlari bul
n = len(network_complete)
alpha = 0.05

significant_edges = []
for i, var1 in enumerate(network_vars):
    for j, var2 in enumerate(network_vars):
        if i < j:
            r = cor_matrix.loc[var1, var2]
            # t-testi ile anlamlilik
            t_stat = r * np.sqrt((n-2) / (1 - r**2))
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-2))

            if p_value < alpha and abs(r) > 0.1:
                significant_edges.append({
                    'From': var1,
                    'To': var2,
                    'Correlation': round(r, 3),
                    'p_value': round(p_value, 4),
                    'Strength': abs(r)
                })

sig_edges_df = pd.DataFrame(significant_edges)
sig_edges_df = sig_edges_df.sort_values('Strength', ascending=False)

print("\nAnlamli korelasyonlar (p < 0.05, |r| > 0.1):")
print(sig_edges_df.to_string(index=False))

sig_edges_df.to_csv("data/significant_correlations_python.csv", index=False)
print("\nAnlamli korelasyonlar kaydedildi: data/significant_correlations_python.csv")

# =============================================================================
# ASAMA 8: CENTRALITY OLCULERI
# =============================================================================

print("\n" + "=" * 60)
print("CENTRALITY OLCULERI")
print("=" * 60)

try:
    import networkx as nx

    # Korelasyon matrisinden network olustur
    G = nx.Graph()

    # Dugumleri ekle
    for var in network_vars:
        G.add_node(var)

    # Anlamli kenarlari ekle
    for _, row in sig_edges_df.iterrows():
        G.add_edge(row['From'], row['To'], weight=abs(row['Correlation']))

    # Centrality hesapla
    degree_cent = nx.degree_centrality(G)
    between_cent = nx.betweenness_centrality(G)
    closeness_cent = nx.closeness_centrality(G)

    # Strength (weighted degree)
    strength = dict(G.degree(weight='weight'))

    centrality_df = pd.DataFrame({
        'Variable': network_vars,
        'Degree': [degree_cent.get(v, 0) for v in network_vars],
        'Betweenness': [between_cent.get(v, 0) for v in network_vars],
        'Closeness': [closeness_cent.get(v, 0) for v in network_vars],
        'Strength': [strength.get(v, 0) for v in network_vars]
    })

    centrality_df = centrality_df.sort_values('Strength', ascending=False)

    print("\nCentrality Olculeri:")
    print(centrality_df.to_string(index=False))

    centrality_df.to_csv("data/centrality_python.csv", index=False)
    print("\nCentrality olculeri kaydedildi: data/centrality_python.csv")

except ImportError:
    print("networkx yuklu degil, centrality hesaplanamadi.")

# =============================================================================
# ASAMA 9: GORSELLESTIRME
# =============================================================================

print("\n" + "=" * 60)
print("GORSELLESTIRME")
print("=" * 60)

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    # 1. Korelasyon Heatmap
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(cor_matrix, dtype=bool))
    sns.heatmap(cor_matrix, mask=mask, annot=True, fmt='.2f',
                cmap='RdBu_r', center=0, square=True,
                linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title('Korelasyon Matrisi', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/correlation_heatmap.png', dpi=150)
    plt.close()
    print("Korelasyon heatmap kaydedildi: data/correlation_heatmap.png")

    # 2. Network Gorseli
    if 'G' in dir() and len(G.edges()) > 0:
        plt.figure(figsize=(14, 12))

        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Kenar kalinliklari
        edge_weights = [G[u][v]['weight'] * 3 for u, v in G.edges()]

        # Dugum boyutlari (strength'e gore)
        node_sizes = [strength.get(v, 1) * 1000 + 500 for v in G.nodes()]

        # Kenar renkleri
        edge_colors = []
        for u, v in G.edges():
            r = cor_matrix.loc[u, v]
            edge_colors.append('green' if r > 0 else 'red')

        # Ciz
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                              node_color='lightblue', alpha=0.9)
        nx.draw_networkx_edges(G, pos, width=edge_weights,
                              edge_color=edge_colors, alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

        plt.title('Psychological Variables Network\n(Green=Positive, Red=Negative)',
                 fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('data/network_plot.png', dpi=150)
        plt.close()
        print("Network grafigi kaydedildi: data/network_plot.png")

    # 3. Centrality Bar Plot
    if 'centrality_df' in dir():
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))

        # Strength
        ax1 = axes[0, 0]
        centrality_sorted = centrality_df.sort_values('Strength', ascending=True)
        ax1.barh(centrality_sorted['Variable'], centrality_sorted['Strength'], color='steelblue')
        ax1.set_xlabel('Strength')
        ax1.set_title('Strength Centrality')

        # Betweenness
        ax2 = axes[0, 1]
        centrality_sorted = centrality_df.sort_values('Betweenness', ascending=True)
        ax2.barh(centrality_sorted['Variable'], centrality_sorted['Betweenness'], color='coral')
        ax2.set_xlabel('Betweenness')
        ax2.set_title('Betweenness Centrality')

        # Closeness
        ax3 = axes[1, 0]
        centrality_sorted = centrality_df.sort_values('Closeness', ascending=True)
        ax3.barh(centrality_sorted['Variable'], centrality_sorted['Closeness'], color='seagreen')
        ax3.set_xlabel('Closeness')
        ax3.set_title('Closeness Centrality')

        # Degree
        ax4 = axes[1, 1]
        centrality_sorted = centrality_df.sort_values('Degree', ascending=True)
        ax4.barh(centrality_sorted['Variable'], centrality_sorted['Degree'], color='purple')
        ax4.set_xlabel('Degree')
        ax4.set_title('Degree Centrality')

        plt.suptitle('Centrality Measures', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('data/centrality_plot.png', dpi=150)
        plt.close()
        print("Centrality grafigi kaydedildi: data/centrality_plot.png")

except ImportError as e:
    print(f"Gorsellestirme paketi eksik: {e}")

# =============================================================================
# ASAMA 10: OZET RAPOR
# =============================================================================

print("\n" + "=" * 60)
print("ANALIZ OZETI")
print("=" * 60)

print(f"""
VERI BILGISI:
- Toplam gozlem: {len(df)}
- Tam veri ile gozlem: {len(network_complete)}
- Degisken sayisi: {len(network_vars)}

EN GUCLU KORELASYONLAR:
""")

top_correlations = sig_edges_df.head(10)
for _, row in top_correlations.iterrows():
    sign = "+" if row['Correlation'] > 0 else ""
    print(f"  {row['From']} <-> {row['To']}: {sign}{row['Correlation']}")

if 'centrality_df' in dir():
    print(f"""
EN MERKEZI DEGISKENLER (Strength):
""")
    top_central = centrality_df.nlargest(5, 'Strength')
    for _, row in top_central.iterrows():
        print(f"  {row['Variable']}: {row['Strength']:.3f}")

print(f"""
OLUSTURULAN DOSYALAR:
- data/descriptives_python.csv
- data/correlation_matrix_python.csv
- data/significant_correlations_python.csv
- data/centrality_python.csv
- data/bn_edges_python.csv
- data/correlation_heatmap.png
- data/network_plot.png
- data/centrality_plot.png

ANALIZ TAMAMLANDI!
""")
