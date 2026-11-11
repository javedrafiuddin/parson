# Final report — Operation Asymmetry Hunter v3 (White Swan edition)

Written 2026-11-11; to be confirmed unchanged on Sun Nov 15 (lock) and Mon Nov 16 (buy day).

> "Buying long-term white swans on a one-week analysis sprint means the analysis — not the market — is what this week tests. A multi-year thesis cannot be validated in seven days; nothing that happens to these prices during the week, or for many months after, confirms or refutes the screen. The $800 buys years-long exposure and years-long uncertainty on the strength of arithmetic, historical cohort analogy, and filing-level verification performed under time pressure. Treat the $800 as tuition with a real chance of total loss. Any result — this week or this year — is anecdote, not evidence."

## 1. Verdict: NO TRADE
**NO TRADE: the filter does not beat the base rate enough to make EV positive.** The buy set is empty; the $800 is deployed nowhere.
Arithmetic: `ranked_table.md`. The pre-red-team table (four finalists) is preserved as `ranked_table_R5_pre_redteam.md`.

## 2. Fills
Nothing actuated — there were no tickets. No reconciliation is required; no open discrepancies.

## 3. Cohort validation (8.5) — stated separately
Swan ranking: **FAILED** its benchmarks. No model beat the human rubric at ranking future swans; a fully purged 5-year test was feasible only for the 2020–21
test years, with 3–31 training positives. The elastic-net swan model was retired and base-rate tables used. Wipeout (zero/delisted) model: **PASSED** 4/4 purged
folds against the rubric, random selection and the climatology forecast. Details: `cohort_report.md`.

## 4. Paper shadow book
Opened 2026-11-11 06:34 ET (pre-market quotes, wide spreads; re-mark at the Sun Nov 15 lock) on the ten names that reached full math, notional $100 each,
probabilities locked: VRRM, KLC, ALIT, FMC, RXST, FLNC, METC, TE, ABAT, BLNK. `paper_shadow.csv`, doctrine in `monitoring.md`.

## 5. Finalist and kill history
- R5 (2026-11-10): finalists VRRM, ALIT, KLC, FMC (LIFT 2.5x each, EV +0.29 to +0.35). NO TRADE fired individually for RXST, METC, TE, ABAT, BLNK; FLNC below the white-swan class.
- R6 (2026-11-11): one red-team pass per finalist (`redteam/*.md`), all WOUNDED; every accepted point answered in `redteam/ANSWERS.md` and re-run:
  VRRM 2.2x/+0.20, KLC 2.3x/+0.23, ALIT 1.8x/+0.03, FMC 2.4x/−0.51 → all removed.
- R6 (2026-11-11): 98 further names verified at filing level (VA-01..VA-11): 80 survivor, 10 rejected, 8 could-not-verify; none can reach LIFT 2.5x with a ≥10x ceiling.
- The red team found five ranked-table numbers wrong (VRRM debt structure; ALIT unrestricted cash and EV multiple; KLC leases omitted; FMC operating cash flow and the cause
  of its decline). The verification batches found stale or wrong debt figures in the code-built packs for about a dozen names (IRWD, HPP, SVC, TTEC, RILY, TTGT, NVCR, QDEL, OEC, ASPI…).

## 6. Audit log, could-not-verify
Audit log: `ledger.csv`. Could-not-verify: `could_not_verify.md` plus the COULD_NOT_VERIFY rows in `batches/VA-*.json`.

## 7. Analysis verdict: ANALYSIS FLAWED (in named, bounded ways); the NO-TRADE conclusion is SOUND
The machine did what it was built to do at its gates — screen, verify, red-team, apply the NO-TRADE arithmetic — and it stopped the $800 going into four names whose
filings did not support them. But the analysis has flaws that must be stated plainly:
1. **Code-built fundamentals were unreliable.** Debt, cash and share counts extracted from XBRL were wrong or stale for a material fraction of names (debt shown as $0
   for several heavily indebted companies). The four R5 finalists were selected partly on those numbers; the red team caught it. Any rerun must verify debt and cash
   from the filing before ranking, not after.
2. **Coverage was incomplete.** Of 1,723 Stage-1 survivors, 113 + 98 were read at filing level; 294 first-tier names never reached the math and tiers 2–3 (≈1,200 names) were never
   read. They are logged as unverified, not rejected (`screen_log.md`). The verdict is "nothing in what was examined clears the bar", not "nothing exists".
3. **The swan model could not be validated** (too few historical swans for a purged test), so ranking leaned on base-rate tables and judgement scores (wave 0–5, leader/participant).
4. **No warrant could be assessed**: agreement exhibits were unreadable from this environment (www.sec.gov refused), so the instrument class closest to the QBTS archetype was
   excluded wholesale.
5. **Survivorship in the price data**: dead tickers have no prices, so dead names were valued from public-float filings; the cohort's swan rate is a lower bound.

No claim about edge is made in either direction.

## 8. Hand-off
`monitoring.md` carries the shadow book and the monthly review instruction. The waiver expires Mon Nov 16, 2026 11:59 pm PT, unused.
