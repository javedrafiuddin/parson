# Screen log and coverage ledger

Rule: a narrowing step that is not in this ledger did not happen; a name cut without a logged reason is restored.
As-of 2026-11-10. Prices: Yahoo chart API daily closes through 2026-11-09 (delayed); Nasdaq API for warrant history and quotes.

## Coverage ledger — R2 (universe construction)

| # | Step | Names in | Names out | Cut | Rule / evidence |
|---|---|---|---|---|---|
| F0 | Field enumeration | — | 14,177 | — | field enumerated: 13241 listed securities (Nasdaq Trader directory) + 936 OTC tickers of SEC registrants (EDGAR submissions, exchanges=OTC) |
| F1 | Instrument scope | 14,177 | 7,455 | 6,722 | instrument scope = common/ADR/warrant/convertible-or-preferred/OTC common; cut by type: {"etf": 5784, "unit": 322, "fund_or_etn": 318, "note": 190, "right": 108} |
| F2 | EDGAR CIK mapping | 7,455 | 6,794 | 661 | maps to an EDGAR CIK that has filed XBRL periodic reports (submissions.tickers; base-symbol fallback for instrument lines) |
| F3 | Filing floor | 6,794 | 5,444 | 1,350 | filing floor: 10-K and 10-Q both filed since 2025-11-10; of the 1350 cut, 1004 are 20-F/40-F-only foreign issuers, the rest are delinquent/new/non-reporting |
| F4 | Price floor | 5,444 | 5,338 | 106 | price floor: >= 60 sessions of history and a quote within the last 10 sessions (Yahoo chart API, delayed) |
| F5 | Liquidity floor | 5,338 | 3,891 | 1,447 | liquidity floor: 20-day average dollar volume >= $250k (common/ADR/OTC) or >= $50k (warrants, preferreds) |
| D1 | Cheap damage scan (Section 5.2 priced-for-failure) | 3,891 | 1,930 | 1,961 | cheap damage scan, any of: drawdown>=60% from 3y high (935), EV<2.0x TTM revenue (1346), mcap<$500M with TTM revenue>$20M (571); two or more tests: 684 |

**Answer to "of the full tradable field, how many were examined, how many remain, what removed the rest?"**
14,177 securities were enumerated (13,241 exchange-listed + 936 OTC tickers of SEC registrants). 1,930 remain after R2.
Removed: 6,722 out-of-scope instruments (5,784 ETFs, 322 units, 318 funds/ETNs, 190 notes, 108 rights); 661 with no EDGAR
periodic-report CIK; 1,350 failing the 10-K + 10-Q filing floor (1,004 of them 20-F/40-F-only foreign issuers); 106 with no usable
price history; 1,447 below the liquidity floor; 1,961 not priced for failure on any of the three Section 5.2 tests.
Per-name cut lists: `data/tmp/cut_F3.csv`, `cut_F4.csv`, `cut_F5.csv` (rebuildable); full scan table: `data/derived/field_scan.parquet`.

R2 universe by list-building bucket (a bucket confers no advantage): US-listed common stock 1,825, Tradable convertible/preferred 78, OTC with current SEC filings 10, US-listed ADR/ADS (10-K/10-Q filer) 10, Listed warrant 7.
Damage tests passed: one test 1,246; two 446; all three 238.

Notes on method limits (also in could_not_verify.md):
- NYSE-family warrants have no daily history at any reachable source; their liquidity test used the last session's consolidated
  dollar volume from the Nasdaq quote API (column `adv_src` in the scan table).
- Market cap = Nasdaq screener value where available, else price x as-filed shares. 103 universe names show a > 30% mismatch between
  the two (ADS ratios, multi-class share counts, recent reverse splits); they are flagged `mcap_mismatch` and their share counts
  must be rebuilt from the filing itself in R3 before any ranked use.
- Pre-merger SPAC commons, crypto trusts and similar non-operating vehicles are still in the R2 list (no theme or business
  pre-filter is applied at R2 by design); they meet the Stage 1 real-business test in R3.

## Coverage ledger — R3 Stage 1 (code pass over all 1,930 universe names; Section 5.2 filters computable from filed data)

| # | Step | Names in | Names out | Cut | Rule / evidence |
|---|---|---|---|---|---|
| S1 | Stage 1 hard filters (code) | 1,930 | 1,723 | 207 | fails: runway < 12 months with no financing document filed since the balance sheet (95); late filer (NT 10-K/10-Q) with < 12 months runway (70); 8-K item 4.02 non-reliance/restatement inside 12 months (39); exchange financial-status flag (3). Per-name outcomes: `data/derived/stage1.parquet` column `stage1` |

| Stage 1 outcome | Names |
|---|---|
| PASS | 1,509 |
| NEEDS_FILING_CHECK: lead asset | 142 |
| FAIL: runway<12m, no financing filed since | 95 |
| NEEDS_FILING_CHECK: survival | 72 |
| FAIL: late filing (NT) with <12m runway | 70 |
| FAIL: 8-K item 4.02 non-reliance (restatement) within 12m | 39 |
| FAIL: exchange financial-status flag E | 2 |
| FAIL: exchange financial-status flag H | 1 |

PASS here means "earns filing-level verification", not "verified". The 142 "lead asset" and 72 "survival" names are routed to
filing checks rather than cut, because code could not confirm a lead asset or a closed financing from the index alone.
Of the 1,723, 1,637 are distinct common-stock issuers; the rest are second lines (preferreds, warrants) of the same issuers.

## Emergent theme clusters (Section 4: discovered from the scan, never an input list)

Method: TF-IDF + NMF (45 topics) over company descriptions of all 1,623 Stage-1 survivors with a description; the label of a
cluster is its own top terms. "Fallen leader" = down ≥ 60% from the 3-year high AND 3-year-high market cap in the cluster's top
quartile. Descriptions are vendor text used as a lead for grouping only. Code: `scripts/r3_themes.py`; members: `batches/cluster_members.csv`.

| Cluster | Top terms (machine-generated label) | Names | Down ≥ 60% | Down ≥ 80% | Median drawdown | Fallen leaders (largest first) |
|---|---|---|---|---|---|---|
| 41 | biopharmaceutical, therapeutics, clinical-stage biopharmaceutical, clinical-stage, unmet, drug, developing | 85 | 72 | 41 | 0.79 | SPRB, VKTX, RXRX, GPCR, MLTX, XFOR |
| 1 | disease, diseases, biotechnology, gene, rare, potential, genetic | 44 | 40 | 22 | 0.80 | ALNY, IONS, INDP, DYN, WGS, NTLA |
| 35 | intelligence, artificial intelligence, artificial, agentic, finance, platform, agentic finance | 39 | 34 | 17 | 0.75 | COIN, MBLY, SKYA, AMKR, ORBS, PL |
| 11 | energy, power, fuel, nuclear, clean, renewable, reliable | 53 | 31 | 15 | 0.71 | OKLO, SMR, FRMI, ENPH, QS, UEC |
| 25 | cancer, phase, patients, clinical, treatment, lead, trial | 32 | 30 | 22 | 0.89 | CBIO, IRLA, NVCR, OLMA, ALT, PALI |
| 44 | media, digital, advertising, news, content, local, marketing | 60 | 28 | 16 | 0.59 | FIG, HUBS, DJT, SOUN, DV |
| 38 | communications, connectivity, wireless, mobile, network, internet, broadband | 44 | 27 | 10 | 0.63 | ORCL, ASTS, CHTR, AAOI, LUMN, AD |
| 33 | cell, autoimmune, autoimmune diseases, diseases, cell therapies, therapies, cell therapy | 28 | 27 | 14 | 0.80 | JBIO, CABA, VOR, NKTR, SANA, CAPR |
| 8 | com, www, information, visit, visit www, information visit, learn | 78 | 26 | 11 | 0.36 | WDC, RDDT, SRPT, SBET, XRAY |
| 32 | manufacturing, semiconductor, aerospace, applications, defense, industrial, design | 48 | 25 | 6 | 0.62 | VELO, TTMI, FPS, AXTI, GPK, ACMR |
| 6 | health, care, wellness, health wellness, better, health care, consumers | 48 | 25 | 12 | 0.60 | ENHA, CELH, HIMS, FIVN |
| 18 | security, defense, national security, space, national, critical, mission | 37 | 24 | 12 | 0.69 | AXON, KTOS, KRMN |
| 24 | systems, power, technologies, control, safety, industrial, leader | 33 | 22 | 7 | 0.68 | SNDK, SMCI, RGTI, QBTS, OLED, NVTS |
| 40 | healthcare, care, patient, improve, clinical, outcomes, providers | 67 | 22 | 5 | 0.43 | DOCS, PRCT, QDEL |
| 30 | steel, metals, processing, production, facilities, producer, metal | 38 | 18 | 7 | 0.57 | MP, USAR, LNZA, AMR |
| 19 | technology, clients, expertise, organizations, helps, deep, outcomes | 38 | 18 | 4 | 0.52 | CRWV, IT |
| 17 | medical, device, medical device, patients, treatment, therapy, fda | 25 | 17 | 9 | 0.74 | ADGM, INSP, ATEC, RXST, ICU, EMBC |
| 9 | infrastructure, data, computing, data centers, compute, centers, digital | 18 | 17 | 9 | 0.79 | IREN, CIFR, AVX, RUM, HOST |
| 12 | value, capital, long-term, disciplined, growth, long-term value, shareholders | 27 | 16 | 10 | 0.63 | MSTR, BMNR, OWL, ASST, XXI |
| 15 | gaming, entertainment, sports, betting, sports betting, experiences, games | 29 | 15 | 7 | 0.63 | ADBE, RBLX, FLUT, DKNG |
| 14 | stores, footwear, apparel, accessories, women, lifestyle, retailer | 51 | 14 | 4 | 0.44 | NKE, LULU, SFM, FND |
| 5 | gas, oil, natural gas, natural, oil natural, production, oil gas | 37 | 12 | 4 | 0.37 | KOS |
| 31 | europe, asia, europe asia, middle east, middle, east, australia | 36 | 12 | 4 | 0.42 | TTD, WLK, GLXY, MOD |
| 27 | automotive, vehicles, parts, vehicle, dealerships, repair, trucks | 39 | 11 | 4 | 0.43 | RKLB, LKQ |
| 3 | properties, trust, investment trust, investment, estate investment, office, office properties | 27 | 11 | 6 | 0.57 | SVC, MPT, HPP, SAFE, AIV |
| 42 | construction, infrastructure, industrial, electrical, maintenance, building, projects | 44 | 10 | 2 | 0.43 | STRL, AGX, LGN |
| 21 | provider, leading provider, management, countries, managed, employees countries, government | 29 | 10 | 3 | 0.45 | CAR, KD, CLVT, VRRM |
| 22 | supply, supply chain, chain, logistics, freight, network, brokerage | 42 | 10 | 6 | 0.35 | FICO |
| 34 | home, furniture, residential, custom, design, furnishings, categories | 50 | 9 | 1 | 0.35 | BLDR, Z, UPST |
| 39 | airlines, air, aircraft, airline, aviation, destinations, scheduled | 26 | 9 | 4 | 0.42 | JOBY, ACHR |
| 2 | estate, real estate, real, commercial real, commercial, investment, mortgage | 25 | 9 | 5 | 0.40 | CSGP, ARE, WD |
| 4 | food, foods, consumer, foodservice, beverages, retail, packaged | 17 | 8 | 3 | 0.50 | FMC, BRBR |
| 43 | outdoor, equipment, recreation, outdoor recreation, enthusiasts, outdoors, outdoor enthusiasts | 36 | 8 | 2 | 0.34 |  |
| 26 | billion, sales, sales billion, net sales, net, employees, fiscal | 46 | 8 | 1 | 0.35 | QXO |
| 23 | stock, exchange, stock exchange, traded, symbol, publicly, traded stock | 28 | 8 | 4 | 0.34 | CNTN |
| 29 | restaurants, restaurant, dining, casual, guests, casual dining, locations | 32 | 7 | 1 | 0.42 | FOUR |
| 36 | education, learning, university, students, programs, learners, higher | 25 | 7 | 3 | 0.50 | DUOL, BFAM |
| 7 | insurance, casualty, property casualty, property, casualty insurance, reinsurance, holding | 42 | 5 | 1 | 0.11 |  |
| 20 | homes, homebuilding, nation, mortgage, largest, nation largest, communities | 16 | 5 | 3 | 0.48 | UWMC |
| 13 | financial, businesses, institutions, financial institutions, money, credit, payments | 30 | 5 | 1 | 0.33 | FISV, CRCL, FIS |
| 37 | water, wastewater, water wastewater, water treatment, treatment, resources, chemical | 22 | 5 | 3 | 0.35 | FUN |
| 28 | owns, limited, logistics, midstream, partnership, crude, transportation | 18 | 5 | 2 | 0.24 |  |
| 10 | bank, banking, management, holding, wealth, wealth management, loan | 19 | 4 | 0 | 0.18 | FLG, LAC |
| 16 | world, countries, world largest, largest, world leading, nyse, innovation | 15 | 3 | 0 | 0.32 | SNAP |

Reading: the damage is concentrated in clinical-stage biotech and in the leaders of the 2023–2025 theme run (AI/compute,
crypto-treasury, nuclear/clean power, space/defence, quantum, connectivity). These are post-wave wreckage, not pre-wave neglect —
the wave-formation analysis has to treat "a second wave" as a different claim from "a first wave".

## Wave atlas — prior cycles measured on prices (Section 5.6 comparables; survivors only, trough-to-peak is an upper envelope)

| Window | Names with ≥ 250 sessions | Rose ≥ 25x trough→peak | ≥ 100x | Median months trough→crest (25x names) | Industries (SIC-3) whose leader basket rose ≥ 10x | Largest |
|---|---|---|---|---|---|---|
| W1_2015-2018 | 2,646 | 11 (0.42%) | 1 | 27.9 | 2 of 72 | CNBX 215x, IGC 93x, CVSI 65x, ACB 61x, GLBS 59x, CGC 50x, MDGL 47x, CDNA 38x |
| W2_2019-2021 | 3,441 | 101 (2.94%) | 11 | 13.6 | 34 of 89 | BRTX 420x, AITX 263x, MARA 190x, FCEL 175x, RTB 166x, ABAT 163x, MVIS 156x, DRIO 149x |
| W3_2022-2026 | 4,321 | 124 (2.87%) | 9 | 24.4 | 30 of 110 | OPTT 162x, AAOI 149x, SEZL 139x, WGS 135x, CVNA 129x, TSSI 124x, AXTI 121x, QBTS 108x |

Trough-to-peak assumes buying the exact low and selling the exact high; it is evidence that waves of this size have formed, and how
long they took, not an achievable return. The cohort's base-date figures in `cohort_report.md` are the achievable-entry measure.

## R3 verification batches — tier 1 (filing-level, ≤ 25 names each)

Order of verification (not a cut): tier 1 = Stage-1 survivors down ≥ 80% from the 3-year high (326) plus fallen leaders down 60–80% (110)
= 436 names in 25 batches grouped by cluster. Tier 2 = the other 299 names down 60–80%. Tier 3 = 902 names that passed the damage scan
only on EV/revenue or small-cap tests (cohort swan rate for < 60% drawdown: 0.23%). A name that is not reached stays unverified and
cannot enter the ranked table; it is not rejected.

| Batch | Names | Clusters |
|---|---|---|
| T1-01 | 24 | 41 |
| T1-02 | 24 | 41 |
| T1-03 | 14 | 1 |
| T1-04 | 14 | 1 |
| T1-05 | 24 | 25 |
| T1-06 | 21 | 35 |
| T1-07 | 18 | 11 |
| T1-08 | 18 | 33 |
| T1-09 | 18 | 44 |
| T1-10 | 17 | 38 |
| T1-11 | 15 | 6 |
| T1-12 | 15 | 18 |
| T1-13 | 14 | 8 |
| T1-14 | 13 | 24 |
| T1-15 | 12 | 9 |
| T1-16 | 12 | 12 |
| T1-17 | 12 | 17 |
| T1-18 | 12 | 32 |
| T1-19 | 11 | 15 |
| T1-20 | 10 | 30 |
| T1-21 | 25 | 2,3,7,14 |
| T1-22 | 25 | 13,22,31,40 |
| T1-23 | 25 | 5,10,19,27,39 |
| T1-24 | 25 | 21,23,28,34,36,42 |
| T1-25 | 18 | -1,4,16,20,26,29,37,43 |

Instructions given to every batch: `batches/BATCH_INSTRUCTIONS.md`. Results: `batches/<batch>.json`, summarised below as they land.

## R3 batches

(appended per batch)
