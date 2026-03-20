---
date: 2026-03-19
topic: setiawangsa-dashboard
---

# P.118 Setiawangsa Interactive Dashboard

## Problem Frame

MUDA volunteers and party workers need a centralized, interactive way to explore the P.118 Setiawangsa voter roll analysis. Currently the analysis outputs are scattered across ~35 CSVs and 16 static charts — useful for the analyst who produced them, but not accessible for team members who need to quickly look up a DM's demographics, compare areas, or identify canvassing priorities during meetings and field work.

## Requirements

- R1. **Password-gated access** — A client-side password screen (hashed password check) prevents casual access. Not server-side secure, but sufficient to keep opponents and random visitors out.
- R2. **Constituency overview** — Landing page showing headline stats: total voters, gender split, age distribution, ethnic composition, and a summary of all 17 DMs.
- R3. **DM-level views** — Select any Daerah Mengundi to see its full demographic profile: voter count, age pyramid, ethnicity breakdown, gender ratio, housing types, youth concentration, migration origins, and priority score.
- R4. **Lokaliti drill-down** — From a DM view, click into any lokaliti to see its specific stats (voter count, ethnicity, housing type, age profile).
- R5. **Comparison mode** — Side-by-side comparison of two DMs or two lokaliti across key metrics (voter count, ethnicity, age distribution, housing type, priority score).
- R6. **Priority & canvassing view** — Dedicated page showing DM and lokaliti priority rankings, youth concentration hotspots, B40/PPR areas, and institutional zones (MINDEF, PULAPOL).
- R7. **Housing & socioeconomic view** — PPR/flat vs condo vs taman breakdowns, B40 proxy indicators, household size distributions.
- R8. **Interactive charts** — Charts respond to filters and selections (not just static PNGs). Tooltips on hover, clickable elements for drill-down.
- R9. **PII protection** — No individual voter names, IC numbers, or addresses exposed. All data is aggregated at lokaliti level or higher.
- R10. **Mobile-friendly** — Responsive layout that works on phones, since volunteers will use it in the field.

## Success Criteria

- A MUDA volunteer can look up any DM's demographics in under 10 seconds
- Team leads can compare two target areas side-by-side during a strategy meeting
- The dashboard loads from GitHub Pages with no backend dependencies
- All existing analysis modules (age, ethnicity, housing, migration, household, institutional, gender, priority) are represented

## Scope Boundaries

- **No individual voter lookup** — this is aggregate analytics only
- **No live data updates** — data is pre-processed from the existing pipeline; refresh by re-running the pipeline and redeploying
- **No map/GIS view** — geographic visualization is out of scope for v1 (could be a future addition)
- **English only** — no BM translation needed
- **No server-side auth** — client-side password gate is acceptable
- **No past election results** — only voter roll demographics, not GE15 vote counts

## Key Decisions

- **Static site on GitHub Pages**: No backend, no hosting costs, simple deployment. Trade-off: client-side password is not truly secure.
- **Pre-process CSVs to JSON**: A build step converts the existing CSV outputs into JSON files the dashboard consumes. Charts are rendered client-side (not static PNGs).
- **All analysis modules included**: Comprehensive rather than selective — volunteers get the full picture.

## Dependencies / Assumptions

- The existing analysis pipeline (`run_all.py`) produces correct, up-to-date CSVs in `outputs/csv/`
- The `enriched_voters.parquet` file contains the enriched dataset if deeper aggregations are needed
- GitHub Pages repo can be set to private (GitHub Pro/Team) or the client-side gate is sufficient for a public repo

## Outstanding Questions

### Deferred to Planning
- [Affects R8][Technical] Which charting library to use — Chart.js (lighter) vs Plotly.js (more features) vs D3 (most flexible)?
- [Affects R3-R4][Technical] Exact data structure for the JSON files — one file per DM? One big file? Trade-offs for load time vs simplicity.
- [Affects R5][Needs research] Best UX pattern for comparison mode on mobile — tabs vs swipe vs stacked layout?
- [Affects R1][Technical] Password hashing approach for the client-side gate — SHA-256 hash in JS, or a simpler obfuscation?
- [Affects R2][Needs research] What headline stats are most useful for the overview page — need to review all CSV outputs to determine the best summary metrics.

## Next Steps

-> `/ce:plan` for structured implementation planning
