# STATE.md — Operation Asymmetry Hunter v3 (White Swan edition)

**Run as-of:** 2026-11-11 (Wed) · **Current run stage:** R6 IN PROGRESS — red team DONE (4 memos + ANSWERS.md): all four finalists now FAIL the NO-TRADE bar; VA verification batches running for possible new finalists
**Last updated:** 2026-11-11 (reset applied; R6 relaunched)

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
- [x] **R3 — Screen** — COMPLETE AS SCALED 2026-11-10 (see `screen_log.md` "R3 as actually run"): Stage 1 code pass 1,930 → 1,723; theme clusters; wave atlas;
  407 evidence packs read in code; funnel L1–L9 → 15 names read at filing level by the main session → 10 into the math. The 25-batch swarm did NOT run
  (pilot hit the 5-hour limit; user reported 50% Fable use). Unreached names are unverified, not rejected.
- [x] **R4 — Cohort + ML ranking + cross-check** — COMPLETE 2026-11-10: `cohort_report.md`; swan ranking FAILED validation (elastic-net retired; base-rate table used);
  wipeout model PASSED 4/4 purged folds (`ah-v3-e679a99d598d`); measured Fermi factors; cross-check recorded in `ranked_table.md`
- [x] **R5 — White-swan math + finalists** — COMPLETE 2026-11-10: `ranked_table.md` (`scripts/r5_math.py`, `scripts/r5_write_table.py`, `data/derived/r5_math.json`, `r5_finalists.json`)
  Finalists: VRRM, ALIT, KLC, FMC (one cluster; effective N ≈ 1.6). NO-TRADE branch fired individually for RXST, METC, TE, ABAT, BLNK; FLNC fails the white-swan class.
- [ ] **R6 — Finalist deep verification + red team** (Sat Nov 14; started early)
  - [x] red-team memos VRRM/ALIT/KLC/FMC written and answered (`redteam/ANSWERS.md`): all WOUNDED; after corrections LIFT 2.2/1.8/2.3/2.4x → NO TRADE for all four
  - [ ] VA-01..VA-11 verification (98 pool names) → any SURVIVOR goes through r5_math + its own red-team pass before the lock. EXACT NEXT ACTION: `ls asymmetry-hunter-state/batches/VA-*.json`; relaunch agents for missing batches
  - [ ] (superseded) red-team memos in `redteam/<SYM>.md` — two earlier agents died at 5-hour walls with nothing written; relaunched 2026-11-11 with memo-by-memo saving.
        EXACT NEXT ACTION if a wall hits: `ls asymmetry-hunter-state/redteam/`; for any of VRRM, ALIT, KLC, FMC without a memo, launch ONE subagent with `redteam/BRIEF.md` for the missing names only; then write `redteam/ANSWERS.md`
  - [ ] every ranked-table number re-traced; dilution trajectory re-modelled; Schwab tradability pre-flight (7.1.1) per name
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

## RESOURCE LEDGER (updated at every stage boundary; last update 2026-11-11, burn-down audit)

| Item | Status |
|---|---|
| (a) 5-hour walls hit | 2026-11-10 ~08:16 ET (cleared 10:40 ET) · 2026-11-10 ~16:20 ET (killed pilot batch T1-14) · 2026-11-10 evening, reset 03:20 UTC Nov 11 (killed the red-team agent). Container clock is unreliable after restarts; wall times are as the user reported or as the API error stated |
| (b) Free Fable limit reset | **USED — applied by the user Wed Nov 11; weekly allowance restored.** (previously: UNUSED (user instruction 2026-11-10: treat as unused; reserved for the weekly-allowance wall, never a 5-hour wall). Announced as binding on 2026-11-11 with the prescribed sentence |
| Weekly allowance | restored by the reset on Wed Nov 11. A red-team agent hit the Fable limit just before the reset (no memos written). Session model switched to Opus 5.5 by the user. Critical path estimated at ~25% of a full allowance |
| (c) Calendar to the lock | Wed Nov 11 → Sat Nov 14 = 4 days, then lock Sun Nov 15, buy day Mon Nov 16 (reset expires Nov 16 11:59 pm PT) |
| (d) Incomplete stages | R6 red team + answers + finalist verification ≈ 9% / 1 window · R7 lock ≈ 7% / 1 window (Sun) · close-out ≈ 5% / 1 window (Mon) · resume overhead ≈ 4% → **≈ 25% still required** |
| Verdict | **ENOUGH** after the reset (~25% needed). Headroom used for ONE optional pass: verification of the 98 pool names in batches VA-01..VA-11 (4 agents), run in parallel with the red team, and dropped first if usage climbs |

Estimated share of the ~84% used so far (estimates, not metered): R1 16 · R2 6 · R3 26 · R4 16 · R5 8 · R6 so far 6 · resumes/audits 6.

**Minimum-viable plan to the lock (critical path, in order):** (1) one red-team pass per finalist — ONE subagent, four memos, each written to disk as it is finished;
(2) answer every kill argument in `redteam/ANSWERS.md`, remove what cannot be defended, re-trace the ranked-table numbers of what remains, Schwab tradability pre-flight;
(3) Sun Nov 15: refresh quotes, re-run `scripts/r5_math.py` + `r5_write_table.py`, write `buy_set.md`, `paper_shadow.csv`, `monitoring.md`; (4) Mon Nov 16: fills, reconciliation, `final_report.md`.

**CUT (first to go, in this order of size):** the reopened first-tier verification swarm (`batches/verify_batches.csv`, 43 batches, 392 names — NOT RUN); tiers 2 and 3;
any re-run of the cohort, models or sweeps; a separate red-team agent per finalist; second verification passes; deeper dives on cut names; warrant / SEC-access work.
**Never cut:** the coverage ledger (every unreached name is logged as unverified, not rejected), one red-team pass per finalist, the NO-TRADE arithmetic, state-saving.

**Cost note:** this session's context is very large, so every step in it is expensive. A FRESH session started with the resume line is cheaper per step and can do
R6/R7 from the repository alone: `data/derived/` is committed (incl. `pit_finalists_*.parquet`); `data/pit` and `data/prices` are NOT needed for R6/R7.

## Token-budget notes (Section 3.3)

- 2026-11-10: session 1 ran R1–R5. The pilot verification agent hit the 5-hour limit (reset 21:20 UTC). User reported Fable use at 50% and asked to scale to resources.
- 2026-11-10 22:35 UTC, said in session: "Weekly Fable allowance nearly exhausted — apply the free Fable limit reset now to refuel the run." (conditional on 50% being the cap
  on included Fable use). Reset status: not confirmed by the user.
- Budget rule from here: no swarms. Main-session code + targeted greps; one red-team subagent for all finalists; keep reserve for the Nov 15 lock and Nov 16 report.

## Funding status / settled-cash tracker (user-reported only)

| Report date/time | Total cash reported | Settled | Unsettled | Reserved vs locked buy set | Free = settled − reserved | Cumulative wires in |
|---|---|---|---|---|---|---|
| — none reported yet — | | | | | | |

## Finalists

| Ticker | Status | Verification | EV per $1 (5y) | LIFT | Proposed allocation (pre-R6) |
|---|---|---|---|---|---|
| VRRM | finalist, pending R6 | VERIFIED (10-Q 0001628280-26-068455) | +0.300 | 2.5x | $400 |
| ALIT | finalist, pending R6 | VERIFIED (10-Q 0001628280-26-069567) | +0.350 | 2.5x | $200 |
| KLC | finalist, pending R6 | VERIFIED (10-Q 0001193125-26-349480; Q3 10-Q due this week — re-read) | +0.293 | 2.5x | $120 |
| FMC | finalist, pending R6 | VERIFIED (10-Q 0000037785-26-000171); covenant amendments April 2026 to be read | +0.293 | 2.5x | $80 |

Kill conditions (7.4) to check at every session until the lock: `python3 scripts/tools.py recent SYM --months 1` for new 8-Ks (items 1.03, 2.04, 3.01, 4.01, 4.02, 5.02);
a going-concern paragraph, covenant waiver, trading suspension or toxic financing removes the finalist.

## Buy-set status

NOT LOCKED.

## Next three actions, in order

1. R6: read `redteam/*.md` when the red-team agent finishes (if absent, launch ONE subagent with the brief in `redteam/BRIEF.md`); answer every kill argument
   line-by-line from filings in `redteam/ANSWERS.md`; remove any finalist whose kill cannot be answered and report it. Re-read KLC's Q3 10-Q when filed.
   Schwab tradability pre-flight (all four are exchange-listed commons above $1: confirm whole-share orderable, no OTC fee).
2. Refresh prices and the filing index (`scripts/r2_pull_prices.py` on a 4-symbol csv; `scripts/tools.py recent`); re-run `scripts/r5_math.py` + `scripts/r5_write_table.py`
   with regular-hours bid/ask in `data/derived/r5_finalists.json`.
3. R7 on Sun Nov 15: lock `buy_set.md` (Section 9 format; allocations sum to exactly $800; PRIMARY largest), open `paper_shadow.csv` on all finalists and the six R5
   rejects, write `monitoring.md`; Mon Nov 16: log fills as reported, reconcile, write `final_report.md`. If funding has not been reported, mark "awaiting funding report".

## Stage reports (appended)

- R1 — complete 2026-11-10. Full text: `stage_reports/R1.md`. Summary: state folder live; blueprint written; survivorship-free master of
  16,594 CIKs; 7.5M filings; 13.6M as-first-filed facts; 22.1M daily price rows; leakage tests pass. Blockers B1–B3 above.
- R2 — complete 2026-11-10. Full text: `stage_reports/R2.md`. Summary: 14,177 securities enumerated → 7,455 in scope → 6,794 with CIK →
  5,444 pass the 10-K+10-Q floor → 5,338 priced → 3,891 liquid → 1,930 priced-for-failure (universe.csv). Rules as written, not tuned to 800–1,500.
- R3 — complete as scaled 2026-11-10. `stage_reports/R3-R5.md`. 1,723 Stage-1 survivors → 407 first-tier packs → 113-name pool → 20 agreed → 15 read → 10 to math.
- R4 — complete 2026-11-10. Swan ranking FAILED validation; wipeout model PASSED 4/4; base-rate tables adopted. `cohort_report.md`.
- R5 — complete 2026-11-10. Four finalists (VRRM, ALIT, KLC, FMC), one cluster, lift at the 2.5x bar, EV +0.29 to +0.35 per $1. `ranked_table.md`.
