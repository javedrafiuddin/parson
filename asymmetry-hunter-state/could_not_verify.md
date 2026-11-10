# Could-Not-Verify list (cumulative)

Every material fact not confirmable from a primary source: the fact, where I looked, which decision it blocks.
Names listed here appear nowhere else in ranked output.

| # | Stage | Name / scope | Fact not verifiable | Where I looked | Decision blocked |
|---|---|---|---|---|---|
| 1 | R1 | all dead/delisted securities | daily price history after delisting or cancellation | Yahoo chart API (purged), Nasdaq API (current only), SEC FTD files (www.sec.gov refused) | exact peak/terminal multiples for dead names in the cohort; handled as subset S2_UNPRICED |
| 2 | R1 | OTC names | OTC Markets tier (Pink / Expert / Caveat Emptor) | otcmarkets.com (maintenance page) | OTC tier check; replaced by SEC current-reporting test + Schwab tradability pre-flight at R6 |
| 3 | R1 | all warrants issued before ~May 2026 | original warrant agreement text (strike, expiry, redemption trigger, cashless table, anti-dilution) | EDGAR full-text search locates the exhibit by accession, but www.sec.gov Archives is refused and the QuoteMedia mirror serves only ~6 months of filings | warrant checklist (5.4): affected warrants cannot be VERIFIED; terms restated in the issuer's latest 10-K are PARTIALLY_VERIFIED only |
| 4 | R2 | NYSE-family listed warrants (60) | 20-day average dollar volume | Yahoo chart API (one row), Nasdaq historical API (no records for .WS symbols) | liquidity floor applied on last-session dollar volume from the Nasdaq quote instead |
| 5 | R2 | 103 universe names flagged `mcap_mismatch` | current share count (exchange-reported cap vs price x as-filed shares differ > 30%) | XBRL cover page vs Nasdaq screener | market cap, EV, runway per share; must be rebuilt from the filing before ranked use |
| 6 | R3 | ANNA (AleAnna) | deSPAC row (5.5): old-vs-new CUSIP confirmation and the closing 8-K | closing 8-K is older than the mirror's ~6-month window; 10-Q/10-K read | excluded from the ranked table (any blank = EXCLUDED); Stage 1 numbers otherwise pass (revenue TTM $39.9M, operating cash flow +$19.8M, no debt) |
| 7 | R3 | BATL (Battalion Oil) | fully diluted share count; whether the 8-K item 4.01 auditor change involved a disagreement | 10-Q filed 2026-08-12 (0001104659-26-094946): $221.2M redeemable convertible preferred at a $6 conversion price vs $43M cap; cover shares 57.3M vs 38.9M six weeks earlier | excluded (5.3: FD count not assemblable = EXCLUDED) |
| 8 | R3 | KLXE (KLX Energy Services) | what the exchange's Form 25-NSE of 2026-09-24 delisted; liquidity beyond $5.0M cash | filing index; 10-Q filed 2026-11-06 (0001738827-26-000069) | excluded pending explanation |
| 9 | R3 | HTZWW (Hertz warrants) and every other listed warrant | warrant agreement terms from the agreement exhibit | agreement exhibits are older than the mirror's window; www.sec.gov refused | warrant checklist cannot be completed → no warrant can enter the ranked table |
| 10 | R3 | 294 first-tier names, tier 2 (299), tier 3 (902) | everything beyond code-computed numbers | not read at filing level (budget) | not eligible for the ranked table; not rejected |
| 11 | R5 | FLNC | contracted backlog figure; exact convertible principal | regex on 10-Q filed 2026-08-05 found the terms but not the figures | did not change the outcome (fails the white-swan class on the plausibility ceiling) |
| 12 | R5 | METC | cover share count | cover tag stale in XBRL; regex found no cover line | share count inferred from market cap ÷ price; name fails on EV regardless |
