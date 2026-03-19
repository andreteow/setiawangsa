---
title: "feat: Comprehensive Voter Roll Analysis for P.118 Setiawangsa"
type: feat
status: completed
date: 2026-03-19
origin: docs/brainstorms/2026-03-19-setiawangsa-voter-analysis-requirements.md
---

# feat: Comprehensive Voter Roll Analysis for P.118 Setiawangsa

## Overview

Build a complete analytical suite that transforms the SPR electoral roll (~95,732 voter records) for P.118 Setiawangsa into actionable intelligence for MUDA's ground-game strategy. The analysis spans 10 modules covering data validation, demographic profiling, geographic concentration, ethnicity inference, housing-type segmentation, migration patterns, household clustering, institutional voter blocks, gender analysis, and composite priority scoring.

## Problem Statement / Motivation

MUDA needs data-driven answers to: Where should we canvass? Who lives there? What are their demographics? Which areas have the highest concentration of potential MUDA supporters (young, urban, multi-ethnic)? Currently the raw Excel file is unusable for strategic decisions. This analysis turns it into structured, visual, actionable outputs. (see origin: `docs/brainstorms/2026-03-19-setiawangsa-voter-analysis-requirements.md`)

## Proposed Solution

A phased Python pipeline that:
1. Validates and cleans the raw data (Module 0 — surfaced by spec analysis)
2. Derives enriched fields (ethnicity, age band, housing type, birth state) on a shared dataframe
3. Runs 8 analytical modules that produce cross-tabulations
4. Generates a composite canvassing priority score per DM/lokaliti (Module 9 — surfaced by spec analysis)
5. Outputs everything as reusable scripts, CSVs, charts, and a Jupyter notebook

## Technical Approach

### Architecture

```
P.118 SETIAWANGSA.xlsx
        │
        ▼
┌─────────────────────┐
│  data_loader.py      │  ← Load Excel, validate, clean
│  Module 0: Validate  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────────┐
│  enrichment.py           │  ← Add derived columns to master DF
│  - age_band              │
│  - estimated_ethnicity   │
│  - housing_type          │
│  - birth_state           │
│  - birth_state_name      │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Per-module analysis scripts          │
│  module_1_concentration.py            │
│  module_2_age.py                      │
│  module_3_ethnicity.py                │
│  module_4_housing.py                  │
│  module_5_migration.py                │
│  module_6_household.py                │
│  module_7_institutional.py            │
│  module_8_gender.py                   │
│  module_9_priority_scoring.py         │
└────────┬─────────────────────────────┘
         │
         ▼
┌───────────────────────┐
│  outputs/              │
│  ├── csv/              │  ← Summary tables
│  ├── charts/           │  ← PNG visualizations
│  └── notebook/         │  ← Jupyter integration
└───────────────────────┘
```

**Shared Data Contract:** All modules operate on a single enriched DataFrame with these derived columns:

| Column | Type | Values | Added By |
|--------|------|--------|----------|
| `age` | int | 2026 - TahunLahir | enrichment.py |
| `age_band` | str | `"22-27 (Youth)"`, `"28-39 (Young Adult)"`, `"40-59 (Middle Age)"`, `"60+ (Senior)"` | enrichment.py |
| `estimated_ethnicity` | str | `"Malay"`, `"Chinese"`, `"Indian"`, `"Other"` | enrichment.py |
| `ethnicity_confidence` | str | `"high"`, `"medium"`, `"low"` | enrichment.py |
| `ethnicity_signals` | str | Comma-separated signals used (e.g., `"bin/binti,birth_state"`) | enrichment.py |
| `housing_type` | str | `"PPR"`, `"Flat"`, `"Taman"`, `"Condo/Apartment"`, `"Institutional"`, `"Other"` | enrichment.py |
| `birth_state_code` | str | IC digits 3-4 (e.g., `"10"`) | enrichment.py |
| `birth_state_name` | str | State name (e.g., `"Selangor"`, `"Kelantan"`) | enrichment.py |
| `norumah_normalized` | str | Cleaned NoRumah value | enrichment.py |

### Implementation Phases

#### Phase 1: Foundation (Module 0 + Data Loading)

**Goal:** Load, validate, and clean the raw data. Establish project infrastructure.

**Tasks:**

- [ ] Create `requirements.txt` with: `pandas`, `openpyxl`, `matplotlib`, `seaborn`, `jupyter`, `numpy`, `pyarrow` (for parquet support)
- [ ] Create `data_loader.py`:
  - Load `P.118 SETIAWANGSA.xlsx` via pandas/openpyxl
  - Return raw DataFrame
- [ ] Create Module 0: Data Validation (`module_0_validation.py`):
  - Check for duplicate IC numbers and flag/report them
  - Validate IC format (exactly 12 digits, numeric)
  - Check for null/blank Nama fields
  - Flag birth years before 1926 (age 100+ in 2026) as probable data anomalies — **exclude from age analysis, include in total voter counts**
  - Verify all 17 expected DMs are present
  - Count actual unique lokaliti and reconcile with CLAUDE.md (~515) vs actual count (529)
  - Check Kodlokaliti ↔ NamaLokaliti consistency (same code = same name)
  - Report the 812 missing NoRumah records — which DMs/lokaliti are they in?
  - Generate `outputs/csv/validation_report.csv` with all flagged records
  - Print summary statistics to console
- [ ] Create `outputs/` directory structure: `outputs/csv/`, `outputs/charts/`, `outputs/notebook/`

**Key Decision:** Voters with birth year < 1926 (age 100+) will be flagged as anomalies and excluded from age band analysis but retained in total voter counts and other modules. (Decision made during spec analysis — these are likely deceased voters not yet removed from the roll.)

#### Phase 2: Enrichment (Derived Fields)

**Goal:** Add all derived columns to the master DataFrame and save as parquet for downstream modules.

**Tasks:**

- [ ] Create `enrichment.py` with the following functions:
- [ ] After enrichment, save the enriched DataFrame to `outputs/enriched_voters.parquet` (fast columnar format; all downstream modules load this instead of re-reading Excel)

**2a. Age Band Calculation**
- `age = 2026 - TahunLahir` (approximation — no birth month/day available)
- Age bands aligned to actual data range (birth years 1926–2004):
  - `"22-27 (Youth)"` — born 1999-2004 (Undi18 cohort present in data)
  - `"28-39 (Young Adult)"` — born 1987-1998
  - `"40-59 (Middle Age)"` — born 1967-1986
  - `"60+ (Senior)"` — born 1926-1966
  - `"Anomaly (100+)"` — born before 1926 (excluded from age analysis)
- **Note:** The data only contains voters born through 2004 (age 22+), so the youngest Undi18 voters (18-21) are absent from this roll snapshot. Label adjusted from original spec's "18-27" to "22-27" to match actual data. (see origin: R4 + SpecFlow Gap 2.2)

**2b. Ethnicity Inference**

Signal hierarchy (conflict resolution order — highest priority first):

1. **Definitive markers (confidence: high):**
   - `A/L` or `A/P` in name → Indian (nearly 100% reliable)
   - `bin` or `binti` in name → Malay (with caveats for non-Malay Muslims)

2. **Name pattern matching (confidence: medium-high):**
   - Chinese surname list: Match against a curated list of ~100 common Malaysian Chinese surnames accounting for romanization variants (Tan/Chen/Chan, Ng/Woo/Wu, Lee/Li, Wong/Ong, Lim/Lin, etc.)
   - Indian name patterns: Common Indian first/last names (Kumar, Muthu, Samy, Raj, Devi, Lakshmi, etc.) beyond A/L/A/P
   - Malay name patterns: Common Malay first names (Muhammad, Ahmad, Siti, Nur, etc.) for names without bin/binti

3. **Birth-state refinement (adjusts confidence):**
   - IC state codes mapped using standard MyKad encoding:
     - `01-02` = Johor, `03-04` = Kedah, `05-06` = Kelantan, `07` = Melaka, `08` = Negeri Sembilan, `09` = Pahang, `10` = Penang, `11` = Perak, `12-13` = Perlis, `14` = Selangor, `15-16` = Terengganu, `21-22` = Johor, `23-24` = Kedah, `25-27` = Kelantan, `28-29` = Melaka, `30` = NS, `31-33` = Pahang, `34-35` = Penang, `36-38` = Perak, `39-40` = Perlis, `41-43` = Sabah, `44-46` = Sarawak, `47-49` = Selangor, `50-52` = Terengganu, `53-54` = WP KL, `55-56` = WP Labuan, `57-59` = WP Putrajaya/Sabah, `60` = Brunei, `61-62` = Indonesia/Cambodia, `63-68` = other countries, `71-82` = foreign-born
   - Born in Kelantan/Terengganu → strengthens Malay signal
   - Born in Sabah/Sarawak → if name doesn't match Malay/Chinese/Indian patterns, classify as "Other (Bumiputera)"
   - Born outside Malaysia (codes 60-82) → reduce confidence of name-based inference
   - Born in Penang/Selangor/KL → no adjustment (multi-ethnic states)

4. **Conflict resolution:**
   - If name says Malay (bin/binti) but birth state is Sabah → keep Malay (Muslim converts common)
   - If name is ambiguous and birth state is strongly associated with one ethnicity → use birth state signal
   - If all signals conflict or are weak → classify as "Other" with confidence "low"

5. **Validation approach:**
   - After initial classification, randomly sample 200 records from each ethnicity category (800 total)
   - Manual spot-check against name patterns to estimate accuracy
   - Report confusion matrix and per-category accuracy in methodology notes
   - Target: 90%+ overall, document where it falls short

- [ ] Create the Chinese surname list (`data/chinese_surnames.txt`) — ~100 entries with romanization variants
- [ ] Create the Indian name list (`data/indian_names.txt`) — common first and last names
- [ ] Create the IC state code mapping (`data/state_codes.json`)

**2c. Housing-Type Classification**

Keyword-to-category mapping table:

| Keywords in NamaLokaliti | Housing Type |
|--------------------------|-------------|
| `PPR` | PPR |
| `FLAT`, `PANGSA`, `RUMAH PANGSA` | Flat |
| `TAMAN`, `TMN`, `KAMPUNG`, `KG`, `DESA`, `JALAN` | Taman (Landed) |
| `KONDOMINIUM`, `CONDO`, `RESIDENSI`, `PANGSAPURI`, `APARTMENT`, `VISTA`, `SUITES` | Condo/Apartment |
| `MINDEF`, `PULAPOL`, `POLIS`, `TENTERA`, `ASRAMA` | Institutional |
| *(no match)* | Other |

- [ ] Review actual NamaLokaliti values in the data to refine keywords
- [ ] Target: "Other" category should be <10% of voters; if exceeded, review and add keywords
- [ ] Note limitation: some lokaliti names are geographic (e.g., "SEKSYEN 10 WANGSA MAJU") — classify by inspecting the full name, not just first keyword

**2d. Birth-State Parsing**
- Extract IC digits at positions [6:8] (0-indexed) — these are the state code digits
- Map to state names using the state code JSON
- Handle edge cases: codes 60-82 = foreign-born, label as country/region

**2e. NoRumah Normalization**
- Strip leading/trailing whitespace
- Normalize common prefixes: `"NO."`, `"NO "`, `"LOT "` → remove prefix
- Uppercase all values
- Handle the 812 null values: assign to a sentinel value `"MISSING"` — exclude from household clustering but count in reports

#### Phase 3: Analytical Modules

Each module reads the enriched DataFrame and produces CSVs and chart data.

**Module 1: Voter Concentration Map** (`module_1_concentration.py`)
- [ ] R1: Rank 17 DMs by voter count with gender breakdown → `dm_voter_counts.csv`
- [ ] R2: Rank all lokaliti by voter count; top 20 table → `lokaliti_top20.csv`, `lokaliti_all_ranked.csv`
- [ ] R3: DM as % of total constituency → `dm_share_pct.csv`
- [ ] Chart: Horizontal bar chart of DM voter counts (stacked by gender)
- [ ] Chart: Top 20 lokaliti bar chart

**Module 2: Age Segmentation** (`module_2_age.py`)
- [ ] R4-R5: Age band distribution overall + by DM + by gender → `age_by_dm.csv`, `age_by_gender.csv`
- [ ] R6: DMs/lokaliti with highest youth concentration → `youth_concentration.csv`
- [ ] Chart: Population pyramid (age bands by gender)
- [ ] Chart: Youth % by DM (bar chart)

**Module 3: Ethnicity Analysis** (`module_3_ethnicity.py`)
- [ ] R9: Ethnicity by DM, age band, gender cross-tabs → `ethnicity_by_dm.csv`, `ethnicity_by_age.csv`, `ethnicity_by_gender.csv`
- [ ] R10: Ethnic composition per DM → `dm_ethnic_composition.csv`
- [ ] Methodology report with accuracy notes → `ethnicity_methodology.txt`
- [ ] Chart: Stacked bar chart of ethnic composition per DM
- [ ] Chart: Ethnicity × age band heatmap

**Module 4: Housing-Type Analysis** (`module_4_housing.py`)
- [ ] R11-R12: Voter counts by housing type, cross-tabbed with ethnicity and age → `housing_type_summary.csv`, `housing_ethnicity.csv`, `housing_age.csv`
- [ ] R13: B40-proxy areas (PPR + Flat) vs middle-class (Taman/Condo) → `income_proxy.csv`
- [ ] Note caveat: not all flat dwellers are B40; this is a rough proxy
- [ ] Chart: Housing type distribution (pie/donut chart)
- [ ] Chart: B40-proxy vs middle-class by DM

**Module 5: Birth-State Migration** (`module_5_migration.py`)
- [ ] R14-R15: KL-born vs out-of-state breakdown by DM → `birth_state_by_dm.csv`
- [ ] R16: Top origin states and their geographic concentration → `top_origin_states.csv`, `origin_by_dm.csv`
- [ ] Chart: Top 10 origin states (bar chart)
- [ ] Chart: KL-born % by DM

**Module 6: Household Clustering** (`module_6_household.py`)
- [ ] R17: Group by `norumah_normalized` + `Kodlokaliti` → `household_clusters.csv`
- [ ] R18: Household size distribution with buckets: 1 (single), 2-3 (small), 4-6 (medium), 7-9 (large), 10+ (very large) → `household_size_distribution.csv`
- [ ] R19: Multi-generational flag (voters spanning 3+ age bands at same address) → `multigenerational_households.csv`
- [ ] Exclude 812 records with missing NoRumah from clustering; report separately
- [ ] Note limitation: NoRumah + Kodlokaliti is an imperfect household proxy, especially in high-rises
- [ ] Chart: Household size distribution histogram
- [ ] Chart: Multi-generational household % by DM

**Module 7: Institutional Voter Blocks** (`module_7_institutional.py`)
- [ ] R20: Filter MINDEF + PULAPOL DMs; full demographic profile (age, gender, ethnicity, housing type) → `institutional_profile.csv`
- [ ] R21: Institutional voters as % of total → included in profile
- [ ] Strategic note: These voters historically lean pro-government; sizing them helps MUDA understand the "floor" of non-contestable votes
- [ ] Chart: Institutional vs civilian voter comparison

**Module 8: Gender Ratio Analysis** (`module_8_gender.py`)
- [ ] R22: Gender ratio per DM and per lokaliti → `gender_ratio_dm.csv`, `gender_ratio_lokaliti.csv`
- [ ] R23: Flag areas with >60% one gender — but note that institutional DMs (MINDEF/PULAPOL) will naturally exceed this threshold → `gender_skew_areas.csv`
- [ ] Chart: Gender ratio by DM (diverging bar chart)

**Module 9: Composite Priority Scoring** (`module_9_priority.py`) *(New — surfaced by spec analysis)*
- [ ] Combine dimensions into a weighted priority score per DM and per lokaliti:
  - Youth concentration (% voters aged 22-39) — weight: 0.35 (MUDA's core demographic)
  - Ethnic diversity (Simpson's diversity index) — weight: 0.25 (multi-ethnic areas align with MUDA's positioning)
  - B40-proxy (% PPR + Flat) — weight: 0.25 (service-oriented messaging resonates)
  - Household density (avg household size) — weight: 0.15 (door-to-door efficiency)
  - Non-institutional (exclude MINDEF/PULAPOL from ranking) — filter, not weighted
  - All dimensions normalized to 0-1 before weighting; composite score = weighted sum
- [ ] Rank DMs and top 20 lokaliti by composite score → `priority_ranking_dm.csv`, `priority_ranking_lokaliti.csv`
- [ ] This is the most directly actionable output for MUDA's canvassing team
- [ ] Chart: Priority ranking visualization (bubble chart or ranked bar)

#### Phase 4: Integration & Output

- [ ] R24: Ensure all module scripts are standalone-runnable with `python3 module_X_*.py` (each loads `outputs/enriched_voters.parquet` — requires running enrichment first)
- [ ] R25: All CSVs in `outputs/csv/`
- [ ] R26: All charts in `outputs/charts/` as PNG (150 DPI for screen, 300 DPI for print)
  - Charts use English labels with Malay data labels (DM names, lokaliti names, housing types in Malay)
  - Use a consistent color palette across all charts; consider colorblind accessibility
- [ ] R27: Create `outputs/notebook/setiawangsa_analysis.ipynb` integrating all modules with:
  - Executive summary section for non-technical MUDA leadership
  - Per-module sections with methodology explanation, key tables, and inline charts
  - Final section: composite priority ranking with canvassing recommendations
  - All PII masked — no full IC numbers, no individual-level name exports
- [ ] Create a `run_all.py` script that executes the full pipeline: load → validate → enrich → all modules → notebook export

## Data Integrity Verification Protocol

Every stage of the pipeline includes row-count assertions to guarantee no data is silently lost.

### Layer 1: Load Verification
```
After loading Excel:
  EXPECTED_ROWS = 95732  # Update this when using a new electoral roll
  assert len(df) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS} rows, got {len(df)}"
  Print: "Loaded {len(df)} rows from Excel (expected {EXPECTED_ROWS})"
```
This confirms pandas read every row. The constant is defined once in `data_loader.py` and updated when the electoral roll changes. 95K rows is trivial for pandas — no chunking needed.

### Layer 2: Enrichment Verification
```
After adding derived columns (age_band, estimated_ethnicity, housing_type, birth_state):
  assert len(enriched_df) == len(raw_df), "Row count changed during enrichment!"
  assert enriched_df['age_band'].notna().all(), "Some rows missing age_band"
  assert enriched_df['estimated_ethnicity'].notna().all(), "Some rows missing ethnicity"
  assert enriched_df['housing_type'].notna().all(), "Some rows missing housing_type"
  Print: "Enriched {len(enriched_df)} rows — all derived columns populated"
```
Enrichment adds columns, never drops rows.

### Layer 3: Per-Module Sum Verification
Every module that produces cross-tabulations must verify totals:
```
For each cross-tab CSV:
  assert cross_tab.sum() == expected_total, "Cross-tab doesn't sum to total"
  Print: "Module X: {sum} voters accounted for (expected {total})"
```

Specific checks:
- **Module 1 (Concentration):** Sum of all DM voter counts == 95,732
- **Module 2 (Age):** Sum across all age bands == total minus anomaly exclusions; report how many excluded
- **Module 3 (Ethnicity):** Sum of Malay + Chinese + Indian + Other == 95,732
- **Module 4 (Housing):** Sum across all housing types == 95,732
- **Module 5 (Migration):** Sum across all birth states == 95,732
- **Module 6 (Household):** Sum of voters in all household clusters + 812 missing-NoRumah == 95,732
- **Module 7 (Institutional):** Institutional + civilian == 95,732
- **Module 8 (Gender):** Male + female == 95,732

### Layer 4: Final Reconciliation Report
A `verification_summary.csv` and console output that shows:

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Total rows loaded | 95,732 | ? | PASS/FAIL |
| Rows after enrichment | 95,732 | ? | PASS/FAIL |
| DM voter sum | 95,732 | ? | PASS/FAIL |
| Age band sum (excl. anomalies) | ? | ? | PASS/FAIL |
| Ethnicity sum | 95,732 | ? | PASS/FAIL |
| Housing type sum | 95,732 | ? | PASS/FAIL |
| ... | ... | ... | ... |

**If any check fails, the pipeline halts and reports the discrepancy.** This makes data loss impossible to miss.

### Layer 5: Spot-Check Sampling
- After enrichment, export a random 50-row sample with **derived fields only** (age, age_band, estimated_ethnicity, housing_type, birth_state_name — no IC, no full name) to `outputs/csv/enrichment_spot_check.csv` for manual review. Include a truncated name (first 3 chars + "***") for cross-referencing only.
- After ethnicity inference, export 200 random samples per ethnicity category (800 total) with the same PII-safe fields for accuracy validation → `outputs/csv/ethnicity_validation_sample.csv`

## PII Protection Rules

- Never output full IC numbers in any CSV, chart, or notebook
- IC digits 3-4 (birth state) may be used for analysis but not exported at individual level
- CSVs should contain aggregated summaries, not individual voter records
- The Jupyter notebook must not display individual-level data in cell outputs
- Full names (Nama) should not appear in exported outputs — aggregates only
- The raw Excel file should remain in the working directory and not be committed to any public repo

## Acceptance Criteria

### Functional Requirements
- [ ] All 10 modules (0-9) execute without errors on the full 95,732-row dataset
- [ ] Ethnicity classification covers 90%+ of voters with methodology documented
- [ ] All CSVs contain accurate aggregations that sum to expected totals
- [ ] All charts render correctly with readable labels and legends
- [ ] Jupyter notebook runs end-to-end and is presentation-ready
- [ ] Composite priority ranking produces a clear, actionable canvassing target list

### Data Quality Gates
- [ ] Module 0 validation report generated and reviewed before proceeding
- [ ] No full IC numbers appear in any output file
- [ ] Ethnicity validation spot-check completed on 800-record sample
- [ ] Housing-type "Other" category is <10% of voters

## Dependencies & Prerequisites

- Python 3.8+ with pandas, openpyxl, matplotlib, seaborn, numpy, jupyter
- The Excel file `P.118 SETIAWANGSA.xlsx` in the working directory
- Chinese surname list and Indian name list (to be created in Phase 2)
- IC state code mapping (to be created in Phase 2)

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ethnicity inference accuracy <90% | Strategic recommendations based on wrong demographics | Validation spot-check; confidence labels allow filtering low-confidence records |
| NoRumah normalization insufficient | Unreliable household clustering | Sample actual values first; document known limitations |
| "Ghost voters" (age 100+) skew analysis | Inflated senior band | Module 0 flags and excludes from age analysis |
| Housing-type keywords miss edge cases | Large "Other" bucket | Review actual NamaLokaliti values; iterate keywords until Other <10% |
| Excel file changes format in future update | Scripts break | data_loader.py validates column names on load; clear error messages |

## Sources & References

### Origin
- **Origin document:** [docs/brainstorms/2026-03-19-setiawangsa-voter-analysis-requirements.md](docs/brainstorms/2026-03-19-setiawangsa-voter-analysis-requirements.md) — Key decisions carried forward: multi-signal ethnicity inference, all-formats output, 8 analytical modules expanded to 10 with Module 0 (validation) and Module 9 (priority scoring) added based on spec analysis.

### Domain References
- MyKad state code encoding: Standard Malaysian NRIC format
- Undi18: Malaysian voting age lowered to 18 with automatic voter registration (2021)
- PPR: Program Perumahan Rakyat (public housing program)
- SPR: Suruhanjaya Pilihan Raya Malaysia (Election Commission of Malaysia)
