# STATE.md — Operation Asymmetry Hunter v3 (White Swan edition)

**Run as-of:** 2026-11-10 (Tue) · **Current run stage:** R1 in progress (data layer building), R2 started in parallel
**Last updated:** 2026-11-10 ~12:30 UTC

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

- [ ] **R1 — Blueprint + data layer** (Tue Nov 10)
  - [x] state folder created; rules restated; waiver recorded (2026-11-10)
  - [x] source probe done; environment `parson` created with public data hosts (2026-11-10)
  - [x] blueprint.md written (schemas ×4, feature schema, label pseudocode, warrant form, ledger/ticket/buy-set templates)
  - [x] survivorship-free CIK master: 16,594 CIKs from XBRL frames 2009Q2–2026Q3 → `data/derived/frames_cover.parquet`
  - [ ] FILINGS tables: submissions + companyfacts for all master CIKs → `data/pit/` (running: `scripts/r1_pull_facts.py`, resumable)
  - [ ] PRICES table: full daily history for 7,457 listed non-ETF securities → `data/prices/listed/` (running: `scripts/r2_pull_prices.py`, resumable)
  - [ ] DuckDB views + data dictionary check; leakage tests
  - [ ] R1 stage report posted
- [ ] **R2 — Universe build** (Tue Nov 10): field enumerated (13,241 listed securities); floors + damage scan pending the pulls
- [ ] **R3 — Screen** (Wed–Thu)
- [ ] **R4 — Cohort + ML ranking + cross-check** (Thu–Fri)
- [ ] **R5 — White-swan math + finalists** (Fri)
- [ ] **R6 — Finalist deep verification + red team** (Sat)
- [ ] **R7 — Buy set lock (Sun Nov 15), buy day + close-out (Mon Nov 16)**

## Blockers and open issues

- **B1 — `www.sec.gov` refuses this machine** (SEC automated-access policy page; `data.sec.gov` and `efts.sec.gov` work).
  Consequences: (a) no SEC fails-to-deliver price files → no free price history for dead tickers; (b) filing text is
  read through the QuoteMedia mirror that Nasdaq's filing pages link to (works; covers currently listed symbols).
  Possible remedy, user's decision: SEC asks automated clients to declare a contact email in the User-Agent. I will
  not send the user's email to any outside service without his explicit say-so. Asked in session 2026-11-10; no answer yet.
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

1. Wait for `scripts/r1_pull_facts.py` and `scripts/r2_pull_prices.py` to finish (both resumable — just re-run them);
   then build DuckDB views and run the leakage tests; post the R1 stage report.
2. R2: map symbols ↔ CIKs, add SEC-reporting OTC names, apply floors F1–F5 and damage scan D1, write `universe.csv`
   and the coverage ledger in `screen_log.md`; post the R2 stage report.
3. R3: begin hard-filter + survival scoring on the R2 universe in verification batches of ≤ 25; start the cohort build.

## Stage reports (appended)

(none yet)
