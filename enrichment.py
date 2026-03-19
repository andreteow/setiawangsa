"""
Enrichment module for P.118 Setiawangsa electoral roll.
Adds derived columns: age_band, estimated_ethnicity, housing_type, birth_state, etc.
Saves enriched DataFrame to parquet for downstream modules.
"""

import json
import re

import numpy as np
import pandas as pd

from data_loader import load_electoral_roll, ANALYSIS_YEAR, PARQUET_COLUMNS

# ---------------------------------------------------------------------------
# Reference data loaders
# ---------------------------------------------------------------------------


def _load_chinese_surnames():
    """Load Chinese surname set from reference file."""
    surnames = set()
    with open("data/chinese_surnames.txt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for variant in line.split(","):
                variant = variant.strip().upper()
                if variant:
                    surnames.add(variant)
    return surnames


def _load_indian_names():
    """Load Indian name set from reference file."""
    names = set()
    with open("data/indian_names.txt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            names.add(line.strip().upper())
    return names


def _load_state_codes():
    """Load IC state code mapping."""
    with open("data/state_codes.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Common Malay first names (no bin/binti required)
# ---------------------------------------------------------------------------

MALAY_FIRST_NAMES = {
    "MUHAMMAD", "MOHD", "MOHAMAD", "MOHAMED", "AHMAD", "AHMED",
    "SITI", "NUR", "NURUL", "NOOR", "NOORUL", "NORLIA", "NORLIZA",
    "NORZILA", "NORAZLINA", "NORHAYATI", "NORAINI", "NORMA",
    "AZMAN", "AZIZ", "AZIZAH", "AZMI", "AZMAH",
    "FAIZAL", "FAISAL", "FARID", "FARHAN", "FARHANA",
    "HAFIZ", "HAFIZAH", "HAKIM", "HALIM", "HAMID",
    "ISMAIL", "IBRAHIM",
    "JAMALUDDIN", "JAMAL",
    "KAMAL", "KAMARUL", "KHAIRUL", "KHAIRUDDIN",
    "MAZLAN", "MAZLINA", "MUHAMAD",
    "NASIR", "NASRUL", "NAZRI", "NIZAM",
    "RASHID", "RAZAK", "RIZAL", "ROSLI", "ROSLAN", "ROSMAN",
    "SAFUAN", "SHAHRUL", "SHARIFAH", "SHUKOR", "SULAIMAN", "SYAHMI",
    "TENGKU", "WAN", "ZAINAB", "ZAINAL", "ZAINUDDIN", "ZULKIFLI",
    "AMIRUL", "AISYAH", "ARIF", "AZHAR", "BAHARUDDIN",
    "DAYANG", "ENCIK",
    "FITRI", "HAZIQ", "HUSNA", "IZZAT",
    "LUQMAN", "MARIAM", "MAISARAH",
    "NAIM", "PUTERI", "QAYYUM",
    "RAFIQ", "SYAFIQ", "UMMUL", "YUSOF", "YUSUF", "ZIKRI",
    "FATIMAH", "AMINAH", "KHADIJAH", "RAMLAH", "ROHANI",
    "SAADIAH", "ZAINON", "ROKIAH", "HASNAH", "AISHAH",
    "NIK", "MEGAT", "CHE",
}

# Pre-compiled regex for bin/binti detection
_BIN_PATTERN = re.compile(r"\bBIN\b|\bBINTI\b|\bB\.\b|\bBT\b|\bBT\.\b")

# ---------------------------------------------------------------------------
# 2a. Age Band
# ---------------------------------------------------------------------------


def add_age_band(df):
    """Add age and age_band columns. Mutates df in-place."""
    df["age"] = ANALYSIS_YEAR - df["TahunLahir"]

    conditions = [
        df["TahunLahir"] < 1926,       # Anomaly (100+)
        df["TahunLahir"] <= 1966,       # 60+ Senior
        df["TahunLahir"] <= 1986,       # 40-59 Middle Age
        df["TahunLahir"] <= 1998,       # 28-39 Young Adult
        df["TahunLahir"] <= 2004,       # 22-27 Youth
    ]
    choices = [
        "Anomaly (100+)",
        "60+ (Senior)",
        "40-59 (Middle Age)",
        "28-39 (Young Adult)",
        "22-27 (Youth)",
    ]
    df["age_band"] = np.select(conditions, choices, default="Unknown")


# ---------------------------------------------------------------------------
# 2b. Ethnicity Inference (vectorized)
# ---------------------------------------------------------------------------


def add_ethnicity(df, chinese_surnames, indian_names, state_codes):
    """Add ethnicity columns using vectorized multi-signal inference. Mutates df in-place."""
    name_upper = df["Nama"].str.upper().str.strip()
    ic_str = df["IC"].astype(str)

    # --- Signal 1: Definitive markers (vectorized) ---
    has_al_ap = name_upper.str.contains(r" A/L | A/P ", regex=True, na=False)
    has_bin = name_upper.str.contains(
        r"\bBIN\b|\bBINTI\b|\bB\.\b|\bBT\b|\bBT\.\b", regex=True, na=False
    )

    # --- Signal 2: Name pattern matching (vectorized) ---
    first_token = name_upper.str.split().str[0].fillna("")
    is_chinese_surname = first_token.isin(chinese_surnames)

    # Build regex patterns for Indian and Malay name matching
    indian_pattern = r"\b(?:" + "|".join(sorted(indian_names, key=len, reverse=True)) + r")\b"
    malay_pattern = r"\b(?:" + "|".join(sorted(MALAY_FIRST_NAMES, key=len, reverse=True)) + r")\b"
    has_indian_name = name_upper.str.contains(indian_pattern, regex=True, na=False)
    has_malay_name = name_upper.str.contains(malay_pattern, regex=True, na=False)

    # --- Signal 3: Birth state (vectorized) ---
    is_mykad = ic_str.str.match(r"^\d{12}$")
    state_code = ic_str.str[6:8]
    birth_state = state_code.map(state_codes).where(is_mykad)

    malay_states = {"Kelantan", "Terengganu", "Kedah", "Perlis"}
    is_malay_state = birth_state.isin(malay_states)
    is_east_my = birth_state.isin({"Sabah", "Sarawak"})
    is_india_born = birth_state.isin({"India"})
    is_china_born = birth_state.isin({"China"})

    # --- Ethnicity assignment (priority cascade via np.select) ---
    eth_conditions = [
        has_al_ap,                                          # Indian (definitive)
        has_bin,                                            # Malay (definitive)
        is_chinese_surname & ~has_indian_name,              # Chinese (name)
        has_indian_name & ~is_chinese_surname,              # Indian (name)
        has_malay_name,                                     # Malay (name)
        is_malay_state,                                     # Malay (birth state)
        is_india_born,                                      # Indian (birth state)
        is_china_born,                                      # Chinese (birth state)
        is_east_my,                                         # Other/Bumiputera (East MY)
    ]
    eth_choices = [
        "Indian", "Malay", "Chinese", "Indian", "Malay",
        "Malay", "Indian", "Chinese", "Other",
    ]
    df["estimated_ethnicity"] = np.select(eth_conditions, eth_choices, default="Other")

    # --- Confidence assignment ---
    conf_conditions = [
        has_al_ap,
        has_bin,
        is_chinese_surname & ~has_indian_name,
        has_indian_name & ~is_chinese_surname,
        has_malay_name & is_malay_state,    # name + state agreement
        has_malay_name,
        is_malay_state | is_india_born | is_china_born,
    ]
    conf_choices = [
        "high", "high", "medium", "medium", "high", "medium", "medium",
    ]
    df["ethnicity_confidence"] = np.select(conf_conditions, conf_choices, default="low")

    # --- Signals column (for audit trail) ---
    signals_parts = []
    signals_parts.append(has_al_ap.map({True: "a/l_a/p", False: ""}))
    signals_parts.append(has_bin.map({True: "bin/binti", False: ""}))
    signals_parts.append(
        is_chinese_surname.map({True: "chinese_surname", False: ""})
    )
    signals_parts.append(
        has_indian_name.map({True: "indian_name", False: ""})
    )
    signals_parts.append(
        has_malay_name.map({True: "malay_name", False: ""})
    )
    signals_parts.append(
        birth_state.fillna("").apply(
            lambda x: f"birth_state:{x}" if x else ""
        )
    )
    df["ethnicity_signals"] = (
        pd.concat(signals_parts, axis=1)
        .apply(lambda row: ",".join(s for s in row if s), axis=1)
        .replace("", "no_signal")
    )


# ---------------------------------------------------------------------------
# 2c. Housing Type Classification
# ---------------------------------------------------------------------------

# Ordered list of (keywords, housing_type) — first match wins
HOUSING_RULES = [
    # Institutional first (specific DM-based names)
    (["MINDEF", "PULAPOL", "POLIS", "TENTERA", "ASRAMA", "KEM ", "MARKAS",
      "REJIMEN", "MAKTAB PERTAHANAN", "ANGKUT", "KOMP ", "FLEET",
      "JURUTERA", "ARTILERI", "INFANTRI", "ORDNANS", "SEMBOYAN",
      "BSEP", "BSPP", "JABATANARAH", "JABATAN ARAH", "OPLAT",
      "ATCK", "MK TD", "MK ATM", "MTAT", "MATM", "MTL", "MTU",
      "PERUBATAN AT", "MESS M", "R/PANJANG BARU IMT", "PERGIGIAN AT",
      "MKTD", "PEJ. PTD", "PEJ. PTU", "REJ ", "PUSAT LATIHAN POLIS",
      "RUMAH PUSAT LATIHAN POLIS", "BEKAS POLIS", "BEKAS TENTERA",
      "IBU PEJABAT POLIS", "BALAI POLIS", "BALAI BOMBA",
      "KOMPLEKS PERUMAHAN ATM", "BPA ", "CAWANGAN PROBOS",
      "DTD CAW", "STAF OPERASI", "MIDAS", "104 KOMP",
      "11 SKN", "40 REJ", "50 REJ", "56 REJIMEN", "60 REJ", "70 REJ",
      "711 PUSAT", "91 REJIMEN", "92 ATCK", "932 KOMP", "94 UPKAT",
      "BAHAGIAN INSPEKTORAT", "BAHAGIAN LOJISTIK", "BAHAGIAN PERKHIDMATAN",
      "RUMAH PANJANG", "MK  TD", "MK LOG"],
     "Institutional"),
    (["PPR"], "PPR"),
    (["FLAT", "PANGSA", "R/PANGSA", "RUMAH PANGSA"], "Flat"),
    (["KONDOMINIUM", "CONDO", "RESIDENSI", "PANGSAPURI", "APARTMENT",
      "APT ", "VISTA", "SUITES", "HEIGHTS", "LOJING", "MENARA",
      "INFINITI", "PLATINUM", "SEASONS GARDEN", "ASCENDA",
      "VILLA WANGSAMAS", "DESA VILLA", "IRAMA WANGSA",
      "SRI LEDANG", "SRI KINABALU", "PUNCAK", "DESIRAN BAYU",
      "KENANGA SARI", "SRI AYU", "WANGSA DELIMA", "WANGSA JAYA",
      "SETIAWANGSA BUSINESS SUITE", "BLOCK KEDIDI",
      "RAMPAI BUSINESS PARK", "KALEIDOSCOPE", "TIARA TITIWANGSA",
      "RAMPAI COURT"],
     "Condo/Apartment"),
    (["TAMAN", "TMN", "KAMPUNG", "KAMPONG", "KG ", "DESA ", "JALAN ",
      "JLN ", "LORONG ", "LRG ", "PERSIARAN", "SEK ", "SEKSYEN",
      "BUKIT", "SETAPAK", "SEKOLAH TINGGI", "MARIAN CONVENT",
      "WAIZURI", "PLAZA WANGSA MAJU", "KAWASAN PERUSAHAAN"],
     "Taman"),
    (["KELOMPOK"], "Flat"),
    (["PERUMAHAN AWAM"], "Flat"),
]


def _classify_housing(lokaliti_name):
    """Classify a single lokaliti name into housing type."""
    name_upper = lokaliti_name.upper().strip()
    for keywords, housing_type in HOUSING_RULES:
        for kw in keywords:
            if kw in name_upper:
                return housing_type
    return "Other"


def add_housing_type(df):
    """Add housing_type column. Uses unique-value map for speed. Mutates df in-place."""
    unique_lokaliti = df["NamaLokaliti"].unique()
    housing_map = {lok: _classify_housing(lok) for lok in unique_lokaliti}
    df["housing_type"] = df["NamaLokaliti"].map(housing_map)


# ---------------------------------------------------------------------------
# 2d. Birth State Parsing
# ---------------------------------------------------------------------------


def add_birth_state(df, state_codes):
    """Add birth_state_code and birth_state_name columns. Mutates df in-place."""
    ic_str = df["IC"].astype(str)

    is_mykad = ic_str.str.match(r"^\d{12}$")
    df["birth_state_code"] = np.where(is_mykad, ic_str.str[6:8], "N/A")
    mapped = df["birth_state_code"].map(state_codes)
    fallback = np.where(
        df["birth_state_code"] == "N/A", "Old IC (no state)", "Unknown Code"
    )
    df["birth_state_name"] = mapped.where(mapped.notna(), fallback)


# ---------------------------------------------------------------------------
# 2e. NoRumah Normalization
# ---------------------------------------------------------------------------


def add_norumah_normalized(df):
    """Normalize NoRumah values for household clustering. Mutates df in-place."""
    norumah = df["NoRumah"].fillna("MISSING").str.strip().str.upper()
    norumah = norumah.str.replace(r"^NO\.?\s*", "", regex=True)
    norumah = norumah.str.replace(r"^LOT\s+", "", regex=True)
    norumah = norumah.str.rstrip(",")
    df["norumah_normalized"] = norumah


# ---------------------------------------------------------------------------
# Main enrichment pipeline
# ---------------------------------------------------------------------------


def enrich(df):
    """Run all enrichment steps. Mutates and returns the DataFrame."""
    df = df.copy()  # single defensive copy

    chinese_surnames = _load_chinese_surnames()
    indian_names = _load_indian_names()
    state_codes = _load_state_codes()

    print(f"Reference data loaded: {len(chinese_surnames)} Chinese surnames, "
          f"{len(indian_names)} Indian names, {len(state_codes)} state codes")

    print("Adding age bands...")
    add_age_band(df)

    print("Inferring ethnicity...")
    add_ethnicity(df, chinese_surnames, indian_names, state_codes)

    print("Classifying housing types...")
    add_housing_type(df)

    print("Parsing birth states...")
    add_birth_state(df, state_codes)

    print("Normalizing NoRumah...")
    add_norumah_normalized(df)

    return df


def verify_enrichment(df, raw_len):
    """Run enrichment verification checks."""
    print(f"\n{'=' * 60}")
    print("ENRICHMENT VERIFICATION")
    print(f"{'=' * 60}")

    if len(df) != raw_len:
        raise ValueError(f"Row count changed! Expected {raw_len}, got {len(df)}")
    print(f"Row count: {len(df)} (expected {raw_len}) ✓")

    if df["age_band"].isna().any():
        raise ValueError("Some rows missing age_band")
    print(f"age_band: all populated ✓")
    print(f"  {df['age_band'].value_counts().to_dict()}")

    if df["estimated_ethnicity"].isna().any():
        raise ValueError("Some rows missing ethnicity")
    print(f"estimated_ethnicity: all populated ✓")
    print(f"  {df['estimated_ethnicity'].value_counts().to_dict()}")
    print(f"  Confidence: {df['ethnicity_confidence'].value_counts().to_dict()}")

    if df["housing_type"].isna().any():
        raise ValueError("Some rows missing housing_type")
    print(f"housing_type: all populated ✓")
    ht_counts = df["housing_type"].value_counts()
    print(f"  {ht_counts.to_dict()}")
    other_pct = ht_counts.get("Other", 0) / len(df) * 100
    print(f"  'Other' category: {other_pct:.1f}% (target: <10%)")

    if df["birth_state_name"].isna().any():
        raise ValueError("Some rows missing birth_state")
    print(f"birth_state_name: all populated ✓")

    if df["norumah_normalized"].isna().any():
        raise ValueError("Some rows missing norumah_normalized")
    missing_count = (df["norumah_normalized"] == "MISSING").sum()
    print(f"norumah_normalized: all populated ✓ ({missing_count} MISSING sentinel values)")

    print(f"\nEnriched {len(df)} rows — all derived columns populated ✓")


def save_spot_check(df):
    """Export a 50-row sample with derived fields only (PII-safe)."""
    sample = df.sample(50, random_state=42).copy()
    sample["name_truncated"] = sample["Nama"].str[:3] + "***"
    spot_cols = [
        "name_truncated", "age", "age_band", "estimated_ethnicity",
        "ethnicity_confidence", "ethnicity_signals", "housing_type",
        "birth_state_name", "NamaDM",
    ]
    sample[spot_cols].to_csv("outputs/csv/enrichment_spot_check.csv", index=False)
    print("Spot-check sample saved: outputs/csv/enrichment_spot_check.csv")


def run_enrichment():
    """Load, enrich, verify, and save."""
    df = load_electoral_roll()
    raw_len = len(df)

    df = enrich(df)
    verify_enrichment(df, raw_len)
    save_spot_check(df)

    # Save enriched DataFrame as parquet — PII columns stripped
    output_path = "outputs/enriched_voters.parquet"
    df[PARQUET_COLUMNS].to_parquet(output_path, index=False)
    print(f"\nEnriched data saved: {output_path} (PII columns excluded)")

    return df


if __name__ == "__main__":
    run_enrichment()
