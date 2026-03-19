"""
Run the full P.118 Setiawangsa analysis pipeline.
Load -> Validate -> Enrich -> All Modules -> Verification Summary
"""

import importlib
import time

import pandas as pd

from data_loader import EXPECTED_ROWS

MODULES = [
    ("Module 1: Concentration", "module_1_concentration", "run_module_1"),
    ("Module 2: Age Segmentation", "module_2_age", "run_module_2"),
    ("Module 3: Ethnicity", "module_3_ethnicity", "run_module_3"),
    ("Module 4: Housing Type", "module_4_housing", "run_module_4"),
    ("Module 5: Migration", "module_5_migration", "run_module_5"),
    ("Module 6: Household", "module_6_household", "run_module_6"),
    ("Module 7: Institutional", "module_7_institutional", "run_module_7"),
    ("Module 8: Gender", "module_8_gender", "run_module_8"),
    ("Module 9: Priority Scoring", "module_9_priority", "run_module_9"),
]


def run_pipeline():
    start = time.time()
    print("=" * 70)
    print("P.118 SETIAWANGSA — FULL ANALYSIS PIPELINE")
    print("=" * 70)

    # Phase 1: Validation
    print(f"\n{'━' * 70}")
    print("PHASE 1: VALIDATION")
    print(f"{'━' * 70}")
    from module_0_validation import run_validation
    df_raw, flagged = run_validation()

    # Phase 2: Enrichment
    print(f"\n{'━' * 70}")
    print("PHASE 2: ENRICHMENT")
    print(f"{'━' * 70}")
    from enrichment import run_enrichment
    run_enrichment()

    # Phase 3: Analytical Modules
    for name, module_name, func_name in MODULES:
        print(f"\n{'━' * 70}")
        print(f"PHASE 3: {name.upper()}")
        print(f"{'━' * 70}")
        mod = importlib.import_module(module_name)
        getattr(mod, func_name)()

    # Phase 4: Verification Summary
    print(f"\n{'━' * 70}")
    print("PHASE 4: FINAL VERIFICATION SUMMARY")
    print(f"{'━' * 70}")
    generate_verification_summary()

    elapsed = time.time() - start
    print(f"\n{'=' * 70}")
    print(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    print(f"{'=' * 70}")


def generate_verification_summary():
    """Generate Layer 4 verification summary."""
    df = pd.read_parquet("outputs/enriched_voters.parquet")
    total = len(df)
    anomalies = (df["age_band"] == "Anomaly (100+)").sum()
    missing_norumah = (df["norumah_normalized"] == "MISSING").sum()

    checks = []

    checks.append({
        "Check": "Total rows loaded",
        "Expected": EXPECTED_ROWS,
        "Actual": total,
        "Status": "PASS" if total == EXPECTED_ROWS else "FAIL",
    })

    checks.append({
        "Check": "Rows after enrichment",
        "Expected": EXPECTED_ROWS,
        "Actual": total,
        "Status": "PASS" if total == EXPECTED_ROWS else "FAIL",
    })

    dm_csv = pd.read_csv("outputs/csv/dm_voter_counts.csv", index_col=0)
    dm_sum = dm_csv.loc[dm_csv.index != "All", "Total"].sum()
    checks.append({
        "Check": "DM voter sum",
        "Expected": EXPECTED_ROWS,
        "Actual": int(dm_sum),
        "Status": "PASS" if int(dm_sum) == EXPECTED_ROWS else "FAIL",
    })

    age_expected = EXPECTED_ROWS - anomalies
    age_csv = pd.read_csv("outputs/csv/age_by_gender.csv", index_col=0)
    age_sum = age_csv["Total"].sum()
    checks.append({
        "Check": "Age band sum (excl. anomalies)",
        "Expected": int(age_expected),
        "Actual": int(age_sum),
        "Status": "PASS" if int(age_sum) == int(age_expected) else "FAIL",
    })

    eth_csv = pd.read_csv("outputs/csv/ethnicity_by_dm.csv", index_col=0)
    eth_sum = eth_csv["Total"].sum()
    checks.append({
        "Check": "Ethnicity sum",
        "Expected": EXPECTED_ROWS,
        "Actual": int(eth_sum),
        "Status": "PASS" if int(eth_sum) == EXPECTED_ROWS else "FAIL",
    })

    ht_csv = pd.read_csv("outputs/csv/housing_type_summary.csv", index_col=0)
    ht_sum = ht_csv["Voters"].sum()
    checks.append({
        "Check": "Housing type sum",
        "Expected": EXPECTED_ROWS,
        "Actual": int(ht_sum),
        "Status": "PASS" if int(ht_sum) == EXPECTED_ROWS else "FAIL",
    })

    mig_csv = pd.read_csv("outputs/csv/birth_state_by_dm.csv", index_col=0)
    mig_sum = mig_csv["Total"].sum()
    checks.append({
        "Check": "Birth state sum",
        "Expected": EXPECTED_ROWS,
        "Actual": int(mig_sum),
        "Status": "PASS" if int(mig_sum) == EXPECTED_ROWS else "FAIL",
    })

    hh_csv = pd.read_csv("outputs/csv/household_clusters.csv")
    hh_sum = hh_csv["Members"].sum() + missing_norumah
    checks.append({
        "Check": "Household clusters + missing NoRumah",
        "Expected": EXPECTED_ROWS,
        "Actual": int(hh_sum),
        "Status": "PASS" if int(hh_sum) == EXPECTED_ROWS else "FAIL",
    })

    inst_csv = pd.read_csv("outputs/csv/institutional_profile.csv")
    inst_total = inst_csv[inst_csv["Group"] == "Constituency Total"]["Total"].values[0]
    checks.append({
        "Check": "Institutional + civilian",
        "Expected": EXPECTED_ROWS,
        "Actual": int(inst_total),
        "Status": "PASS" if int(inst_total) == EXPECTED_ROWS else "FAIL",
    })

    gen_csv = pd.read_csv("outputs/csv/gender_ratio_dm.csv", index_col=0)
    gen_sum = gen_csv["Total"].sum()
    checks.append({
        "Check": "Gender sum (Male + Female)",
        "Expected": EXPECTED_ROWS,
        "Actual": int(gen_sum),
        "Status": "PASS" if int(gen_sum) == EXPECTED_ROWS else "FAIL",
    })

    summary_df = pd.DataFrame(checks)
    summary_df.to_csv("outputs/csv/verification_summary.csv", index=False)

    print("\nVERIFICATION SUMMARY")
    print("=" * 60)
    all_pass = True
    for _, row in summary_df.iterrows():
        status_marker = "✓" if row["Status"] == "PASS" else "✗ FAIL"
        print(f"  {row['Check']:<40} {row['Expected']:>8} → {row['Actual']:>8}  {status_marker}")
        if row["Status"] != "PASS":
            all_pass = False

    print(f"\n{'All checks PASSED ✓' if all_pass else 'SOME CHECKS FAILED ✗'}")
    print(f"Saved: outputs/csv/verification_summary.csv")

    if not all_pass:
        raise SystemExit("Pipeline verification failed!")


if __name__ == "__main__":
    run_pipeline()
