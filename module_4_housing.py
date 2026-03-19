"""
Module 4: Housing-Type Analysis
Voter counts by housing type, cross-tabbed with ethnicity and age. B40-proxy.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS, HOUSING_ORDER, ETHNICITY_ORDER


def run_module_4():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R11: Housing type summary
    ht_summary = df["housing_type"].value_counts().reindex(HOUSING_ORDER).fillna(0).astype(int)
    ht_summary_df = pd.DataFrame({"Voters": ht_summary, "Pct": (ht_summary / EXPECTED_ROWS * 100).round(2)})
    ht_summary_df.to_csv("outputs/csv/housing_type_summary.csv")
    print("Housing Type Summary:")
    print(ht_summary_df)

    if not (ht_summary.sum() == EXPECTED_ROWS):
        raise ValueError(f"Housing sum {ht_summary.sum()} != {EXPECTED_ROWS}")
    print(f"\nVerification: Housing total = {ht_summary.sum()} ✓")

    # R12: Housing × ethnicity
    ht_eth = pd.crosstab(df["housing_type"], df["estimated_ethnicity"])
    ht_eth = ht_eth.reindex(index=HOUSING_ORDER, columns=ETHNICITY_ORDER)
    ht_eth["Total"] = ht_eth.sum(axis=1)
    ht_eth.to_csv("outputs/csv/housing_ethnicity.csv")
    print("\nHousing × Ethnicity:")
    print(ht_eth)

    # Housing × age
    df_age = df[df["age_band"] != "Anomaly (100+)"]
    ht_age = pd.crosstab(df_age["housing_type"], df_age["age_band"])
    age_order = ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]
    ht_age = ht_age.reindex(index=HOUSING_ORDER, columns=age_order)
    ht_age["Total"] = ht_age.sum(axis=1)
    ht_age.to_csv("outputs/csv/housing_age.csv")
    print("\nHousing × Age:")
    print(ht_age)

    # R13: B40-proxy (PPR + Flat) vs middle-class (Taman + Condo)
    income_proxy = df["housing_type"].map({
        "PPR": "B40-proxy",
        "Flat": "B40-proxy",
        "Taman": "Middle-class",
        "Condo/Apartment": "Middle-class",
        "Institutional": "Institutional",
        "Other": "Other",
    })
    income_dm = pd.crosstab(df["NamaDM"], income_proxy)
    income_dm["Total"] = income_dm.sum(axis=1)
    income_dm = income_dm.sort_values("Total", ascending=False)
    income_dm.to_csv("outputs/csv/income_proxy.csv")
    print("\nB40-proxy vs Middle-class by DM:")
    print(income_dm)

    # Chart: Housing type donut chart
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = ["#F44336", "#FF9800", "#4CAF50", "#2196F3", "#9C27B0", "#9E9E9E"]
    wedges, texts, autotexts = ax.pie(
        ht_summary_df["Voters"], labels=ht_summary_df.index,
        autopct="%1.1f%%", colors=colors, pctdistance=0.8,
        wedgeprops=dict(width=0.4)
    )
    ax.set_title("P.118 Setiawangsa — Housing Type Distribution")
    plt.tight_layout()
    plt.savefig("outputs/charts/housing_type_donut.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/housing_type_donut.png")

    # Chart: B40 vs middle-class by DM
    fig, ax = plt.subplots(figsize=(14, 8))
    plot_cols = ["B40-proxy", "Middle-class", "Institutional"]
    avail_cols = [c for c in plot_cols if c in income_dm.columns]
    income_plot = income_dm[avail_cols].sort_values(avail_cols[0], ascending=True)
    income_plot.plot.barh(stacked=True, ax=ax,
                          color=["#F44336", "#4CAF50", "#9C27B0"])
    ax.set_xlabel("Number of Voters")
    ax.set_title("P.118 Setiawangsa — B40-Proxy vs Middle-Class by DM")
    ax.legend(title="Income Proxy")
    plt.tight_layout()
    plt.savefig("outputs/charts/b40_vs_middleclass.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/b40_vs_middleclass.png")

    print(f"\nModule 4 complete.")


if __name__ == "__main__":
    run_module_4()
