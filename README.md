# P.118 Setiawangsa Electoral Analysis

Electoral analysis workspace for **P.118 Setiawangsa**, a Parliament constituency in Kuala Lumpur, W.P. — supporting **MUDA** (Malaysian United Democratic Alliance) in understanding the electorate and building a ground-game strategy.

## Objectives

- Demographic profiling of ~95,700 registered voters
- Geographic mapping across 17 Daerah Mengundi (polling districts) and ~515 lokaliti
- Voter segmentation by age, gender, ethnicity, and locality type (PPR/flat, taman, condo)
- Political landscape assessment (incumbent strength, swing potential, MUDA positioning)
- Priority area identification for canvassing and outreach

## Data

Source: Official SPR (Election Commission) electoral roll (`P.118 SETIAWANGSA.xlsx`) — ~95,732 voter records with demographics, locality, and polling district information.

**Note:** IC numbers are sensitive PII and must never be output in full. Use masked format or aggregates only.

## Constituency Structure

17 Daerah Mengundi: Ayer Panas Dalam, Ayer Panas Luar, Ayer Panas Tengah, Desa Rejang, Jalan Pahang, Jalan Usahawan, Keramat Wangsa, MINDEF, PKNS Batu 6 Ulu Klang, PULAPOL, Seksyen 10 Wangsa Maju, Seksyen 5/6 Wangsa Maju, Taman Setapak Jaya, Taman Setapak Permai, Taman Setiawangsa, Taman Sri Rampai, Taman Tasik.

## Tools

- Python (pandas, openpyxl) for data analysis
- Claude Code for AI-assisted analysis and reporting

## Project Structure

```
├── P.118 SETIAWANGSA.xlsx   # SPR electoral roll data
├── docs/
│   ├── brainstorms/         # Requirements and brainstorm documents
│   ├── plans/               # Implementation plans
│   └── solutions/           # Documented solutions and learnings
├── CLAUDE.md                # Claude Code project instructions
└── README.md
```
