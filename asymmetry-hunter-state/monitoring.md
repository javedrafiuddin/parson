# Monitoring — Operation Asymmetry Hunter v3

No live positions (NO-TRADE verdict). This file carries the paper shadow book forward so the analysis can be judged later.

## Doctrine for the shadow book (fixed at lock)
- Paper entries at the lock ask (2026-11-11 06:34 ET), notional $100 each; probabilities and EV locked in `paper_shadow.csv` and never revised after outcomes are known.
- Each name's dated invalidation (the standing exit trigger on paper):
- **VRRM** — Thesis is dead if FY2027 operating cash flow (10-K due by 2028-03-15) is below $100M, or NYCDOT is no longer a customer by then
- **KLC** — Thesis is dead if FY2027 operating cash flow (10-K due by 2028-03-31) is below $100M or a covenant waiver/default is disclosed before then
- **ALIT** — Thesis is dead if FY2027 revenue (10-K due by 2028-03-15) is below $1.7B or a covenant waiver/default is disclosed before then
- **FMC** — Thesis is dead if a covenant waiver, default or debt exchange is disclosed, or FY2026 operating cash flow (10-K due by 2027-03-01) is negative
- **RXST** — Thesis is dead if cash + short-term investments fall below $150M in any 10-Q/10-K filed by 2028-03-15
- **FLNC** — Thesis is dead if cash falls below $150M or going-concern language appears in any filing through the FY2027 10-K (due by 2027-12-15)
- **METC** — Thesis is dead if no mineral reserve is reported for Brook Mine by 2028-12-31 and FY2027 operating cash flow is negative
- **TE** — Thesis is dead if going-concern language appears or the largest customer is lost by the FY2027 10-K (due by 2028-03-31)
- **ABAT** — Thesis is dead if shares outstanding exceed 285M (2x) by the FY2028 10-K (due by 2028-09-30) or cash falls below 12 months of burn
- **BLNK** — Thesis is dead if FY2026 revenue (10-K due by 2027-03-31) is below $80M or going-concern language appears
- Purpose: in 1, 3 and 5 years, compare what these names did with the probabilities locked here. One winner is survivorship, not evidence.

## Monthly review instruction (paste into any later session)
"Monthly review — Operation Asymmetry Hunter. Read asymmetry-hunter-state/STATE.md, buy_set.md, monitoring.md, and paper_shadow.csv. For each position: check the Section 7.4 standing triggers and the position's dated invalidation against current filings and prices; check any warrant expiry/redemption or LEAPS roll window inside the next 12 months and state the required decision date; update the shadow book (including unbought finalists) at current bid/ask; append every check to ledger.csv. Report only: triggers fired or approaching, decisions required this month with their deadlines, and any doctrine exit that is due — with a ready-to-place ticket if one is. No new positions, no adds, no thesis rewrites in a monthly review."
