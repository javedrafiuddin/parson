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
