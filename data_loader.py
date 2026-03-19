"""
Data loader for P.118 Setiawangsa electoral roll.
Loads the SPR Excel file, validates column schema, and returns a clean DataFrame.
Exports shared constants used across all modules.
"""

import pandas as pd

EXCEL_FILE = "P.118 SETIAWANGSA.xlsx"
EXPECTED_ROWS = 95732
ANALYSIS_YEAR = 2026

EXPECTED_COLUMNS = [
    "NoSiri", "IC", "ICLama", "Nama", "ICSpouse", "NoRumah",
    "Jantina", "Kodlokaliti", "NamaLokaliti", "NamaParlimen",
    "NamaDM", "NamaDUN", "Negeri", "TahunLahir",
]

EXPECTED_DMS = [
    "AYER PANAS DALAM", "AYER PANAS LUAR", "AYER PANAS TENGAH",
    "DESA REJANG", "JALAN PAHANG", "JALAN USAHAWAN", "KERAMAT WANGSA",
    "MINDEF", "PKNS BATU 6 ULU KLANG", "PULAPOL",
    "SEKSYEN 10 WANGSA MAJU", "SEKSYEN 5/6 WANGSA MAJU",
    "TAMAN SETAPAK JAYA", "TAMAN SETAPAK PERMAI", "TAMAN SETIAWANGSA",
    "TAMAN SRI RAMPAI", "TAMAN TASIK",
]

INSTITUTIONAL_DMS = ["MINDEF", "PULAPOL"]

AGE_BAND_ORDER = [
    "22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)",
]

ETHNICITY_ORDER = ["Malay", "Chinese", "Indian", "Other"]

HOUSING_ORDER = ["PPR", "Flat", "Taman", "Condo/Apartment", "Institutional", "Other"]

# Columns safe for parquet export (no PII)
PARQUET_COLUMNS = [
    "NoSiri", "Jantina", "Kodlokaliti", "NamaLokaliti", "NamaDM", "TahunLahir",
    "age", "age_band", "estimated_ethnicity", "ethnicity_confidence",
    "ethnicity_signals", "housing_type", "birth_state_code", "birth_state_name",
    "norumah_normalized",
]


def load_electoral_roll(filepath=EXCEL_FILE):
    """Load the electoral roll Excel file and perform basic schema validation."""
    print(f"Loading {filepath}...")
    df = pd.read_excel(filepath, dtype={"IC": str})

    # Validate row count
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(df)}")
    print(f"Loaded {len(df)} rows from Excel (expected {EXPECTED_ROWS})")

    # Validate columns
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    if extra_cols:
        print(f"NOTE: Extra columns found: {extra_cols}")

    # Strip whitespace from string columns
    for col in ["Jantina", "Nama", "NamaLokaliti", "NamaDM", "NamaParlimen", "Negeri"]:
        df[col] = df[col].str.strip()

    return df


if __name__ == "__main__":
    df = load_electoral_roll()
    print(f"\nSchema validated. {len(df)} rows, {len(df.columns)} columns.")
    print(f"Gender: {df['Jantina'].value_counts().to_dict()}")
    print(f"DMs: {df['NamaDM'].nunique()}")
    print(f"Lokaliti: {df['NamaLokaliti'].nunique()}")
    print(f"Birth year range: {df['TahunLahir'].min()}-{df['TahunLahir'].max()}")
