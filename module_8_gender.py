"""
Module 8: Gender Ratio Analysis
Gender ratio per DM and lokaliti. Flag areas with >60% one gender.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS, INSTITUTIONAL_DMS


def run_module_8():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R22: Gender ratio per DM
    gender_dm = pd.crosstab(df["NamaDM"], df["Jantina"])
    gender_dm = gender_dm.rename(columns={"L": "Male", "P": "Female"})
    gender_dm["Total"] = gender_dm.sum(axis=1)
    gender_dm["Male_Pct"] = (gender_dm["Male"] / gender_dm["Total"] * 100).round(2)
    gender_dm["Female_Pct"] = (gender_dm["Female"] / gender_dm["Total"] * 100).round(2)
    gender_dm = gender_dm.sort_values("Total", ascending=False)
    gender_dm.to_csv("outputs/csv/gender_ratio_dm.csv")
    print("Gender ratio by DM:")
    print(gender_dm)

    if not (gender_dm["Total"].sum() == EXPECTED_ROWS):
        raise ValueError(f"Sum {gender_dm['Total'].sum()} != {EXPECTED_ROWS}")
    print(f"\nVerification: Total = {gender_dm['Total'].sum()} ✓")

    # Gender ratio per lokaliti
    gender_lok = pd.crosstab(df["NamaLokaliti"], df["Jantina"])
    gender_lok = gender_lok.rename(columns={"L": "Male", "P": "Female"})
    gender_lok["Total"] = gender_lok.sum(axis=1)
    gender_lok["Male_Pct"] = (gender_lok["Male"] / gender_lok["Total"] * 100).round(2)
    gender_lok = gender_lok.sort_values("Total", ascending=False)
    gender_lok.to_csv("outputs/csv/gender_ratio_lokaliti.csv")

    # R23: Flag areas with >60% one gender
    skewed = gender_lok[(gender_lok["Male_Pct"] > 60) | (gender_lok["Male_Pct"] < 40)]
    skewed = skewed.copy()
    skewed["Skew_Direction"] = skewed["Male_Pct"].apply(
        lambda x: "Male-heavy" if x > 60 else "Female-heavy"
    )
    # Add DM info
    lok_dm = df.groupby("NamaLokaliti")["NamaDM"].first()
    skewed["NamaDM"] = skewed.index.map(lok_dm)
    skewed["Is_Institutional"] = skewed["NamaDM"].isin(INSTITUTIONAL_DMS)
    skewed = skewed.sort_values("Male_Pct", ascending=False)
    skewed.to_csv("outputs/csv/gender_skew_areas.csv")
    print(f"\nGender-skewed areas (>60% one gender): {len(skewed)}")
    print(f"  Institutional (expected): {skewed['Is_Institutional'].sum()}")
    print(f"  Non-institutional: {(~skewed['Is_Institutional']).sum()}")
    # Show non-institutional skewed
    non_inst_skew = skewed[~skewed["Is_Institutional"]]
    if len(non_inst_skew) > 0:
        print("\nNon-institutional gender-skewed areas:")
        print(non_inst_skew[["Male", "Female", "Total", "Male_Pct", "Skew_Direction", "NamaDM"]].head(20))

    # Chart: Gender ratio by DM (diverging bar chart)
    fig, ax = plt.subplots(figsize=(12, 8))
    dm_sorted = gender_dm.sort_values("Male_Pct", ascending=True)
    deviation = dm_sorted["Male_Pct"] - 50
    colors = ["#2196F3" if d > 0 else "#E91E63" for d in deviation]
    bars = ax.barh(dm_sorted.index, deviation, color=colors)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Deviation from 50% (positive = more male)")
    ax.set_title("P.118 Setiawangsa — Gender Ratio Deviation by DM")
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in dm_sorted["Male_Pct"]], fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/gender_ratio_dm.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/gender_ratio_dm.png")

    print(f"\nModule 8 complete.")


if __name__ == "__main__":
    run_module_8()
