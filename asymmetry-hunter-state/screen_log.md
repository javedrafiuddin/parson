# Screen log and coverage ledger

Rule: a narrowing step that is not in this ledger did not happen; a name cut without a logged reason is restored.

## Coverage ledger

| # | Step | Names in | Names out | Cut | Rule / evidence |
|---|---|---|---|---|---|
| F0 | Field enumeration: every non-test security in Nasdaq Trader `nasdaqlisted.txt` + `otherlisted.txt` (file stamp 2026-11-10 03:02) | — | 13,241 | — | exchange symbol directory; full list in `data/derived/field_listed_all.csv` |
