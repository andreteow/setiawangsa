"""
Module 9: Composite Priority Scoring
Weighted score combining youth, diversity, B40-proxy, and household density.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import INSTITUTIONAL_DMS

# Weights (must sum to 1.0)
W_YOUTH = 0.35
W_DIVERSITY = 0.25
W_B40 = 0.25
W_DENSITY = 0.15


def simpsons_diversity(row, ethnicity_cols):
    """Calculate Simpson's diversity index (1 - D)."""
    total = row[ethnicity_cols].sum()
    if total == 0:
        return 0
    proportions = row[ethnicity_cols] / total
    return 1 - (proportions ** 2).sum()


def normalize_series(s):
    """Min-max normalize to 0-1."""
    if s.max() == s.min():
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def score_area(df_area, group_col):
    """Compute priority scores for DMs or lokaliti."""
    df_age = df_area[df_area["age_band"] != "Anomaly (100+)"]

    # Group metrics
    groups = df_area.groupby(group_col)

    # 1. Youth concentration (% aged 22-39)
    youth_count = df_age[df_age["age_band"].isin(["22-27 (Youth)", "28-39 (Young Adult)"])].groupby(group_col).size()
    total_age = df_age.groupby(group_col).size()
    youth_pct = (youth_count / total_age).fillna(0)

    # 2. Ethnic diversity (Simpson's index)
    eth_counts = pd.crosstab(df_area[group_col], df_area["estimated_ethnicity"])
    eth_cols = ["Malay", "Chinese", "Indian", "Other"]
    for c in eth_cols:
        if c not in eth_counts.columns:
            eth_counts[c] = 0
    diversity = eth_counts.apply(lambda row: simpsons_diversity(row, eth_cols), axis=1)

    # 3. B40-proxy (% PPR + Flat)
    b40_count = df_area[df_area["housing_type"].isin(["PPR", "Flat"])].groupby(group_col).size()
    total = groups.size()
    b40_pct = (b40_count / total).fillna(0)

    # 4. Household density (avg voters per address)
    valid_addr = df_area[df_area["norumah_normalized"] != "MISSING"]
    hh = valid_addr.groupby([group_col, "Kodlokaliti", "norumah_normalized"]).size().reset_index(name="members")
    avg_hh_size = hh.groupby(group_col)["members"].mean()

    # Build scoring DataFrame
    scores = pd.DataFrame({
        "Total_Voters": total,
        "Youth_Pct": youth_pct,
        "Diversity_Index": diversity,
        "B40_Pct": b40_pct,
        "Avg_HH_Size": avg_hh_size,
    }).dropna()

    # Normalize all dimensions to 0-1
    scores["Youth_Norm"] = normalize_series(scores["Youth_Pct"])
    scores["Diversity_Norm"] = normalize_series(scores["Diversity_Index"])
    scores["B40_Norm"] = normalize_series(scores["B40_Pct"])
    scores["Density_Norm"] = normalize_series(scores["Avg_HH_Size"])

    # Composite score
    scores["Priority_Score"] = (
        W_YOUTH * scores["Youth_Norm"] +
        W_DIVERSITY * scores["Diversity_Norm"] +
        W_B40 * scores["B40_Norm"] +
        W_DENSITY * scores["Density_Norm"]
    ).round(4)

    scores = scores.sort_values("Priority_Score", ascending=False)
    scores["Rank"] = range(1, len(scores) + 1)

    return scores


def run_module_9():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # Exclude institutional DMs from ranking
    df_civilian = df[~df["NamaDM"].isin(INSTITUTIONAL_DMS)]
    print(f"Scoring {len(df_civilian):,} civilian voters (excluding MINDEF/PULAPOL)")

    # Score DMs
    print("\n--- DM Priority Ranking ---")
    dm_scores = score_area(df_civilian, "NamaDM")
    dm_scores.to_csv("outputs/csv/priority_ranking_dm.csv")
    display_cols = ["Rank", "Total_Voters", "Youth_Pct", "Diversity_Index",
                    "B40_Pct", "Avg_HH_Size", "Priority_Score"]
    print(dm_scores[display_cols].to_string())

    # Score lokaliti (top 20)
    print("\n--- Top 20 Lokaliti Priority Ranking ---")
    # Filter to lokaliti with at least 50 voters for meaningful stats
    lok_counts = df_civilian.groupby("NamaLokaliti").size()
    large_lok = lok_counts[lok_counts >= 50].index
    df_large = df_civilian[df_civilian["NamaLokaliti"].isin(large_lok)]
    lok_scores = score_area(df_large, "NamaLokaliti")
    lok_scores.to_csv("outputs/csv/priority_ranking_lokaliti.csv")
    print(lok_scores.head(20)[display_cols].to_string())

    # Print actionable summary
    print(f"\n{'=' * 60}")
    print("CANVASSING PRIORITY RECOMMENDATIONS")
    print(f"{'=' * 60}")
    print(f"\nWeights: Youth {W_YOUTH}, Diversity {W_DIVERSITY}, B40 {W_B40}, Density {W_DENSITY}")
    print(f"\nTop 5 DMs for canvassing:")
    for _, row in dm_scores.head(5).iterrows():
        print(f"  {int(row['Rank'])}. {row.name} (score: {row['Priority_Score']:.3f}, "
              f"voters: {int(row['Total_Voters']):,})")
    print(f"\nTop 10 Lokaliti for canvassing:")
    for _, row in lok_scores.head(10).iterrows():
        print(f"  {int(row['Rank'])}. {row.name} (score: {row['Priority_Score']:.3f}, "
              f"voters: {int(row['Total_Voters']):,})")

    # Chart: Priority ranking (DMs)
    fig, ax = plt.subplots(figsize=(12, 8))
    dm_plot = dm_scores.sort_values("Priority_Score", ascending=True)
    colors = plt.cm.RdYlGn(dm_plot["Priority_Score"] / dm_plot["Priority_Score"].max())
    bars = ax.barh(dm_plot.index, dm_plot["Priority_Score"], color=colors)
    ax.set_xlabel("Composite Priority Score")
    ax.set_title("P.118 Setiawangsa — DM Canvassing Priority (excl. Institutional)")
    ax.bar_label(bars, fmt="%.3f", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/priority_ranking_dm.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/priority_ranking_dm.png")

    # Chart: Top 20 lokaliti priority
    fig, ax = plt.subplots(figsize=(12, 10))
    top20 = lok_scores.head(20).sort_values("Priority_Score", ascending=True)
    colors = plt.cm.RdYlGn(top20["Priority_Score"] / top20["Priority_Score"].max())
    bars = ax.barh(top20.index, top20["Priority_Score"], color=colors)
    ax.set_xlabel("Composite Priority Score")
    ax.set_title("P.118 Setiawangsa — Top 20 Lokaliti Canvassing Priority")
    ax.bar_label(bars, fmt="%.3f", fontsize=7)
    plt.tight_layout()
    plt.savefig("outputs/charts/priority_ranking_lokaliti.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/priority_ranking_lokaliti.png")

    print(f"\nModule 9 complete.")


if __name__ == "__main__":
    run_module_9()
