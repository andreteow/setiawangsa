"""
Module 1: Voter Concentration Map
Ranks DMs and lokaliti by voter count with demographic breakdowns.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS


def run_module_1():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R1: DM voter counts with gender breakdown
    dm_gender = pd.crosstab(df["NamaDM"], df["Jantina"], margins=True)
    dm_gender = dm_gender.rename(columns={"L": "Male", "P": "Female", "All": "Total"})
    dm_gender = dm_gender.sort_values("Total", ascending=False)
    dm_gender.index.name = "DM"
    dm_gender.to_csv("outputs/csv/dm_voter_counts.csv")
    print("R1: DM voter counts with gender breakdown")
    print(dm_gender)

    # Verification: sum check
    dm_only = dm_gender.drop("All", errors="ignore")
    if not (dm_only["Total"].sum() == EXPECTED_ROWS):
        raise ValueError(f"DM sum {dm_only['Total'].sum()} != {EXPECTED_ROWS}")
    print(f"\nVerification: DM total = {dm_only['Total'].sum()} ✓")

    # R2: Lokaliti ranked by voter count
    lok_counts = df.groupby("NamaLokaliti").size().reset_index(name="Voters")
    lok_counts = lok_counts.sort_values("Voters", ascending=False).reset_index(drop=True)
    lok_counts.index = lok_counts.index + 1
    lok_counts.index.name = "Rank"
    lok_counts.to_csv("outputs/csv/lokaliti_all_ranked.csv")
    lok_counts.head(20).to_csv("outputs/csv/lokaliti_top20.csv")
    print(f"\nR2: Top 20 Lokaliti")
    print(lok_counts.head(20))

    # R3: DM as % of total
    dm_share = dm_only[["Total"]].copy()
    dm_share["Pct"] = (dm_share["Total"] / EXPECTED_ROWS * 100).round(2)
    dm_share = dm_share.sort_values("Total", ascending=False)
    dm_share.to_csv("outputs/csv/dm_share_pct.csv")
    print(f"\nR3: DM share of total")
    print(dm_share)

    # Chart 1: Horizontal bar chart of DM voter counts (stacked by gender)
    dm_plot = dm_only.drop("Total", axis=1).sort_values(
        dm_only.columns[0], ascending=True  # sort for horizontal bar
    )
    # Re-sort by total for chart
    dm_plot["_total"] = dm_plot.sum(axis=1)
    dm_plot = dm_plot.sort_values("_total", ascending=True).drop("_total", axis=1)

    fig, ax = plt.subplots(figsize=(12, 8))
    dm_plot.plot.barh(stacked=True, ax=ax, color=["#2196F3", "#E91E63"])
    ax.set_xlabel("Number of Voters")
    ax.set_title("P.118 Setiawangsa — Voters by Daerah Mengundi (Gender)")
    ax.legend(title="Gender")
    for container in ax.containers:
        ax.bar_label(container, fmt="%,.0f", label_type="center", fontsize=7)
    plt.tight_layout()
    plt.savefig("outputs/charts/dm_voter_counts.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/dm_voter_counts.png")

    # Chart 2: Top 20 lokaliti bar chart
    top20 = lok_counts.head(20).copy()
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(top20["NamaLokaliti"], top20["Voters"], color="#4CAF50")
    ax.invert_yaxis()
    ax.set_xlabel("Number of Voters")
    ax.set_title("P.118 Setiawangsa — Top 20 Lokaliti by Voter Count")
    ax.bar_label(bars, fmt="%,.0f", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/lokaliti_top20.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/lokaliti_top20.png")

    print(f"\nModule 1 complete. {EXPECTED_ROWS:,} voters accounted for.")


if __name__ == "__main__":
    run_module_1()
