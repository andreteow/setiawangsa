"""
Module 0: Data Validation for P.118 Setiawangsa electoral roll.
Checks data quality, flags anomalies, and generates a validation report.
"""

import pandas as pd
from data_loader import load_electoral_roll, EXPECTED_DMS, ANALYSIS_YEAR


def validate_ic_format(df):
    """Check IC format: 12-digit MyKad or old-format (G/RF/RFS/T/I prefix)."""
    ic = df["IC"].astype(str)
    is_mykad = ic.str.match(r"^\d{12}$")
    is_old_format = ic.str.match(r"^(G|RFS?|T|I)\d+$")
    invalid = ~(is_mykad | is_old_format)

    results = {
        "mykad_12digit": is_mykad.sum(),
        "old_format": is_old_format.sum(),
        "invalid_format": invalid.sum(),
    }
    print(f"\nIC Format Check:")
    print(f"  12-digit MyKad: {results['mykad_12digit']:,}")
    print(f"  Old format (G/RF/RFS/T/I prefix): {results['old_format']:,}")
    print(f"  Invalid format: {results['invalid_format']:,}")

    invalid_records = df[invalid][["NoSiri", "Nama", "NamaDM"]].copy()
    invalid_records["flag"] = "invalid_ic_format"
    return invalid_records, results


def check_duplicate_ics(df):
    """Check for duplicate IC numbers."""
    ic_counts = df["IC"].value_counts()
    duplicates = ic_counts[ic_counts > 1]

    print(f"\nDuplicate IC Check:")
    print(f"  Unique ICs: {df['IC'].nunique():,}")
    print(f"  Duplicate IC values: {len(duplicates):,}")
    if len(duplicates) > 0:
        total_dup_records = duplicates.sum() - len(duplicates)
        print(f"  Total extra records from duplicates: {total_dup_records:,}")
        print(f"  (details omitted for PII protection)")

    dup_records = df[df["IC"].isin(duplicates.index)][
        ["NoSiri", "Nama", "NamaDM"]
    ].copy()
    dup_records["flag"] = "duplicate_ic"
    return dup_records


def check_null_names(df):
    """Check for null or blank Nama fields."""
    null_names = df["Nama"].isna() | (df["Nama"].str.strip() == "")
    count = null_names.sum()
    print(f"\nNull/Blank Name Check:")
    print(f"  Null or blank names: {count:,}")

    flagged = df[null_names][["NoSiri", "Nama", "NamaDM"]].copy()
    flagged["flag"] = "null_name"
    return flagged


def check_age_anomalies(df):
    """Flag voters with birth year before 1926 (age 100+ in analysis year)."""
    age = ANALYSIS_YEAR - df["TahunLahir"]
    anomalies = df[age >= 100]
    count = len(anomalies)

    print(f"\nAge Anomaly Check (birth year < 1926, age 100+):")
    print(f"  Anomalous records: {count:,}")
    if count > 0:
        print(f"  Birth year range of anomalies: {anomalies['TahunLahir'].min()}-{anomalies['TahunLahir'].max()}")
        print(f"  By DM:")
        for dm, cnt in anomalies["NamaDM"].value_counts().items():
            print(f"    {dm}: {cnt}")

    flagged = anomalies[["NoSiri", "Nama", "NamaDM", "TahunLahir"]].copy()
    flagged["flag"] = "age_100_plus"
    return flagged


def verify_dms(df):
    """Verify all 17 expected DMs are present."""
    actual_dms = set(df["NamaDM"].unique())
    expected_dms = set(EXPECTED_DMS)

    missing = expected_dms - actual_dms
    unexpected = actual_dms - expected_dms

    print(f"\nDM Verification:")
    print(f"  Expected DMs: {len(EXPECTED_DMS)}")
    print(f"  Actual DMs: {len(actual_dms)}")
    if missing:
        print(f"  MISSING DMs: {missing}")
    if unexpected:
        print(f"  UNEXPECTED DMs: {unexpected}")
    if not missing and not unexpected:
        print(f"  All 17 DMs present and accounted for ✓")

    return missing, unexpected


def check_lokaliti(df):
    """Count unique lokaliti and check code-name consistency."""
    unique_lokaliti = df["NamaLokaliti"].nunique()
    unique_codes = df["Kodlokaliti"].nunique()

    print(f"\nLokaliti Check:")
    print(f"  Unique NamaLokaliti: {unique_lokaliti}")
    print(f"  Unique Kodlokaliti: {unique_codes}")

    code_name_map = df.groupby("Kodlokaliti")["NamaLokaliti"].nunique()
    inconsistent = code_name_map[code_name_map > 1]
    if len(inconsistent) > 0:
        print(f"  INCONSISTENT code-name mappings: {len(inconsistent)}")
        for code in inconsistent.index:
            names = df[df["Kodlokaliti"] == code]["NamaLokaliti"].unique()
            print(f"    Code {code}: {list(names)}")
    else:
        print(f"  Code-name mapping is consistent ✓")

    name_code_map = df.groupby("NamaLokaliti")["Kodlokaliti"].nunique()
    reverse_inconsistent = name_code_map[name_code_map > 1]
    if len(reverse_inconsistent) > 0:
        print(f"  Names mapping to multiple codes: {len(reverse_inconsistent)}")
        for name in reverse_inconsistent.index:
            codes = df[df["NamaLokaliti"] == name]["Kodlokaliti"].unique()
            print(f"    '{name}': codes {list(codes)}")


def check_missing_norumah(df):
    """Report the missing NoRumah records by DM/lokaliti."""
    missing = df[df["NoRumah"].isna()]
    count = len(missing)

    print(f"\nMissing NoRumah Check:")
    print(f"  Missing NoRumah records: {count:,}")
    if count > 0:
        print(f"  By DM:")
        for dm, cnt in missing["NamaDM"].value_counts().items():
            print(f"    {dm}: {cnt}")
        print(f"  By Lokaliti (top 10):")
        for lok, cnt in missing["NamaLokaliti"].value_counts().head(10).items():
            print(f"    {lok}: {cnt}")

    flagged = missing[["NoSiri", "Nama", "NamaDM", "NamaLokaliti"]].copy()
    flagged["flag"] = "missing_norumah"
    return flagged


def run_validation():
    """Run all validation checks and generate report."""
    df = load_electoral_roll()

    print("\n" + "=" * 60)
    print("MODULE 0: DATA VALIDATION REPORT")
    print("P.118 Setiawangsa Electoral Roll")
    print("=" * 60)

    all_flagged = []

    invalid_ic, ic_stats = validate_ic_format(df)
    all_flagged.append(invalid_ic)

    dup_records = check_duplicate_ics(df)
    all_flagged.append(dup_records)

    null_names = check_null_names(df)
    all_flagged.append(null_names)

    age_anomalies = check_age_anomalies(df)
    all_flagged.append(age_anomalies)

    missing_dms, unexpected_dms = verify_dms(df)
    check_lokaliti(df)

    missing_norumah = check_missing_norumah(df)
    all_flagged.append(missing_norumah)

    flagged_df = pd.concat(all_flagged, ignore_index=True)

    # PII protection: truncate names in output
    if len(flagged_df) > 0 and "Nama" in flagged_df.columns:
        flagged_df["name_truncated"] = flagged_df["Nama"].str[:3] + "***"
        flagged_df = flagged_df.drop(columns=["Nama"])

    output_path = "outputs/csv/validation_report.csv"
    flagged_df.to_csv(output_path, index=False)
    print(f"\n{'=' * 60}")
    print(f"Validation report saved: {output_path}")
    print(f"Total flagged records: {len(flagged_df):,}")
    print(f"  By flag type:")
    if len(flagged_df) > 0:
        for flag, cnt in flagged_df["flag"].value_counts().items():
            print(f"    {flag}: {cnt:,}")

    print(f"\n{'=' * 60}")
    print("SUMMARY STATISTICS")
    print(f"{'=' * 60}")
    print(f"Total voters: {len(df):,}")
    print(f"Male (L): {(df['Jantina'] == 'L').sum():,}")
    print(f"Female (P): {(df['Jantina'] == 'P').sum():,}")
    print(f"Daerah Mengundi: {df['NamaDM'].nunique()}")
    print(f"Lokaliti: {df['NamaLokaliti'].nunique()}")
    print(f"Birth year range: {df['TahunLahir'].min()}-{df['TahunLahir'].max()}")
    print(f"MyKad ICs: {ic_stats['mykad_12digit']:,}")
    print(f"Old-format ICs: {ic_stats['old_format']:,}")
    print(f"Age 100+ anomalies: {len(age_anomalies):,}")
    print(f"Missing NoRumah: {len(missing_norumah):,}")

    return df, flagged_df


if __name__ == "__main__":
    run_validation()
