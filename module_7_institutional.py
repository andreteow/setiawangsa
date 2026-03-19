"""
Module 7: Institutional Voter Blocks
Profile MINDEF and PULAPOL DMs. Institutional vs civilian comparison.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS, INSTITUTIONAL_DMS


def run_module_7():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R20: Filter institutional DMs
    inst = df[df["NamaDM"].isin(INSTITUTIONAL_DMS)]
    civilian = df[~df["NamaDM"].isin(INSTITUTIONAL_DMS)]

    print(f"Institutional voters (MINDEF + PULAPOL): {len(inst):,}")
    print(f"Civilian voters: {len(civilian):,}")

    # Verification
    if not (len(inst) + len(civilian) == EXPECTED_ROWS):
        raise ValueError(f"Sum {len(inst) + len(civilian)} != {EXPECTED_ROWS}")
    print(f"Verification: {len(inst):,} + {len(civilian):,} = {EXPECTED_ROWS:,} ✓")

    # R21: Full demographic profile
    profile_data = []
    for label, subset in [("MINDEF", df[df["NamaDM"] == "MINDEF"]),
                           ("PULAPOL", df[df["NamaDM"] == "PULAPOL"]),
                           ("Institutional Total", inst),
                           ("Civilian Total", civilian),
                           ("Constituency Total", df)]:
        row = {
            "Group": label,
            "Total": len(subset),
            "Pct_of_Total": round(len(subset) / EXPECTED_ROWS * 100, 2),
            "Male": (subset["Jantina"] == "L").sum(),
            "Female": (subset["Jantina"] == "P").sum(),
            "Male_Pct": round((subset["Jantina"] == "L").mean() * 100, 1),
        }
        # Age bands (excl anomalies)
        age_sub = subset[subset["age_band"] != "Anomaly (100+)"]
        for band in ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]:
            row[band] = (age_sub["age_band"] == band).sum()
            row[f"{band}_Pct"] = round((age_sub["age_band"] == band).mean() * 100, 1) if len(age_sub) > 0 else 0

        # Ethnicity
        for eth in ["Malay", "Chinese", "Indian", "Other"]:
            row[eth] = (subset["estimated_ethnicity"] == eth).sum()
            row[f"{eth}_Pct"] = round((subset["estimated_ethnicity"] == eth).mean() * 100, 1)

        profile_data.append(row)

    profile = pd.DataFrame(profile_data)
    profile.to_csv("outputs/csv/institutional_profile.csv", index=False)
    print("\nInstitutional Profile:")
    # Print key columns
    display_cols = ["Group", "Total", "Pct_of_Total", "Male_Pct", "Malay_Pct", "Chinese_Pct", "Indian_Pct"]
    print(profile[display_cols].to_string(index=False))

    # Strategic note
    print(f"\n--- Strategic Note ---")
    print(f"Institutional voters: {len(inst):,} ({len(inst)/EXPECTED_ROWS*100:.1f}% of constituency)")
    print(f"These voters (military/police) historically lean pro-government.")
    print(f"MUDA's effective electorate is ~{len(civilian):,} civilian voters.")
    print(f"Institutional DMs are {inst['Jantina'].value_counts().get('L', 0)/len(inst)*100:.0f}% male.")

    # Chart: Institutional vs civilian comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Gender comparison
    labels = ["Institutional", "Civilian"]
    male_pcts = [
        (inst["Jantina"] == "L").mean() * 100,
        (civilian["Jantina"] == "L").mean() * 100,
    ]
    female_pcts = [100 - m for m in male_pcts]
    x = range(len(labels))
    axes[0].bar(x, male_pcts, label="Male", color="#2196F3")
    axes[0].bar(x, female_pcts, bottom=male_pcts, label="Female", color="#E91E63")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    axes[0].set_ylabel("%")
    axes[0].set_title("Gender Split")
    axes[0].legend()

    # Ethnicity comparison
    for i, (label, subset) in enumerate([("Institutional", inst), ("Civilian", civilian)]):
        eth_pcts = [
            (subset["estimated_ethnicity"] == e).mean() * 100
            for e in ["Malay", "Chinese", "Indian", "Other"]
        ]
        axes[1].bar([j + i * 0.35 for j in range(4)], eth_pcts, width=0.35, label=label)
    axes[1].set_xticks(range(4))
    axes[1].set_xticklabels(["Malay", "Chinese", "Indian", "Other"])
    axes[1].set_ylabel("%")
    axes[1].set_title("Ethnic Composition")
    axes[1].legend()

    # Age comparison
    age_bands = ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]
    for i, (label, subset) in enumerate([("Institutional", inst), ("Civilian", civilian)]):
        sub_age = subset[subset["age_band"] != "Anomaly (100+)"]
        age_pcts = [(sub_age["age_band"] == b).mean() * 100 for b in age_bands]
        axes[2].bar([j + i * 0.35 for j in range(4)], age_pcts, width=0.35, label=label)
    axes[2].set_xticks(range(4))
    axes[2].set_xticklabels(["Youth", "Y.Adult", "Mid", "Senior"], fontsize=8)
    axes[2].set_ylabel("%")
    axes[2].set_title("Age Distribution")
    axes[2].legend()

    fig.suptitle("P.118 Setiawangsa — Institutional vs Civilian Voters", fontsize=13)
    plt.tight_layout()
    plt.savefig("outputs/charts/institutional_vs_civilian.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/institutional_vs_civilian.png")

    print(f"\nModule 7 complete.")


if __name__ == "__main__":
    run_module_7()
