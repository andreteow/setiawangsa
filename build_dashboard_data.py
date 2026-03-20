"""
Build dashboard JSON data files from the analysis pipeline CSV outputs.
Reads from outputs/csv/ and writes to dashboard/data/.

No PII is included — all data is aggregated at lokaliti level or higher.
"""

import json
import os
import re

import pandas as pd

CSV_DIR = "outputs/csv"
OUT_DIR = "dashboard/data"
DM_DIR = os.path.join(OUT_DIR, "dm")


def slugify(name):
    """Convert DM name to URL-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def read_csv(filename):
    return pd.read_csv(os.path.join(CSV_DIR, filename))


def to_dict_clean(df, orient="records"):
    """Convert DataFrame to dict, replacing NaN with None."""
    return json.loads(df.to_json(orient=orient))


def write_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print(f"  wrote {filepath} ({os.path.getsize(filepath):,} bytes)")


def build_overview():
    """Build overview.json with constituency-level headline stats."""
    dm_voters = read_csv("dm_voter_counts.csv")
    age_gender = read_csv("age_by_gender.csv")
    ethnicity_dm = read_csv("ethnicity_by_dm.csv")
    youth = read_csv("youth_concentration.csv")
    income = read_csv("income_proxy.csv")
    priority = read_csv("priority_ranking_dm.csv")
    gender_dm = read_csv("gender_ratio_dm.csv")

    # Totals from the "All" row
    all_row = dm_voters[dm_voters["DM"] == "All"].iloc[0]
    total = int(all_row["Total"])
    male = int(all_row["Male"])
    female = int(all_row["Female"])

    # Age bands
    age_bands = {}
    for _, row in age_gender.iterrows():
        age_bands[row["age_band"]] = int(row["Total"])

    # Ethnicity totals
    eth_totals = ethnicity_dm[["Malay", "Chinese", "Indian", "Other"]].sum()
    ethnicity = {k: int(v) for k, v in eth_totals.items()}

    # Youth % (constituency-wide)
    youth_total = youth["Youth_22_27"].sum() + youth["Young_Adult_28_39"].sum()
    voter_total = youth["Total"].sum()
    youth_pct = round(youth_total / voter_total * 100, 1) if voter_total else 0

    # B40 %
    b40_total = income["B40-proxy"].sum()
    b40_pct = round(b40_total / total * 100, 1)

    # DM summary
    dm_data = dm_voters[dm_voters["DM"] != "All"].copy()
    priority_lookup = dict(zip(priority["NamaDM"], priority["Rank"]))
    youth_lookup = dict(zip(youth["NamaDM"], youth["Youth_Young_Adult_Pct"]))
    b40_lookup = {}
    for _, row in income.iterrows():
        dm_total = row["Total"]
        b40_lookup[row["NamaDM"]] = round(row["B40-proxy"] / dm_total * 100, 1) if dm_total else 0

    dm_summary = []
    for _, row in dm_data.iterrows():
        name = row["DM"]
        dm_summary.append({
            "name": name,
            "slug": slugify(name),
            "voters": int(row["Total"]),
            "male": int(row["Male"]),
            "female": int(row["Female"]),
            "youth_pct": youth_lookup.get(name, 0),
            "b40_pct": b40_lookup.get(name, 0),
            "priority_rank": priority_lookup.get(name),
        })

    overview = {
        "total_voters": total,
        "gender": {"male": male, "female": female},
        "age_bands": age_bands,
        "ethnicity": ethnicity,
        "youth_pct": youth_pct,
        "b40_pct": b40_pct,
        "dm_summary": sorted(dm_summary, key=lambda x: x["voters"], reverse=True),
    }

    write_json(overview, os.path.join(OUT_DIR, "overview.json"))


def build_dm_files():
    """Build individual DM JSON files with full demographic profiles."""
    dm_voters = read_csv("dm_voter_counts.csv")
    age_dm = read_csv("age_by_dm.csv")
    eth_dm = read_csv("ethnicity_by_dm.csv")
    housing_age = read_csv("housing_age.csv")
    gender_dm = read_csv("gender_ratio_dm.csv")
    birth_dm = read_csv("birth_state_by_dm.csv")
    origin_dm = read_csv("origin_by_dm.csv")
    priority = read_csv("priority_ranking_dm.csv")
    youth = read_csv("youth_concentration.csv")
    income = read_csv("income_proxy.csv")
    lokaliti_ranked = read_csv("lokaliti_all_ranked.csv")
    gender_lok = read_csv("gender_ratio_lokaliti.csv")
    priority_lok = read_csv("priority_ranking_lokaliti.csv")

    # Read enriched data for lokaliti-level aggregations
    enriched = pd.read_parquet("outputs/enriched_voters.parquet")

    # Build lookup dicts
    priority_lookup = {}
    for _, row in priority.iterrows():
        priority_lookup[row["NamaDM"]] = {
            "score": round(row["Priority_Score"], 4),
            "rank": int(row["Rank"]),
            "youth_pct": round(row["Youth_Pct"] * 100, 1),
            "diversity_index": round(row["Diversity_Index"], 3),
            "b40_pct": round(row["B40_Pct"] * 100, 1),
            "avg_hh_size": round(row["Avg_HH_Size"], 2),
        }

    youth_lookup = dict(zip(youth["NamaDM"], youth["Youth_Young_Adult_Pct"]))

    origin_states = ["Selangor", "Penang", "Negeri Sembilan", "Johor", "Kelantan"]

    dm_names = dm_voters[dm_voters["DM"] != "All"]["DM"].tolist()

    for dm_name in dm_names:
        slug = slugify(dm_name)

        # Voters
        v_row = dm_voters[dm_voters["DM"] == dm_name].iloc[0]
        voters = {"total": int(v_row["Total"]), "male": int(v_row["Male"]), "female": int(v_row["Female"])}

        # Age bands
        a_row = age_dm[age_dm["NamaDM"] == dm_name]
        age_bands = {}
        if len(a_row):
            a_row = a_row.iloc[0]
            for col in ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]:
                age_bands[col] = int(a_row[col])

        # Ethnicity
        e_row = eth_dm[eth_dm["NamaDM"] == dm_name]
        ethnicity = {}
        if len(e_row):
            e_row = e_row.iloc[0]
            for col in ["Malay", "Chinese", "Indian", "Other"]:
                ethnicity[col] = int(e_row[col])

        # Gender
        g_row = gender_dm[gender_dm["NamaDM"] == dm_name]
        gender = {}
        if len(g_row):
            g_row = g_row.iloc[0]
            gender = {"male_pct": float(g_row["Male_Pct"]), "female_pct": float(g_row["Female_Pct"])}

        # Income proxy
        i_row = income[income["NamaDM"] == dm_name]
        housing = {}
        if len(i_row):
            i_row = i_row.iloc[0]
            total = int(i_row["Total"])
            housing = {
                "b40_proxy": int(i_row["B40-proxy"]),
                "institutional": int(i_row["Institutional"]),
                "middle_class": int(i_row["Middle-class"]),
                "other": int(i_row["Other"]),
                "b40_pct": round(int(i_row["B40-proxy"]) / total * 100, 1) if total else 0,
            }

        # Migration
        o_row = origin_dm[origin_dm["NamaDM"] == dm_name]
        migration = {"top_origins": []}
        if len(o_row):
            o_row = o_row.iloc[0]
            for state in origin_states:
                if state in o_row.index:
                    migration["top_origins"].append({"state": state, "voters": int(o_row[state])})

        # Priority
        pri = priority_lookup.get(dm_name, {})

        # Youth concentration
        youth_pct = youth_lookup.get(dm_name, 0)

        # Lokaliti-level data from enriched parquet
        dm_voters_df = enriched[enriched["NamaDM"] == dm_name]
        lokaliti_list = []

        for lok_name, lok_df in dm_voters_df.groupby("NamaLokaliti"):
            lok_total = len(lok_df)
            lok_male = len(lok_df[lok_df["Jantina"] == "L"])
            lok_female = lok_total - lok_male

            # Ethnicity
            lok_eth = lok_df["estimated_ethnicity"].value_counts().to_dict()
            lok_ethnicity = {
                "Malay": lok_eth.get("Malay", 0),
                "Chinese": lok_eth.get("Chinese", 0),
                "Indian": lok_eth.get("Indian", 0),
                "Other": lok_eth.get("Other", 0),
            }

            # Housing type
            lok_housing = lok_df["housing_type"].value_counts().to_dict()

            # Age bands
            lok_age = lok_df["age_band"].value_counts().to_dict()
            lok_age_clean = {}
            for band in ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]:
                lok_age_clean[band] = lok_age.get(band, 0)

            # Get priority rank if available
            lok_pri_row = priority_lok[priority_lok["NamaLokaliti"] == lok_name]
            lok_pri_rank = int(lok_pri_row.iloc[0]["Rank"]) if len(lok_pri_row) else None
            lok_pri_score = round(float(lok_pri_row.iloc[0]["Priority_Score"]), 4) if len(lok_pri_row) else None

            lokaliti_list.append({
                "name": lok_name,
                "voters": lok_total,
                "male": lok_male,
                "female": lok_female,
                "ethnicity": lok_ethnicity,
                "housing": lok_housing,
                "age_bands": lok_age_clean,
                "priority_rank": lok_pri_rank,
                "priority_score": lok_pri_score,
            })

        lokaliti_list.sort(key=lambda x: x["voters"], reverse=True)

        dm_data = {
            "name": dm_name,
            "slug": slug,
            "voters": voters,
            "age_bands": age_bands,
            "ethnicity": ethnicity,
            "gender": gender,
            "housing": housing,
            "migration": migration,
            "youth_pct": youth_pct,
            "priority": pri,
            "lokaliti": lokaliti_list,
        }

        write_json(dm_data, os.path.join(DM_DIR, f"{slug}.json"))


def build_priority():
    """Build priority.json with DM and lokaliti rankings."""
    dm_pri = read_csv("priority_ranking_dm.csv")
    lok_pri = read_csv("priority_ranking_lokaliti.csv")
    inst = read_csv("institutional_profile.csv")

    dm_rankings = []
    for _, row in dm_pri.iterrows():
        dm_rankings.append({
            "name": row["NamaDM"],
            "slug": slugify(row["NamaDM"]),
            "rank": int(row["Rank"]),
            "total_voters": int(row["Total_Voters"]),
            "priority_score": round(row["Priority_Score"], 4),
            "youth_pct": round(row["Youth_Pct"] * 100, 1),
            "diversity_index": round(row["Diversity_Index"], 3),
            "b40_pct": round(row["B40_Pct"] * 100, 1),
            "avg_hh_size": round(row["Avg_HH_Size"], 2),
            "youth_norm": round(row["Youth_Norm"], 3),
            "diversity_norm": round(row["Diversity_Norm"], 3),
            "b40_norm": round(row["B40_Norm"], 3),
            "density_norm": round(row["Density_Norm"], 3),
        })

    lok_rankings = []
    for _, row in lok_pri.head(50).iterrows():
        lok_rankings.append({
            "name": row["NamaLokaliti"],
            "rank": int(row["Rank"]),
            "total_voters": int(row["Total_Voters"]),
            "priority_score": round(row["Priority_Score"], 4),
            "youth_pct": round(row["Youth_Pct"] * 100, 1),
            "diversity_index": round(row["Diversity_Index"], 3),
            "b40_pct": round(row["B40_Pct"] * 100, 1),
            "avg_hh_size": round(row["Avg_HH_Size"], 2),
        })

    institutional = []
    for _, row in inst.iterrows():
        institutional.append({
            "group": row["Group"],
            "total": int(row["Total"]),
            "pct_of_total": float(row["Pct_of_Total"]),
            "male_pct": float(row["Male_Pct"]),
            "age_bands": {
                "22-27 (Youth)": int(row["22-27 (Youth)"]),
                "28-39 (Young Adult)": int(row["28-39 (Young Adult)"]),
                "40-59 (Middle Age)": int(row["40-59 (Middle Age)"]),
                "60+ (Senior)": int(row["60+ (Senior)"]),
            },
            "ethnicity": {
                "Malay": float(row["Malay_Pct"]),
                "Chinese": float(row["Chinese_Pct"]),
                "Indian": float(row["Indian_Pct"]),
                "Other": float(row["Other_Pct"]),
            },
        })

    write_json({
        "dm_rankings": dm_rankings,
        "lokaliti_rankings": lok_rankings,
        "institutional_zones": institutional,
    }, os.path.join(OUT_DIR, "priority.json"))


def build_housing():
    """Build housing.json with socioeconomic data."""
    type_summary = read_csv("housing_type_summary.csv")
    by_ethnicity = read_csv("housing_ethnicity.csv")
    by_age = read_csv("housing_age.csv")
    income = read_csv("income_proxy.csv")
    hh_size = read_csv("household_size_distribution.csv")

    ts = []
    for _, row in type_summary.iterrows():
        ts.append({"type": row["housing_type"], "voters": int(row["Voters"]), "pct": float(row["Pct"])})

    be = []
    for _, row in by_ethnicity.iterrows():
        be.append({
            "type": row["housing_type"],
            "Malay": int(row["Malay"]), "Chinese": int(row["Chinese"]),
            "Indian": int(row["Indian"]), "Other": int(row["Other"]),
        })

    ba = []
    for _, row in by_age.iterrows():
        ba.append({
            "type": row["housing_type"],
            "22-27 (Youth)": int(row["22-27 (Youth)"]),
            "28-39 (Young Adult)": int(row["28-39 (Young Adult)"]),
            "40-59 (Middle Age)": int(row["40-59 (Middle Age)"]),
            "60+ (Senior)": int(row["60+ (Senior)"]),
        })

    ip = []
    for _, row in income.iterrows():
        total = int(row["Total"])
        ip.append({
            "dm": row["NamaDM"],
            "slug": slugify(row["NamaDM"]),
            "b40_proxy": int(row["B40-proxy"]),
            "institutional": int(row["Institutional"]),
            "middle_class": int(row["Middle-class"]),
            "total": total,
            "b40_pct": round(int(row["B40-proxy"]) / total * 100, 1) if total else 0,
        })

    hs = []
    for _, row in hh_size.iterrows():
        hs.append({
            "category": row["Members"],
            "households": int(row["Households"]),
            "voters": int(row["Voters"]),
            "avg_size": float(row["Avg_Size"]),
        })

    write_json({
        "type_summary": ts,
        "by_ethnicity": be,
        "by_age": ba,
        "income_proxy_by_dm": ip,
        "household_size": hs,
    }, os.path.join(OUT_DIR, "housing.json"))


def build_lokaliti_index():
    """Build lightweight lokaliti index for search and comparison."""
    enriched = pd.read_parquet("outputs/enriched_voters.parquet")

    index = []
    for (dm, lok), group in enriched.groupby(["NamaDM", "NamaLokaliti"]):
        total = len(group)
        eth = group["estimated_ethnicity"].value_counts()
        top_eth = eth.index[0] if len(eth) else "Unknown"
        ht = group["housing_type"].value_counts()
        top_housing = ht.index[0] if len(ht) else "Unknown"

        index.append({
            "name": lok,
            "dm": dm,
            "dm_slug": slugify(dm),
            "voters": total,
            "top_ethnicity": top_eth,
            "top_housing": top_housing,
        })

    index.sort(key=lambda x: x["voters"], reverse=True)
    write_json(index, os.path.join(OUT_DIR, "lokaliti-index.json"))


def main():
    print("Building dashboard data...")
    os.makedirs(DM_DIR, exist_ok=True)

    print("\n[1/5] Overview")
    build_overview()

    print("\n[2/5] DM files")
    build_dm_files()

    print("\n[3/5] Priority rankings")
    build_priority()

    print("\n[4/5] Housing & socioeconomic")
    build_housing()

    print("\n[5/5] Lokaliti index")
    build_lokaliti_index()

    # PII audit
    print("\n[audit] Checking for PII leaks...")
    import glob
    pii_pattern = re.compile(r"\d{6}-\d{2}-\d{4}")  # IC number pattern
    found_pii = False
    for f in glob.glob(os.path.join(OUT_DIR, "**/*.json"), recursive=True):
        with open(f) as fh:
            content = fh.read()
            if pii_pattern.search(content):
                print(f"  WARNING: Possible IC number in {f}")
                found_pii = True
    if not found_pii:
        print("  No PII detected in JSON outputs.")

    print("\nDone! Dashboard data is ready in dashboard/data/")


if __name__ == "__main__":
    main()
