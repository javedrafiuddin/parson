# STATE.md — Operation Asymmetry Hunter v3 (White Swan edition)

**Run as-of:** 2026-11-10 (Tue) · **Current run stage:** R3 in progress (Stage 1 code pass done; verification batches next) · R4 cohort + models DONE early
**Last updated:** 2026-11-10 ~17:15 UTC

> FIRST ACTION OF EVERY SESSION: read this file and every file it indexes, state in two lines where the run
> stands, continue at the next incomplete stage. Never redo a completed stage except to correct a logged error.

## Resume instruction (paste into a fresh session)

"Resume Operation Asymmetry Hunter. Read asymmetry-hunter-state/STATE.md and every file it indexes, tell me in two lines where the run stands, then continue autonomously at the next incomplete run stage. Do not restart completed stages."

The full governing prompt is saved at `asymmetry-hunter-state/PROMPT_v3.md`.

## Section 0 rules, restated in my own words (I operate under all nine; they override anything later)

1. **No credentials, no account access, no orders.** I never ask for, accept, or store logins, tokens, account
   numbers or tax IDs, and I never place or pre-fill an order. My output ends at ready-to-place tickets in the
   Nov 16 buy set; the user clicks at Schwab himself and reports fills. Actuation is mechanical, not a re-approval.
2. **Funding is one-way and user-reported.** The user wires money to his own Schwab account and tells me the settled
   amount once, in writing. I size only against that reported settled cash; I never estimate or fetch a balance.
3. **The waiver is narrow.** For this $800 test only, paper-until-proven and per-trade thesis approval are waived,
   expiring Mon Nov 16, 2026 11:59 pm PT. Nothing larger, later, or in another account is covered. In exchange I must
   run the compressed validation: historical cohort with purged walk-forward, plus a paper shadow book on every
   finalist. The $800 may only go out as the single Nov 16 buy set, after R3–R6 and the per-name tradability check.
4. **The cost of the waiver is stated honestly** — the verbatim paragraph is below and goes in the first and final reports.
5. **Max loss is the stake.** $800, assumed fully losable; allocations sum to exactly $800; every position can go to
   zero. No margin, no naked shorts, no uncovered options, no averaging down. A finalist that trips a kill condition
   during the week is removed and reported without waiting to be told.
6. **No live tickets before Nov 16.** The week is analysis only. No early buys, no "price looks good today".
7. **Public primary data only.** Every material fact traces to a primary public source; what I cannot verify is
   excluded, not estimated.
8. **Honesty outranks helpfulness.** If the math says NO TRADE, the buy set is empty and the report leads with that.
   No manufactured optimism, no quota-filling, no softening because time or budget is short.
9. **State is written, not remembered.** No stage is complete until its outputs are on disk here and this file is
   updated, so any fresh session can resume from the files alone.

**Rule 4 paragraph (verbatim):** "Buying long-term white swans on a one-week analysis sprint means the analysis — not the market — is what this week tests. A multi-year thesis cannot be validated in seven days; nothing that happens to these prices during the week, or for many months after, confirms or refutes the screen. The $800 buys years-long exposure and years-long uncertainty on the strength of arithmetic, historical cohort analogy, and filing-level verification performed under time pressure. Treat the $800 as tuition with a real chance of total loss. Any result — this week or this year — is anecdote, not evidence."

**Waiver record:** scope = $800 test stake maximum, this test only; expires Mon Nov 16, 2026 11:59 pm PT.

## File index

| File | Purpose | Status |
|---|---|---|
| `PROMPT_v3.md` | the governing prompt, verbatim | written |
| `blueprint.md` | R1 buildable specifications (schemas, features, labels, forms, templates) | written |
| `universe.csv` | R2 list | pending |
| `screen_log.md` | coverage ledger + per-batch screen results | started (R2 ledger) |
| `cohort_report.md` | Section 8 cohort construction | pending (R3/R4) |
| `ranked_table.md` | R5 table or NO-TRADE verdict | pending |
| `ledger.csv` | audit log, every 7.5 field | header + stage events |
| `paper_shadow.csv` | shadow/monitoring book | header only (opens at R7 lock) |
| `buy_set.md` | locked Nov 16 buy set | NOT LOCKED |
| `could_not_verify.md` | cumulative could-not-verify list | started |
| `monitoring.md` | per-name doctrine + monthly review instruction | pending (R7) |
| `final_report.md` | final report | pending (R7) |
| `stage_reports/` | stage reports as posted | R1 pending |

Code: `ah/` (package), `scripts/` (stage runners), `tests/` (leakage tests). Data: `data/derived/` (committed, compact),
`data/raw|pit|prices/` (gitignored; rebuild with the scripts below).

## Per-stage checklist

- [x] **R1 — Blueprint + data layer** (Tue Nov 10) — COMPLETE 2026-11-10 ~12:15 UTC
  - [x] state folder created; rules restated; waiver recorded (2026-11-10)
  - [x] source probe done; environment `parson` created with public data hosts (2026-11-10)
  - [x] blueprint.md written (schemas ×4, feature schema, label pseudocode, warrant form, ledger/ticket/buy-set templates)
  - [x] survivorship-free CIK master: 16,594 CIKs from XBRL frames 2009Q2–2026Q3 → `data/derived/frames_cover.parquet`
  - [x] FILINGS tables: 16,594 entities, 7,530,896 filings, 13,601,520 as-first-filed facts → `data/pit/` (rebuild: `scripts/r1_pull_facts.py`, ~70 min)
  - [x] PRICES: 7,454 listed symbols (22.1M rows to 2026-11-09), 361 Nasdaq warrants, 616 OTC → `data/prices/` (rebuild: `scripts/r2_pull_prices.py`, `r2_pull_nasdaq_hist.py`, ~45 min)
  - [x] DuckDB views (`ah/store.py`), PIT series (`ah/pit.py`), 6 leakage tests pass (`tests/test_leakage.py`)
  - [x] R1 stage report posted (`stage_reports/R1.md`)
- [x] **R2 — Universe build** (Tue Nov 10) — COMPLETE 2026-11-10 ~12:25 UTC: 14,177 enumerated → 1,930 in `universe.csv` (1,836 issuers); ledger F0–D1 in `screen_log.md`; report `stage_reports/R2.md`
- [ ] **R3 — Screen** (Wed–Thu) — STARTED early 2026-11-10
  - [x] Stage 1 code pass (`scripts/r3_stage1.py` → `data/derived/stage1.parquet`): 1,930 → 1,723 continue (1,509 PASS; 142 need lead-asset check; 72 need survival check); 207 FAIL logged
  - [x] company descriptions pulled for theme discovery (`data/derived/profiles.parquet`, 1,623 of 1,637 issuers; vendor text = lead only)
  - [ ] emergent theme clusters + fallen leaders written to `screen_log.md`
  - [ ] filing-level verification batches (≤ 25 names, subagents) in rank order → `asymmetry-hunter-state/batches/`
  - [ ] wave-formation evidence per surviving theme; vehicle choice; INSTRUMENT TERMS for surviving warrants
- [ ] **R4 — Cohort + ML ranking + cross-check** (Thu–Fri)
  - [x] cohort built (`scripts/r4_build_cohort.py`): 58,644 matured bases, 363 swan name-dates / 121 CIKs, 5,268 graveyard; `cohort_report.md` WRITTEN
  - [x] pre-flight count + validation (`scripts/r4_model.py`, `r4_baserate_model.py`): swan ranking FAILED benchmarks → elastic-net swan model RETIRED, base-rate table used; wipeout model PASSED 4/4 purged folds (model version `ah-v3-e679a99d598d`)
  - [x] measured Fermi factors (`scripts/r4_wave_rates.py` → `wave_rates.json`): survival 0.655, wave 0.0252, leads 0.393, captures 0.604 → 1-in-255 for a ≥25x peak
  - [x] today's field scored: `data/derived/baserate_scores.parquet` (P(swan) table + sweep range + P(zero))
  - [ ] blind human–model cross-check (8.7) on verified survivors
- [ ] **R5 — White-swan math + finalists** (Fri)
- [ ] **R6 — Finalist deep verification + red team** (Sat)
- [ ] **R7 — Buy set lock (Sun Nov 15), buy day + close-out (Mon Nov 16)**

## Blockers and open issues

- **B1 — `www.sec.gov` refuses this machine** (SEC automated-access policy page; `data.sec.gov` and `efts.sec.gov` work).
  Consequences: (a) no SEC fails-to-deliver price files → no free price history for dead tickers; (b) filing text is
  read through the QuoteMedia mirror that Nasdaq's filing pages link to (works; covers currently listed symbols).
  Possible remedy, user's decision: SEC asks automated clients to declare a contact email in the User-Agent. I will
  not send the user's email to any outside service without his explicit say-so. Asked in session 2026-11-10; no answer yet.
  The mirror serves only the latest 10-K, latest 10-Q and ~6 months of other filings: original warrant-agreement exhibits from earlier
  years are NOT readable → affected warrants go to Could-Not-Verify (PARTIALLY_VERIFIED), never the ranked table, unless B1 is lifted.
- **B2 — OTC Markets site returns a maintenance page.** OTC discovery uses the EDGAR `exchanges` field instead.
- **B3 — Yahoo purges most delisted tickers** (tested: 20 of 25 known-dead tickers return nothing). Handled in the
  cohort design as the `S2_UNPRICED` subset; documented in `blueprint.md` §8.2.

## Token-budget notes (Section 3.3)

- 2026-11-10: session 1 running. Reset not yet used. No allowance warning issued yet.

## Funding status / settled-cash tracker (user-reported only)

| Report date/time | Total cash reported | Settled | Unsettled | Reserved vs locked buy set | Free = settled − reserved | Cumulative wires in |
|---|---|---|---|---|---|---|
| — none reported yet — | | | | | | |

## Finalists

None yet (R5).

## Buy-set status

NOT LOCKED.

## Next three actions, in order

1. If `data/pit` or `data/prices` are missing (fresh container): rebuild with `python3 scripts/r1_secmaster_frames.py && python3 scripts/r1_pull_facts.py`,
   then `python3 scripts/r2_pull_prices.py data/tmp/syms_listed.csv listed` (see README), then `python3 scripts/r2_build_universe.py map` / `scan`.
2. R3: read `data/derived/stage1.parquet` (Stage 1 outcomes); cluster survivors by theme; run filing-level verification batches of ≤ 25
   (subagents, `scripts/filing.py` is their reader); append each batch to `screen_log.md`; write INSTRUMENT TERMS for surviving warrants.
3. R4: read `data/derived/cohort_counts.json`; write `cohort_report.md`; run the pre-flight class count and the model or its mandated degradation.

## Stage reports (appended)

- R1 — complete 2026-11-10. Full text: `stage_reports/R1.md`. Summary: state folder live; blueprint written; survivorship-free master of
  16,594 CIKs; 7.5M filings; 13.6M as-first-filed facts; 22.1M daily price rows; leakage tests pass. Blockers B1–B3 above.
- R2 — complete 2026-11-10. Full text: `stage_reports/R2.md`. Summary: 14,177 securities enumerated → 7,455 in scope → 6,794 with CIK →
  5,444 pass the 10-K+10-Q floor → 5,338 priced → 3,891 liquid → 1,930 priced-for-failure (universe.csv). Rules as written, not tuned to 800–1,500.
