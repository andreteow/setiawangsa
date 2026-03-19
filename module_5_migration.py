"""
Module 5: Birth-State Migration Analysis
KL-born vs out-of-state breakdown. Top origin states.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from data_loader import EXPECTED_ROWS


def run_module_5():
    df = pd.read_parquet("outputs/enriched_voters.parquet")

    # R14-R15: KL-born vs out-of-state by DM
    import numpy as np
    origin_group = np.select(
        [df["birth_state_name"] == "W.P. Kuala Lumpur",
         df["birth_state_name"] == "Old IC (no state)"],
        ["KL-born", "Old IC (no state)"],
        default="Out-of-state",
    )

    origin_dm = pd.crosstab(df["NamaDM"], origin_group)
    origin_dm["Total"] = origin_dm.sum(axis=1)
    origin_dm = origin_dm.sort_values("Total", ascending=False)
    origin_dm.to_csv("outputs/csv/birth_state_by_dm.csv")
    print("Birth state by DM:")
    print(origin_dm)

    if not (origin_dm["Total"].sum() == EXPECTED_ROWS):
        raise ValueError(f"Sum {origin_dm['Total'].sum()} != {EXPECTED_ROWS}")
    print(f"\nVerification: Total = {origin_dm['Total'].sum()} ✓")

    # R16: Top origin states
    # Exclude KL and old IC for this ranking
    non_kl = df[(df["birth_state_name"] != "W.P. Kuala Lumpur") &
                (df["birth_state_name"] != "Old IC (no state)") &
                (df["birth_state_name"] != "Unknown Code")]
    top_states = non_kl["birth_state_name"].value_counts().head(15)
    top_states_df = pd.DataFrame({"Voters": top_states, "Pct": (top_states / EXPECTED_ROWS * 100).round(2)})
    top_states_df.to_csv("outputs/csv/top_origin_states.csv")
    print("\nTop origin states:")
    print(top_states_df)

    # Origin by DM (top 5 states)
    top5_states = top_states.head(5).index.tolist()
    origin_detail = df[df["birth_state_name"].isin(top5_states)]
    origin_by_dm = pd.crosstab(origin_detail["NamaDM"], origin_detail["birth_state_name"])
    origin_by_dm = origin_by_dm.reindex(columns=top5_states)
    origin_by_dm.to_csv("outputs/csv/origin_by_dm.csv")

    # Chart: Top 10 origin states
    fig, ax = plt.subplots(figsize=(10, 6))
    top10 = top_states.head(10)
    bars = ax.barh(top10.index[::-1], top10.values[::-1], color="#FF9800")
    ax.set_xlabel("Number of Voters")
    ax.set_title("P.118 Setiawangsa — Top 10 Birth States (excl. KL)")
    ax.bar_label(bars, fmt="%,.0f", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/top_origin_states.png", dpi=150)
    plt.close()
    print("\nChart saved: outputs/charts/top_origin_states.png")

    # Chart: KL-born % by DM
    kl_pct = (origin_dm.get("KL-born", 0) / origin_dm["Total"] * 100).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(kl_pct.index, kl_pct.values, color="#2196F3")
    ax.set_xlabel("KL-born %")
    ax.set_title("P.118 Setiawangsa — KL-Born Percentage by DM")
    ax.bar_label(bars, fmt="%.1f%%", fontsize=8)
    plt.tight_layout()
    plt.savefig("outputs/charts/kl_born_by_dm.png", dpi=150)
    plt.close()
    print("Chart saved: outputs/charts/kl_born_by_dm.png")

    print(f"\nModule 5 complete.")


if __name__ == "__main__":
    run_module_5()
