# Could-Not-Verify list (cumulative)

Every material fact not confirmable from a primary source: the fact, where I looked, which decision it blocks.
Names listed here appear nowhere else in ranked output.

| # | Stage | Name / scope | Fact not verifiable | Where I looked | Decision blocked |
|---|---|---|---|---|---|
| 1 | R1 | all dead/delisted securities | daily price history after delisting or cancellation | Yahoo chart API (purged), Nasdaq API (current only), SEC FTD files (www.sec.gov refused) | exact peak/terminal multiples for dead names in the cohort; handled as subset S2_UNPRICED |
| 2 | R1 | OTC names | OTC Markets tier (Pink / Expert / Caveat Emptor) | otcmarkets.com (maintenance page) | OTC tier check; replaced by SEC current-reporting test + Schwab tradability pre-flight at R6 |
