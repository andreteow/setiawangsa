---
title: "feat: Interactive dashboard for P.118 Setiawangsa voter analytics"
type: feat
status: active
date: 2026-03-19
origin: docs/brainstorms/2026-03-19-setiawangsa-dashboard-requirements.md
---

# feat: Interactive Dashboard for P.118 Setiawangsa Voter Analytics

## Overview

Build a static, password-gated interactive dashboard that lets MUDA volunteers and party workers explore the P.118 Setiawangsa voter roll analysis. The dashboard consumes pre-aggregated JSON data (converted from the existing CSV pipeline outputs), renders interactive charts client-side with Chart.js, and deploys to GitHub Pages with zero backend dependencies.

## Problem Statement / Motivation

MUDA's analysis pipeline already produces ~35 CSVs and 16 static charts covering demographics, housing, migration, ethnicity, gender, household structure, institutional profiles, and priority scoring for 95,732 voters across 17 DMs and 515 lokaliti. However, this data is only accessible to the analyst who produced it. Volunteers need a centralized, mobile-friendly tool to look up DM demographics in meetings, compare target areas, and identify canvassing priorities in the field. (See origin: `docs/brainstorms/2026-03-19-setiawangsa-dashboard-requirements.md`)

## Proposed Solution

A single-page application (SPA) built with vanilla HTML/CSS/JS + Chart.js, deployed as a static site on GitHub Pages. A Python build script converts CSV outputs to structured JSON files. A client-side password gate keeps casual visitors out.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  BUILD PHASE (Python)                               │
│                                                     │
│  outputs/csv/*.csv  ──→  build_dashboard_data.py    │
│                          ──→  dashboard/data/*.json  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  DASHBOARD (Static HTML/CSS/JS)                     │
│                                                     │
│  dashboard/                                         │
│  ├── index.html          (password gate + app shell)│
│  ├── css/                                           │
│  │   └── style.css       (responsive layout)        │
│  ├── js/                                            │
│  │   ├── app.js          (router + state)           │
│  │   ├── auth.js         (password gate)            │
│  │   ├── charts.js       (Chart.js wrappers)        │
│  │   ├── views/                                     │
│  │   │   ├── overview.js                            │
│  │   │   ├── dm-detail.js                           │
│  │   │   ├── lokaliti-detail.js                     │
│  │   │   ├── compare.js                             │
│  │   │   ├── priority.js                            │
│  │   │   └── housing.js                             │
│  │   └── utils.js        (formatting, helpers)      │
│  ├── data/                                          │
│  │   ├── overview.json                              │
│  │   ├── dm/                                        │
│  │   │   ├── ayer-panas-dalam.json                  │
│  │   │   ├── ayer-panas-luar.json                   │
│  │   │   └── ... (17 files)                         │
│  │   ├── lokaliti-index.json  (summary for all 515) │
│  │   ├── priority.json                              │
│  │   └── housing.json                               │
│  └── lib/                                           │
│      └── chart.min.js    (Chart.js CDN fallback)    │
│                                                     │
│  Hosted on: GitHub Pages                            │
└─────────────────────────────────────────────────────┘
```

### JSON Data Structure

**`overview.json`** — Constituency-level headline stats:
```json
{
  "total_voters": 95732,
  "gender": {"male": 49400, "female": 46332},
  "age_bands": {"22-27": ..., "28-39": ..., "40-59": ..., "60+": ...},
  "ethnicity": {"Malay": ..., "Chinese": ..., "Indian": ..., "Other": ...},
  "youth_pct": 44.2,
  "b40_pct": 9.2,
  "dm_summary": [
    {"name": "AYER PANAS DALAM", "slug": "ayer-panas-dalam", "voters": ..., "youth_pct": ..., "b40_pct": ..., "priority_rank": ...},
    ...
  ]
}
```

**`dm/{slug}.json`** — Full profile for one DM:
```json
{
  "name": "AYER PANAS DALAM",
  "voters": {"total": ..., "male": ..., "female": ...},
  "age_bands": {...},
  "ethnicity": {...},
  "housing": {...},
  "youth_concentration": ...,
  "migration": {"kl_born_pct": ..., "top_origins": [...]},
  "household": {"avg_size": ..., "multigenerational_pct": ...},
  "priority_score": ...,
  "priority_rank": ...,
  "lokaliti": [
    {"name": "...", "code": "...", "voters": ..., "ethnicity": {...}, "housing_type": "...", "age_bands": {...}},
    ...
  ]
}
```

**`priority.json`** — DM and lokaliti rankings:
```json
{
  "dm_rankings": [...],
  "lokaliti_rankings": [...],
  "institutional_zones": [...]
}
```

**`housing.json`** — Housing and socioeconomic data:
```json
{
  "type_summary": [...],
  "by_ethnicity": [...],
  "by_age": [...],
  "income_proxy_by_dm": [...]
}
```

**`lokaliti-index.json`** — Lightweight index for search/comparison (name, code, DM, voters, ethnicity summary, housing type). Full lokaliti detail is embedded in the parent DM file.

## Technical Considerations

- **No build tools or bundlers** — vanilla JS with ES modules. Chart.js loaded from CDN with a local fallback. This keeps the project simple and avoids Node.js dependencies.
- **Chart.js v4** — loaded from CDN (`cdn.jsdelivr.net/npm/chart.js`). Supports bar, doughnut, radar, and custom plugin for population pyramids. ~65KB gzipped.
- **Client-side routing** — hash-based (`#/dm/ayer-panas-dalam`, `#/compare?a=...&b=...`). No server-side routing needed for GitHub Pages.
- **Password gate** — SHA-256 hash of the password stored in `auth.js`. On page load, prompt for password, hash the input with `crypto.subtle.digest()`, compare. Store auth state in `sessionStorage` (clears on tab close). Not secure against a determined attacker inspecting source, but sufficient per origin requirements.
- **Mobile responsive** — CSS Grid + media queries. Charts resize via Chart.js `responsive: true`. Comparison mode stacks vertically on screens < 768px.
- **PII protection** — The build script only outputs aggregated data. No individual voter records, IC numbers, or names appear in any JSON file. (See origin: R9)
- **Data refresh** — Re-run `run_all.py` → `build_dashboard_data.py` → commit and push to GitHub. No live data pipeline.

## Implementation Phases

### Phase 1: Data Build Pipeline
**Goal:** Convert existing CSVs to dashboard-ready JSON files.

- [ ] Create `build_dashboard_data.py` that reads all CSVs from `outputs/csv/` and produces JSON files in `dashboard/data/`
- [ ] Generate `overview.json` from `dm_voter_counts.csv`, `age_by_gender.csv`, `ethnicity_by_dm.csv`, `youth_concentration.csv`, `income_proxy.csv`
- [ ] Generate 17 `dm/{slug}.json` files aggregating data from `age_by_dm.csv`, `ethnicity_by_dm.csv`, `housing_age.csv`, `gender_ratio_dm.csv`, `birth_state_by_dm.csv`, `priority_ranking_dm.csv`, plus lokaliti-level data from `lokaliti_all_ranked.csv`, `gender_ratio_lokaliti.csv`
- [ ] Generate `priority.json` from `priority_ranking_dm.csv`, `priority_ranking_lokaliti.csv`, `institutional_profile.csv`
- [ ] Generate `housing.json` from `housing_type_summary.csv`, `housing_ethnicity.csv`, `housing_age.csv`, `income_proxy.csv`
- [ ] Generate `lokaliti-index.json` as a lightweight lookup for search and comparison
- [ ] Verify no PII leaks into any JSON output (spot-check script)

### Phase 2: App Shell & Auth
**Goal:** Basic SPA skeleton with password gate and hash routing.

- [ ] Create `dashboard/index.html` — single HTML file with app shell, nav bar, content area
- [ ] Create `dashboard/js/auth.js` — password prompt, SHA-256 hashing via Web Crypto API, sessionStorage persistence
- [ ] Create `dashboard/js/app.js` — hash-based router mapping `#/overview`, `#/dm/:slug`, `#/compare`, `#/priority`, `#/housing` to view renderers
- [ ] Create `dashboard/css/style.css` — responsive grid layout, dark theme (zinc/neutral palette), mobile breakpoints
- [ ] Navigation: sidebar on desktop (collapsible), bottom tab bar on mobile
- [ ] Loading states for async JSON fetches

### Phase 3: Overview Page (R2)
**Goal:** Constituency-level summary with headline stats and DM summary table.

- [ ] Headline stat cards: total voters, gender split, youth %, B40 %, ethnic majority
- [ ] Age distribution bar chart (4 bands)
- [ ] Ethnic composition doughnut chart
- [ ] DM summary table (sortable by name, voters, youth %, B40 %, priority rank) with click-through to DM detail
- [ ] Gender split bar (male/female)

### Phase 4: DM Detail View (R3)
**Goal:** Full demographic profile for any selected DM.

- [ ] DM header: name, total voters, priority rank badge
- [ ] Age pyramid chart (horizontal bar, male left / female right) — or age band bar chart if pyramid is complex
- [ ] Ethnicity breakdown (horizontal stacked bar, % labels)
- [ ] Housing type distribution (doughnut)
- [ ] Gender ratio bar
- [ ] Migration origins (top 5 states, horizontal bar)
- [ ] Household stats (avg size, multi-generational %)
- [ ] Lokaliti table (sortable, clickable) with voter count, housing type, top ethnicity

### Phase 5: Lokaliti Drill-Down (R4)
**Goal:** Click a lokaliti from DM view to see its stats.

- [ ] Lokaliti detail panel (modal or inline expansion)
- [ ] Voter count, ethnicity breakdown, housing type, age band distribution
- [ ] "Back to DM" navigation
- [ ] Breadcrumb: Overview → DM → Lokaliti

### Phase 6: Comparison Mode (R5)
**Goal:** Side-by-side (desktop) or stacked (mobile) comparison of two areas.

- [ ] Comparison picker: two dropdowns, one for each area (DM or lokaliti)
- [ ] Tab toggle: "Compare DMs" vs "Compare Lokaliti"
- [ ] Paired charts: age distribution, ethnicity, housing type, key metrics table
- [ ] Highlight differences (e.g., color-code metrics where Area A > Area B)
- [ ] Stacked layout on mobile (< 768px), side-by-side on desktop

### Phase 7: Priority & Canvassing View (R6)
**Goal:** Dedicated targeting page for campaign strategy.

- [ ] DM priority ranking table with composite score breakdown (youth, diversity, B40, density weights)
- [ ] Top 20 lokaliti priority ranking
- [ ] Youth concentration heatmap (bar chart by DM, color-coded)
- [ ] B40/PPR areas highlight
- [ ] Institutional zones callout (MINDEF, PULAPOL) with separate profile cards
- [ ] Scatter plot: priority score vs voter count (identify high-potential small areas)

### Phase 8: Housing & Socioeconomic View (R7)
**Goal:** Socioeconomic lens on the constituency.

- [ ] Housing type summary (doughnut + table)
- [ ] Housing × ethnicity cross-tab (stacked bar or heatmap)
- [ ] Housing × age cross-tab
- [ ] Income proxy by DM (B40 vs middle-class bar chart)
- [ ] Household size distribution bar chart
- [ ] Multi-generational household % by DM

### Phase 9: Polish & Deploy
**Goal:** Final quality pass and GitHub Pages deployment.

- [ ] Test all views on mobile (375px), tablet (768px), desktop (1280px)
- [ ] Add print-friendly styles for meeting handouts (optional)
- [ ] Create `README.md` for the dashboard directory with setup/deploy instructions
- [ ] Configure GitHub Pages to serve from `dashboard/` directory (or `/docs`)
- [ ] Set password and document it for MUDA team distribution
- [ ] Final PII audit: grep all JSON files for IC patterns, full names
- [ ] Performance check: all pages load < 2s on 3G

## Acceptance Criteria

### Functional Requirements
- [ ] Password gate blocks access until correct password entered (R1)
- [ ] Overview page shows total voters, gender, age, ethnicity, DM table (R2)
- [ ] Any DM can be selected to view full demographic profile (R3)
- [ ] Lokaliti drill-down from DM view shows per-lokaliti stats (R4)
- [ ] Two DMs or two lokaliti can be compared side-by-side (R5)
- [ ] Priority view shows ranked DMs and lokaliti with score breakdown (R6)
- [ ] Housing view shows socioeconomic segmentation (R7)
- [ ] All charts are interactive with tooltips and responsive sizing (R8)
- [ ] No PII (IC, full names, addresses) in any JSON or rendered output (R9)
- [ ] Layout works on mobile phones (375px+) (R10)

### Non-Functional Requirements
- [ ] Page loads in < 2 seconds on broadband
- [ ] Total dashboard payload < 2MB (all JSON + JS + CSS)
- [ ] Works offline after initial load (all data is local JSON)
- [ ] No external API calls or backend dependencies

## Dependencies & Prerequisites

- Existing analysis pipeline (`run_all.py`) must have been run successfully with all CSVs in `outputs/csv/`
- Python 3.x with pandas (for `build_dashboard_data.py`)
- GitHub repository with Pages enabled
- Chart.js v4 (loaded from CDN, local fallback included)

## Scope Boundaries (from origin)

- No individual voter lookup — aggregate only
- No live data updates — manual re-run and redeploy
- No map/GIS view — out of scope for v1
- English only
- No server-side auth
- No past election results (GE15 vote counts)

## Sources & References

### Origin
- **Origin document:** [docs/brainstorms/2026-03-19-setiawangsa-dashboard-requirements.md](docs/brainstorms/2026-03-19-setiawangsa-dashboard-requirements.md) — Key decisions carried forward: static site on GitHub Pages, client-side password gate, all 9 analysis modules included, pre-process CSVs to JSON.

### Data Sources
- 35 CSV files in `outputs/csv/` (see CSV inventory in research notes)
- `enriched_voters.parquet` for any additional aggregations needed
- 9 analysis modules (`module_0` through `module_9`) + `enrichment.py`

### Technical References
- Chart.js documentation: https://www.chartjs.org/docs/
- Web Crypto API (SHA-256): https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest
- GitHub Pages documentation: https://docs.github.com/en/pages
