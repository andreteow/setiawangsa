"""
Module 6: Household Clustering
Group by normalized address + locality code. Household size distribution.
Multi-generational households.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS


def run_module_6():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # Separate missing NoRumah
    df_missing = df[df["norumah_normalized"] == "MISSING"]
    df_valid = df[df["norumah_normalized"] != "MISSING"]
    print(f"Valid NoRumah records: {len(df_valid):,}")
    print(f"Missing NoRumah records: {len(df_missing):,}")

    # R17: Group by norumah_normalized + Kodlokaliti
    households = df_valid.groupby(["Kodlokaliti", "norumah_normalized"]).agg(
        Members=("NoSiri", "size"),
        NamaLokaliti=("NamaLokaliti", "first"),
        NamaDM=("NamaDM", "first"),
    ).reset_index()
    households = households.sort_values("Members", ascending=False)
    households.to_csv("outputs/csv/household_clusters.csv", index=False)
    print(f"\nTotal household clusters: {len(households):,}")
    print(f"Total voters in clusters: {households['Members'].sum():,}")

    # Verification
    total = households["Members"].sum() + len(df_missing)
    if not (total == EXPECTED_ROWS):
        raise ValueError(f"Household sum {total} != {EXPECTED_ROWS}")
    print(f"Verification: {households['Members'].sum():,} + {len(df_missing):,} missing = {total:,} ✓")

    # R18: Household size distribution
    size_bins = pd.cut(households["Members"],
                       bins=[0, 1, 3, 6, 9, float("inf")],
                       labels=["1 (Single)", "2-3 (Small)", "4-6 (Medium)", "7-9 (Large)", "10+ (Very Large)"])
    size_dist = size_bins.value_counts().sort_index()
    size_voters = households.groupby(size_bins, observed=True)["Members"].sum().sort_index()
    size_df = pd.DataFrame({
        "Households": size_dist,
        "Voters": size_voters,
        "Avg_Size": (size_voters / size_dist).round(2),
    })
    size_df.to_csv("outputs/csv/household_size_distribution.csv")
    print("\nHousehold size distribution:")
    print(size_df)

    # R19: Multi-generational households (3+ age bands at same address)
    df_valid_agecheck = df_valid[df_valid["age_band"] != "Anomaly (100+)"]
    hh_age_bands = df_valid_agecheck.groupby(
        ["Kodlokaliti", "norumah_normalized"]
    )["age_band"].nunique().reset_index(name="distinct_age_bands")

    multigenerational = hh_age_bands[hh_age_bands["distinct_age_bands"] >= 3]
    # Get details
    multi_details = multigenerational.merge(households, on=["Kodlokaliti", "norumah_normalized"])
    multi_details = multi_details.sort_values("Members", ascending=False)
    multi_details.to_csv("outputs/csv/multigenerational_households.csv", index=False)
    print(f"\nMulti-generational households (3+ age bands): {len(multigenerational):,}")
    print(f"Total voters in multi-gen households: {multi_details['Members'].sum():,}")

    # Multi-gen % by DM
    multi_by_dm = multi_details.groupby("NamaDM").agg(
        MultiGen_Households=("Members", "size"),
        MultiGen_Voters=("Members", "sum"),
    )
    total_by_dm = households.groupby("NamaDM").agg(Total_Households=("Members", "size"))
    multi_dm = multi_by_dm.join(total_by_dm)
    multi_dm["MultiGen_Pct"] = (multi_dm["MultiGen_Households"] / multi_dm["Total_Households"] * 100).round(2)
    multi_dm = multi_dm.sort_values("MultiGen_Pct", ascending=False)
    print("\nMulti-generational % by DM:")
    print(multi_dm)

    # Chart: Household size distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(size_df.index.astype(str), size_df["Households"], color="#4CAF50")
    ax.set_xlabel("Household Size")
    ax.set_ylabel("Number of Households")
    ax.set_title("P.118 Setiawangsa — Household Size Distribution")
    ax.bar_label(bars, fmt="%,.0f", fontsize=9)
    # Add voter count as secondary label
    for i, (idx, row) in enumerate(size_df.iterrows()):
        ax.text(i, row["Households"] + max(size_df["Households"]) * 0.02,
                f"({row['Voters']:,.0f} voters)", ha="center", fontsize=7, color="gray")
    plt.tight_layout()
    plt.savefig("outputs/charts/household_size_dist.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/household_size_dist.png")

    # Chart: Multi-gen % by DM
    fig, ax = plt.subplots(figsize=(12, 8))
    multi_dm_sorted = multi_dm["MultiGen_Pct"].sort_values(ascending=True)
    bars = ax.barh(multi_dm_sorted.index, multi_dm_sorted.values, color="#9C27B0")
    ax.set_xlabel("Multi-Generational Household %")
    ax.set_title("P.118 Setiawangsa — Multi-Generational Households by DM")
    ax.bar_label(bars, fmt="%.1f%%", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/multigenerational_by_dm.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/multigenerational_by_dm.png")

    print(f"\nModule 6 complete.")


if __name__ == "__main__":
    run_module_6()
