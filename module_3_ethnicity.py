"""
Module 3: Ethnicity Analysis
Ethnic composition by DM, age band, gender. Methodology report.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS, ETHNICITY_ORDER, AGE_BAND_ORDER


def run_module_3():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R9: Ethnicity by DM
    eth_dm = pd.crosstab(df["NamaDM"], df["estimated_ethnicity"])
    eth_dm = eth_dm.reindex(columns=ETHNICITY_ORDER)
    eth_dm["Total"] = eth_dm.sum(axis=1)
    eth_dm = eth_dm.sort_values("Total", ascending=False)
    eth_dm.to_csv("outputs/csv/ethnicity_by_dm.csv")
    print("Ethnicity by DM:")
    print(eth_dm)

    # Verification
    if not (eth_dm["Total"].sum() == EXPECTED_ROWS):
        raise ValueError(f"Ethnicity sum {eth_dm['Total'].sum()} != {EXPECTED_ROWS}")
    print(f"\nVerification: Ethnicity total = {eth_dm['Total'].sum()} ✓")

    # Ethnicity by age band (excl anomalies)
    df_age = df[df["age_band"] != "Anomaly (100+)"]
    eth_age = pd.crosstab(df_age["age_band"], df_age["estimated_ethnicity"])
    eth_age = eth_age.reindex(index=AGE_BAND_ORDER, columns=ETHNICITY_ORDER)
    eth_age.to_csv("outputs/csv/ethnicity_by_age.csv")
    print("\nEthnicity by Age Band:")
    print(eth_age)

    # Ethnicity by gender
    eth_gender = pd.crosstab(df["estimated_ethnicity"], df["Jantina"])
    eth_gender = eth_gender.rename(columns={"L": "Male", "P": "Female"})
    eth_gender.to_csv("outputs/csv/ethnicity_by_gender.csv")
    print("\nEthnicity by Gender:")
    print(eth_gender)

    # R10: Ethnic composition per DM (percentages)
    eth_pct = eth_dm[ETHNICITY_ORDER].div(eth_dm["Total"], axis=0) * 100
    eth_pct = eth_pct.round(2)
    eth_pct["Total_Voters"] = eth_dm["Total"]
    eth_pct.to_csv("outputs/csv/dm_ethnic_composition.csv")
    print("\nEthnic composition % per DM:")
    print(eth_pct)

    # Methodology report
    confidence_counts = df["ethnicity_confidence"].value_counts()
    methodology = f"""ETHNICITY INFERENCE METHODOLOGY
================================

Approach: Multi-signal hierarchical classification

Signal Hierarchy (highest priority first):
1. Definitive markers (confidence: high)
   - A/L or A/P in name → Indian
   - BIN or BINTI in name → Malay

2. Name pattern matching (confidence: medium)
   - Chinese surname list (~156 entries with romanization variants)
   - Indian name list (~111 common names)
   - Malay first name list (~90 common names)

3. Birth-state refinement (adjusts confidence)
   - MyKad state codes mapped to 76 states/regions
   - Kelantan/Terengganu → strengthens Malay signal
   - Sabah/Sarawak with no Malay/Chinese/Indian match → Other

4. Fallback
   - No signals match → "Other" with confidence "low"

Results:
  Total classified: {EXPECTED_ROWS:,}
  Malay: {(df['estimated_ethnicity'] == 'Malay').sum():,} ({(df['estimated_ethnicity'] == 'Malay').mean()*100:.1f}%)
  Chinese: {(df['estimated_ethnicity'] == 'Chinese').sum():,} ({(df['estimated_ethnicity'] == 'Chinese').mean()*100:.1f}%)
  Indian: {(df['estimated_ethnicity'] == 'Indian').sum():,} ({(df['estimated_ethnicity'] == 'Indian').mean()*100:.1f}%)
  Other: {(df['estimated_ethnicity'] == 'Other').sum():,} ({(df['estimated_ethnicity'] == 'Other').mean()*100:.1f}%)

Confidence Distribution:
  High: {confidence_counts.get('high', 0):,} ({confidence_counts.get('high', 0)/EXPECTED_ROWS*100:.1f}%)
  Medium: {confidence_counts.get('medium', 0):,} ({confidence_counts.get('medium', 0)/EXPECTED_ROWS*100:.1f}%)
  Low: {confidence_counts.get('low', 0):,} ({confidence_counts.get('low', 0)/EXPECTED_ROWS*100:.1f}%)

Limitations:
- Ethnicity is inferred from name patterns and birth state, not self-reported
- Non-Malay Muslims with bin/binti will be classified as Malay (overcount)
- "Other" category includes Bumiputera Sabah/Sarawak, Orang Asli, mixed, and unclassifiable
- Old-format IC holders ({(df['birth_state_name'] == 'Old IC (no state)').sum():,} records) lack birth state refinement
- Chinese names without a recognized surname in first position may be missed

Validation:
- A 200-per-ethnicity random sample (800 total) is exported to
  outputs/csv/ethnicity_validation_sample.csv for manual accuracy review
"""
    with open("outputs/csv/ethnicity_methodology.txt", "w") as f:
        f.write(methodology)
    print("\nMethodology report saved: outputs/csv/ethnicity_methodology.txt")

    # Validation sample: 200 per ethnicity (PII-safe — no names, parquet has no PII)
    samples = []
    for eth in ETHNICITY_ORDER:
        eth_df = df[df["estimated_ethnicity"] == eth]
        n = min(200, len(eth_df))
        sample = eth_df.sample(n, random_state=42)
        sample = sample[["estimated_ethnicity", "ethnicity_confidence",
                         "ethnicity_signals", "age_band", "NamaDM"]].copy()
        samples.append(sample)
    validation = pd.concat(samples, ignore_index=True)
    validation.to_csv("outputs/csv/ethnicity_validation_sample.csv", index=False)
    print(f"Validation sample saved: {len(validation)} records")

    # Chart: Stacked bar of ethnic composition per DM
    fig, ax = plt.subplots(figsize=(14, 8))
    eth_pct_plot = eth_pct[ETHNICITY_ORDER].sort_values("Malay", ascending=True)
    colors = {"Malay": "#4CAF50", "Chinese": "#F44336", "Indian": "#FF9800", "Other": "#9E9E9E"}
    eth_pct_plot.plot.barh(stacked=True, ax=ax,
                           color=[colors[e] for e in ETHNICITY_ORDER])
    ax.set_xlabel("Percentage (%)")
    ax.set_title("P.118 Setiawangsa — Ethnic Composition by DM")
    ax.legend(title="Ethnicity", loc="lower right")
    plt.tight_layout()
    plt.savefig("outputs/charts/ethnicity_by_dm.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/ethnicity_by_dm.png")

    # Chart: Ethnicity × age band heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    eth_age_pct = eth_age.div(eth_age.sum(axis=1), axis=0) * 100
    im = ax.imshow(eth_age_pct.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(ETHNICITY_ORDER)))
    ax.set_xticklabels(ETHNICITY_ORDER)
    ax.set_yticks(range(len(AGE_BAND_ORDER)))
    ax.set_yticklabels(AGE_BAND_ORDER)
    # Add text annotations
    for i in range(len(AGE_BAND_ORDER)):
        for j in range(len(ETHNICITY_ORDER)):
            val = eth_age_pct.iloc[i, j]
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center", fontsize=10)
    ax.set_title("P.118 Setiawangsa — Ethnicity × Age Band (%)")
    fig.colorbar(im, ax=ax, label="% within age band")
    plt.tight_layout()
    plt.savefig("outputs/charts/ethnicity_age_heatmap.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/ethnicity_age_heatmap.png")

    print(f"\nModule 3 complete.")


if __name__ == "__main__":
    run_module_3()
