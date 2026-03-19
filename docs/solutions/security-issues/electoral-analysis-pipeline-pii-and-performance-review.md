---
title: "Electoral Analysis Pipeline — PII Protection, Performance, and Code Quality Fixes"
category: security-issues
date: 2026-03-19
tags:
  - pii-security
  - pandas
  - performance-optimization
  - python
  - electoral-analysis
  - data-validation
  - code-review
severity: high
component: setiawangsa-analysis-pipeline
resolution_time: ~1 hour (review + fixes)
confidence: high
---

# Electoral Analysis Pipeline — PII Protection, Performance, and Code Quality Fixes

## Problem

After building a 10-module Python pipeline to analyze ~95,732 voter records from the SPR electoral roll for P.118 Setiawangsa, a 4-agent code review (Python reviewer, security sentinel, performance oracle, code simplicity reviewer) identified 15 findings across P1/P2/P3 severity levels. The most critical issues:

1. **PII leaking in intermediate files** — the enriched parquet file contained full IC numbers, names, spouse ICs, and addresses for all 95,732 voters
2. **No .gitignore** — the 8.5MB Excel source file (with full PII) was already tracked in git
3. **Silent validation bypass** — all data integrity checks used `assert`, which is stripped under `python -O`

## Root Cause

Six distinct root cause patterns:

| Pattern | Cause |
|---------|-------|
| PII leakage | `df.to_parquet()` saved the full DataFrame without column filtering; `validation_report.csv` included untruncated names |
| Performance bottleneck | `df.apply(func, axis=1)` invoked a Python function per row (95K calls) for ethnicity inference |
| Validation bypass | `assert` used for production data checks — silently disabled under optimized Python |
| Constants duplication | `EXPECTED_TOTAL`, `AGE_BAND_ORDER`, etc. copy-pasted across 8+ files |
| DataFrame mutation | Modules 4 & 5 added columns directly to the shared parquet-loaded DataFrame |
| Missing .gitignore | Project initialized without one; sensitive data committed before rules existed |

## Solution

### 1. PII Stripped from Parquet Output

Define an allowlist of safe columns in `data_loader.py`:

```python
PARQUET_COLUMNS = [
    "NoSiri", "Jantina", "Kodlokaliti", "NamaLokaliti", "NamaDM", "TahunLahir",
    "age", "age_band", "estimated_ethnicity", "ethnicity_confidence",
    "ethnicity_signals", "housing_type", "birth_state_code", "birth_state_name",
    "norumah_normalized",
]
```

Filter before writing in `enrichment.py`:

```python
df[PARQUET_COLUMNS].to_parquet(output_path, index=False)
```

Truncate names in `validation_report.csv`:

```python
flagged_df["name_truncated"] = flagged_df["Nama"].str[:3] + "***"
flagged_df = flagged_df.drop(columns=["Nama"])
```

### 2. Ethnicity Inference Vectorized (10-50x speedup)

Replaced row-by-row `df.apply()` with vectorized `str.contains()` + `np.select()`:

```python
# Build regex from name sets
indian_pattern = r"\b(?:" + "|".join(sorted(indian_names, key=len, reverse=True)) + r")\b"
has_indian_name = name_upper.str.contains(indian_pattern, regex=True, na=False)

# Priority cascade
df["estimated_ethnicity"] = np.select(
    [has_al_ap, has_bin, is_chinese_surname, has_indian_name, has_malay_name, ...],
    ["Indian", "Malay", "Chinese", "Indian", "Malay", ...],
    default="Other",
)
```

Housing classification similarly optimized — map via 515 unique locality values instead of 95K apply calls (~180x faster):

```python
unique_lokaliti = df["NamaLokaliti"].unique()
housing_map = {lok: _classify_housing(lok) for lok in unique_lokaliti}
df["housing_type"] = df["NamaLokaliti"].map(housing_map)
```

### 3. assert Replaced with raise ValueError

All 13 files updated:

```python
# Before (silently disabled under python -O)
assert len(df) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS}, got {len(df)}"

# After (always enforced)
if len(df) != EXPECTED_ROWS:
    raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(df)}")
```

### 4. Constants Centralized

All shared constants moved to `data_loader.py` — 15 duplicate definitions removed:

```python
# data_loader.py
EXPECTED_ROWS = 95732
ANALYSIS_YEAR = 2026
AGE_BAND_ORDER = ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"]
ETHNICITY_ORDER = ["Malay", "Chinese", "Indian", "Other"]
INSTITUTIONAL_DMS = ["MINDEF", "PULAPOL"]
HOUSING_ORDER = ["PPR", "Flat", "Taman", "Condo/Apartment", "Institutional", "Other"]
```

All modules import from there: `from data_loader import EXPECTED_ROWS, AGE_BAND_ORDER`

### 5. Other Fixes

- **`.gitignore` created** — blocks `*.xlsx`, `*.parquet`, `outputs/`, `__pycache__/`
- **`sys.exit(1)` replaced with `raise ValueError`** in `data_loader.py`
- **DataFrame mutation fixed** — modules 4 & 5 use local variables instead of mutating source
- **Dependencies pinned** in `requirements.txt`
- **Module 6 optimized** — `groupby().apply(count_fn)` replaced with `.nunique()`
- **`importlib.import_module()`** replaces `__import__()` in `run_all.py`
- **Enrichment uses single `df.copy()`** at top of `enrich()` instead of 5 copies

## Verification

| Check | Command / Method | Expected |
|-------|-----------------|----------|
| PII in parquet | `pd.read_parquet("enriched_voters.parquet").columns` | No `IC`, `Nama`, `ICSpouse`, `NoRumah` |
| assert removal | `grep -rn "^\\s*assert " *.py` | Zero matches |
| Constants centralized | `grep -rn "EXPECTED_TOTAL" *.py` | Zero matches (renamed to `EXPECTED_ROWS`, defined once) |
| sys.exit removal | `grep -rn "sys.exit" *.py` | Zero matches |
| Verification summary | `python3 -c "from run_all import generate_verification_summary; generate_verification_summary()"` | All 10 checks PASS |

## Prevention Strategies

### PII in Data Pipelines

- Define a `PARQUET_COLUMNS` or `SAFE_COLUMNS` allowlist — never write raw DataFrames to disk
- Use a thin wrapper (e.g., `safe_to_parquet(df, path)`) that filters columns and raises if sensitive column names are detected
- Add a pre-commit hook scanning for 12-digit numeric sequences (`\b\d{12}\b`) to catch IC leaks
- In CI: assert no file matching `*.xlsx`, `*.csv`, or `*.parquet` exists in `git ls-files`

### Pandas Performance

- Treat `df.apply(func, axis=1)` as a code smell — vectorize with `str.contains`, `np.select`, `.map(dict)` by default
- For classification tasks, pre-compute a mapping from unique values and use `.map()` — avoids calling the function N times when there are only K unique inputs (K << N)
- Add performance regression benchmarks: assert full pipeline completes within a time threshold

### Data Validation

- Ban `assert` outside test files — enforce via linting (`ruff S101` or `flake8-bugbear B011`)
- Use explicit `if not condition: raise ValueError(msg)` for all runtime data checks
- Document the rule in `CLAUDE.md`

### Constants Management

- Single source of truth in one module (e.g., `data_loader.py` or `constants.py`)
- All other modules import from there
- Lint for hardcoded magic numbers appearing outside the constants module

### .gitignore Hygiene

- Add `.gitignore` at project initialization, before any commits
- For already-committed sensitive files: use `git filter-repo` to remove from history
- Consider storing source data in a private object store rather than the repository

## Related Documentation

No prior solution documents existed in `docs/solutions/`. This is the first entry.

Related planning documents:
- `docs/plans/2026-03-19-001-feat-setiawangsa-voter-roll-analysis-plan.md` (status: completed)
- `docs/brainstorms/2026-03-19-setiawangsa-voter-analysis-requirements.md`
