"""
Module 2: Age Segmentation Analysis
Age band distribution overall, by DM, by gender. Youth concentration.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS, AGE_BAND_ORDER


def run_module_2():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # Exclude anomalies from age analysis
    anomalies = df[df["age_band"] == "Anomaly (100+)"]
    df_age = df[df["age_band"] != "Anomaly (100+)"]
    print(f"Excluded {len(anomalies)} anomaly records (age 100+) from age analysis")

    # R4-R5: Age band by DM
    age_dm = pd.crosstab(df_age["NamaDM"], df_age["age_band"])
    age_dm = age_dm.reindex(columns=AGE_BAND_ORDER)
    age_dm["Total"] = age_dm.sum(axis=1)
    age_dm = age_dm.sort_values("Total", ascending=False)
    age_dm.to_csv("outputs/csv/age_by_dm.csv")
    print("\nAge by DM:")
    print(age_dm)

    # Age band by gender
    age_gender = pd.crosstab(df_age["age_band"], df_age["Jantina"])
    age_gender = age_gender.rename(columns={"L": "Male", "P": "Female"})
    age_gender = age_gender.reindex(AGE_BAND_ORDER)
    age_gender["Total"] = age_gender.sum(axis=1)
    age_gender.to_csv("outputs/csv/age_by_gender.csv")
    print("\nAge by Gender:")
    print(age_gender)

    # Verification
    age_total = age_dm["Total"].sum()
    expected_age = EXPECTED_ROWS - len(anomalies)
    if not (age_total == expected_age):
        raise ValueError(f"Age sum {age_total} != {expected_age}")
    print(f"\nVerification: Age total = {age_total} (excl. {len(anomalies)} anomalies) ✓")

    # R6: Youth concentration by DM
    youth_cols = ["22-27 (Youth)", "28-39 (Young Adult)"]
    youth_conc = age_dm[youth_cols].sum(axis=1) / age_dm["Total"] * 100
    youth_conc = youth_conc.round(2).sort_values(ascending=False)
    youth_df = pd.DataFrame({
        "Youth_Young_Adult_Pct": youth_conc,
        "Youth_22_27": age_dm["22-27 (Youth)"],
        "Young_Adult_28_39": age_dm["28-39 (Young Adult)"],
        "Total": age_dm["Total"],
    })
    youth_df.to_csv("outputs/csv/youth_concentration.csv")
    print("\nR6: Youth + Young Adult concentration by DM:")
    print(youth_df)

    # Chart: Population pyramid
    fig, ax = plt.subplots(figsize=(10, 6))
    male_counts = []
    female_counts = []
    for band in AGE_BAND_ORDER:
        male_counts.append(-df_age[(df_age["age_band"] == band) & (df_age["Jantina"] == "L")].shape[0])
        female_counts.append(df_age[(df_age["age_band"] == band) & (df_age["Jantina"] == "P")].shape[0])

    y_pos = np.arange(len(AGE_BAND_ORDER))
    ax.barh(y_pos, male_counts, color="#2196F3", label="Male")
    ax.barh(y_pos, female_counts, color="#E91E63", label="Female")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(AGE_BAND_ORDER)
    ax.set_xlabel("Number of Voters")
    ax.set_title("P.118 Setiawangsa — Population Pyramid by Age Band")
    ax.legend()
    # Add count labels
    for i, (m, f) in enumerate(zip(male_counts, female_counts)):
        ax.text(m - 200, i, f"{abs(m):,}", ha="right", va="center", fontsize=8)
        ax.text(f + 200, i, f"{f:,}", ha="left", va="center", fontsize=8)
    ax.axvline(0, color="black", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("outputs/charts/population_pyramid.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/population_pyramid.png")

    # Chart: Youth % by DM
    fig, ax = plt.subplots(figsize=(12, 8))
    youth_sorted = youth_conc.sort_values(ascending=True)
    colors = ["#FF5722" if v > 45 else "#4CAF50" for v in youth_sorted]
    bars = ax.barh(youth_sorted.index, youth_sorted.values, color=colors)
    ax.set_xlabel("Youth + Young Adult % (age 22-39)")
    ax.set_title("P.118 Setiawangsa — Youth Concentration by DM")
    ax.bar_label(bars, fmt="%.1f%%", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/youth_by_dm.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/youth_by_dm.png")

    print(f"\nModule 2 complete.")


if __name__ == "__main__":
    run_module_2()
