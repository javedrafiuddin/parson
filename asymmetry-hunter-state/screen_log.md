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

## R3 batches

(appended per batch)
