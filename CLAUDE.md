# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is an electoral analysis workspace for **P.118 Setiawangsa**, a Parliament constituency in Kuala Lumpur, W.P. The goal is to support **MUDA** (Malaysian United Democratic Alliance) in understanding the electorate, assessing electoral viability, and building a ground-game strategy for this constituency.

Key objectives:
- Demographic profiling of the ~95,700 registered voters
- Geographic mapping across 17 Daerah Mengundi (polling districts) and ~515 lokaliti
- Voter segmentation by age, gender, ethnicity, and locality type (PPR/flat, taman, condo)
- Political landscape assessment (incumbent strength, swing potential, MUDA's positioning)
- Identify priority areas for canvassing and outreach

## Data Source

**`P.118 SETIAWANGSA.xlsx`** — Official SPR (Election Commission) electoral roll. Single sheet, ~95,732 voter records.

| Column | Description |
|--------|-------------|
| NoSiri | Serial number |
| IC | MyKad number (12-digit NRIC) |
| ICLama | Old IC number (mostly null) |
| Nama | Full name |
| ICSpouse | Spouse IC (mostly null) |
| NoRumah | House/unit number |
| Jantina | Gender: `L` = Lelaki (Male), `P` = Perempuan (Female) |
| Kodlokaliti | Locality code |
| NamaLokaliti | Locality name (e.g., PPR SERI SEMARAK, TAMAN TIARA) |
| NamaParlimen | Parliament constituency (always SETIAWANGSA) |
| NamaDM | Daerah Mengundi / polling district |
| NamaDUN | DUN (State constituency) — always null for W.P. KL (no state seats) |
| Negeri | State (always W.P KUALA LUMPUR) |
| TahunLahir | Birth year (range: 1909–2004) |

## Constituency Structure

17 Daerah Mengundi (DM): AYER PANAS DALAM, AYER PANAS LUAR, AYER PANAS TENGAH, DESA REJANG, JALAN PAHANG, JALAN USAHAWAN, KERAMAT WANGSA, MINDEF, PKNS BATU 6 ULU KLANG, PULAPOL, SEKSYEN 10 WANGSA MAJU, SEKSYEN 5/6 WANGSA MAJU, TAMAN SETAPAK JAYA, TAMAN SETAPAK PERMAI, TAMAN SETIAWANGSA, TAMAN SRI RAMPAI, TAMAN TASIK.

Gender split: ~49,400 male / ~46,300 female.

## Malaysian Electoral Context

- IC digits 3–4 encode birth state; digits 1–6 are birthdate (YYMMDD). Ethnicity can be probabilistically inferred from name patterns (Malay, Chinese, Indian, others).
- PPR = Program Perumahan Rakyat (public housing) — typically lower-income B40 voters.
- MINDEF and PULAPOL are military/police institutional areas with distinct voting patterns.
- Setiawangsa is an urban KL seat — historically mixed Malay-majority with significant Chinese and Indian minorities.
- W.P. Kuala Lumpur has no DUN/state assembly seats, only Parliament seats.

## Working Conventions

- Use Python (pandas/openpyxl) for data analysis. The Excel file is large (~95K rows); prefer chunked reads or pandas for performance.
- When inferring ethnicity from names, document methodology and accuracy limitations clearly.
- Treat IC numbers as **sensitive PII** — never output full IC numbers in reports or exports. Use masked format (e.g., `****01030904`) or aggregate only.
- All analysis outputs (CSVs, charts, reports) should go into this working directory.
- Currency and political terminology should use Malaysian conventions (RM, BN, PH, PN, MUDA, SPR, etc.).
