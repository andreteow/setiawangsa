---
date: 2026-03-19
topic: setiawangsa-voter-analysis
---

# P.118 Setiawangsa Comprehensive Voter Roll Analysis

## Problem Frame

MUDA needs a data-driven understanding of the ~95,700 registered voters in P.118 Setiawangsa to inform ground-game strategy, resource allocation, and electoral positioning. The SPR electoral roll contains name, IC, gender, birth year, locality, and polling district data — enough to derive demographic profiles, geographic concentration, ethnicity estimates, and housing-type segmentation. No analysis has been done yet on this dataset.

## Requirements

### Module 1: Voter Concentration Map
- R1. Rank all 17 DMs by total voter count with gender breakdown
- R2. Rank all 529 lokaliti by voter count; identify the top 20 highest-population lokaliti
- R3. Produce a summary showing what % of total constituency votes each DM controls

### Module 2: Age Segmentation
- R4. Classify voters into age bands: Undi18 youth (18-27, born 1999-2008), young adults (28-39), middle-age (40-59), seniors (60+)
- R5. Cross-tabulate age bands by DM and by gender
- R6. Identify DMs/lokaliti with the highest concentration of young voters (MUDA's potential base)

### Module 3: Ethnicity Inference
- R7. Classify voters as Malay, Chinese, Indian, or Other using a multi-signal approach: name pattern heuristics (bin/binti, Chinese surnames, Indian name patterns) refined with birth-state signals from IC digits 3-4
- R8. Target ~90-95% classification accuracy; document methodology and known limitations
- R9. Cross-tabulate ethnicity by DM, age band, and gender
- R10. Identify the ethnic composition of each DM to understand which are Malay-majority, mixed, or minority-heavy

### Module 4: Housing-Type Classification
- R11. Classify each lokaliti as one of: PPR (public housing), Flat, Taman (landed residential), Condo/Apartment, Institutional (MINDEF/PULAPOL), or Other — based on NamaLokaliti keywords
- R12. Aggregate voter counts by housing type, cross-tabulated with ethnicity and age band
- R13. Identify B40-proxy areas (PPR + Flat) vs middle-class areas (Taman/Condo)

### Module 5: Birth-State Migration Analysis
- R14. Decode IC digits 3-4 to determine birth state for each voter
- R15. Produce a breakdown of KL-born vs out-of-state-born voters by DM
- R16. Identify top origin states (e.g., Kelantan, Johor, Pahang) and where those migrants concentrate geographically

### Module 6: Household Clustering
- R17. Group voters by NoRumah + Kodlokaliti to estimate household units
- R18. Calculate household size distribution (single occupants, small families, large households)
- R19. Identify multi-generational households (3+ age bands in same address)

### Module 7: Institutional Voter Blocks
- R20. Isolate MINDEF and PULAPOL DMs; profile their demographics separately (age, gender, ethnicity, household size)
- R21. Size institutional voters as % of total constituency

### Module 8: Gender Ratio Analysis
- R22. Calculate gender ratio (M:F) per DM and per lokaliti
- R23. Flag areas with unusual gender skews (>60% one gender) for targeted outreach planning

## Output Format
- R24. Reusable Python scripts (.py) for each module that can be re-run as data updates
- R25. CSV summary tables for all cross-tabulations and rankings
- R26. Charts (matplotlib/seaborn, exported as PNG) for key visualizations: age pyramids, ethnicity pie/bar charts, DM voter concentration bar charts, housing-type breakdown
- R27. A Jupyter notebook integrating all modules with inline commentary for team presentation

## Scope Boundaries
- No predictive modeling of voting behavior (no historical election results in this dataset)
- No voter contact/outreach tracking — this is analysis only
- IC numbers are PII: never output full ICs in any report or export; use masked format or aggregates only
- Ethnicity inference is probabilistic, not definitive — always label as "estimated" in outputs
- No geospatial mapping (no lat/long coordinates available) — geographic analysis is by DM/lokaliti name only

## Success Criteria
- All 8 modules produce verified, accurate output from the 95,732-row dataset
- Ethnicity classification covers 90%+ of voters with documented methodology
- Outputs are structured enough to directly inform canvassing prioritization (e.g., "DM X has Y% young Malay voters in PPR housing — high priority for MUDA outreach")
- All CSVs, charts, and notebooks are in the working directory and reproducible

## Key Decisions
- **Ethnicity inference approach**: Multi-signal (name heuristics + IC birth-state) for best accuracy, with limitations documented
- **Age bands**: Using Undi18 youth (18-27), young adults (28-39), middle-age (40-59), seniors (60+) to align with Malaysian political generational categories
- **Housing classification**: Keyword-based from NamaLokaliti (PPR, Flat, Taman, Condo, etc.) — simple and sufficient given the data
- **Output format**: Full suite (scripts + CSVs + charts + notebook) for maximum utility

## Dependencies / Assumptions
- Birth year 2000 in the data corresponds to age 26 in 2026 (current year)
- IC digit 3-4 state codes follow standard MyKad encoding
- Name-based ethnicity patterns assume standard Malaysian naming conventions
- NoRumah + Kodlokaliti combination is a reasonable proxy for household unit (may not be perfect for apartments with sub-units)

## Outstanding Questions

### Deferred to Planning
- [Affects R7][Needs research] What Chinese surname list and Indian name pattern database to use for ethnicity inference? Need to compile or find a Malaysian-specific list.
- [Affects R17][Technical] How to handle missing NoRumah values (812 records) in household clustering — exclude or assign to "unknown" households?
- [Affects R26][Technical] Which specific chart types best communicate each module's findings to a non-technical MUDA team audience?

## Next Steps

→ `/ce:plan` for structured implementation planning
