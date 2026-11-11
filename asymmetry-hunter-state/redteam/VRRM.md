# VRRM (Verra Mobility) — red-team memo (R6)

As-of 2026-11-10. Sources: 10-Q filed 2026-10-30, acc 0001628280-26-068455 ("10-Q"); 10-K filed 2026-02-24, acc 0001193125-26-067293 ("10-K");
EDGAR index via `tools.py recent`; price via `tools.py px`. No 8-K body was opened (index 0 resolved to the S-8), so 8-K content is cited only
as restated in the 10-Q.

## Kill arguments

1. **The anchor-customer loss the table treats as a risk has already happened.** 10-Q (risk-factor summary and Note 15, Subsequent Events): one of
   three significant Commercial Services customers issued a termination notice in May 2026, withdrew it in July 2026 and signed a seven-year
   extension "on terms that were materially less favorable to us", including an option to modulate fleet volume; in Q3 2026 it "significantly
   reduced its fleet volume" and on 2026-10-02 the Company itself exercised its option to terminate, effective 2027-01-30. "We may be unable to
   replace the revenue ... on a timely basis or at all." The ranked-table bear case still says this customer "gave, then withdrew" its notice.

2. **The other two anchors are repriced or in play.** Same 10-Q passage: a second significant customer signed a five-year extension "also on terms
   materially less favorable to us ... with fleet volume modulation rights" (the same right that preceded customer one's exit); the third
   contract "is approaching renewal, and we are following the customer's procurement process. We may not be successful in retaining the contract".
   The 10-K names the three largest U.S. rental-car companies as the long-standing relationships and says toll management was ~39% of 2025 revenue.

3. **The segment being repriced is the profit engine, so TTM cash flow overstates the forward run-rate.** 10-Q Note 14: Q3 2026 segment profit was
   Commercial Services $61.3M, Government Solutions $39.1M, Parking $3.5M (total $103.9M) — Commercial Services is 59% of segment profit on 39% of
   revenue. A year earlier it was $78.3M of $113.3M. Commercial Services service revenue fell 14.5% y/y in Q3 ($117.3M to $100.3M), of which
   $16.1M was rental-car tolling, attributed to the two less-favourable extensions, fleet-volume fluctuation and lower travel demand. That is
   before the 2027-01-30 termination takes effect. The table's "operating cash flow TTM $252M" and survival score 78/100 are computed on the
   pre-loss book; TTM capex is $114.4M (r5 sheet), so the cushion after capex is roughly half the headline figure.

4. **Growth is concentrating into one lower-margin government customer on harder terms.** 10-Q: NYCDOT was 24.1% of Q3 2026 revenue (19.5% a year
   earlier); the new five-year NYCDOT contract effective 2026-01-01 has "materially different" terms "including service level agreements, service
   credits, liquidated damages"; Q3 growth there was "installation revenue on new camera installations, net of pricing changes under the new
   contract"; $55.6M of NYCDOT revenue was unbilled at 2026-09-30. Government Solutions segment margin is 28.6% (39.1/136.8) vs 61.1% for
   Commercial Services (61.3/100.3), so a dollar of mix shift replaces less than half the profit.

5. **Debt is mis-described in the table and the first maturity is inside the five-year window.** 10-Q Note (Debt): the Amended Term Loan is
   ~$688.8M maturing 2032-10-15 (SOFR + 2.00%, 5.9% at quarter-end), plus $350.0M of 5.50% Senior Unsecured Notes due **2029-04-15**; total debt
   $1,032.6M against cash $137.0M. The table says "$1.03B term loan (2032)". The term loan also carries an excess-cash-flow sweep of 50% when
   first-lien net leverage exceeds 3.70x and 25% above 3.20x, so falling EBITDA diverts cash to lenders. The Company states it was in compliance
   with all covenants at 2026-09-30 and there is no going-concern or material-weakness language in the 10-Q — I found no covenant breach.

6. **Franchise impairment and a full leadership turnover.** 10-Q: $64.0M goodwill impairment (Parking Solutions) and $40.4M intangible impairment
   in the nine months to 2026-09-30; nine-month net income $19.0M vs $117.8M. CEO David Roberts "departed" 2026-06-01; interim CEO; new CEO
   effective 2026-11-01; CFO resigned effective 2026-11-04; interim CFO is a Managing Director of Alvarez & Marsal engaged through that firm
   (effective 2026-11-05). Seven Item 5.02 8-Ks in twelve months. (Reading the A&M engagement as restructuring preparation is my inference; the
   filing says only that he serves until a permanent CFO is appointed.)

7. **Securities class action on exactly this issue.** 10-Q Note (Commitments and Contingencies): *Otucu v. Verra Mobility*, D. Ariz., filed
   2026-06-04, class period 2026-02-24 to 2026-05-26, alleging defendants misled investors about "contract renewal negotiations with a Commercial
   S[ervices customer]"; damages unspecified, no accrual stated.

8. **The ≥10x path needs more than survival.** Close was $18.94 on 2026-02-20, with all three rental-car contracts on the old terms (px table).
   10x from $2.13 is $21.30 and the 18.7x cap is ~$39.90, above the 3-year high of $30.84 (r5 sheet). The upside rows require the equity to be
   worth more than it was before the franchise was repriced, with one anchor gone.

## Why it fell (found, not assumed)
The class period in item 7 ends 2026-05-26, the date of an Item 7.01/8.01 8-K (acc 0001193125-26-239351); the 10-Q dates the termination notice to
May 2026. The collapse is a repricing of the rental-car tolling contracts, not a balance-sheet event.

## Ranked-table numbers or statements found wrong
- "$1.03B term loan (2032)": actually ~$688.8M term loan due 2032-10-15 plus $350.0M senior notes due 2029-04-15.
- Bear case describes the first customer's exit as a possibility; the 10-Q reports the contract terminated effective 2027-01-30.
- "Cash $140M" is cash plus restricted cash ($140.1M); unrestricted cash is $137.0M. Share count, debt total, OCF TTM and NYCDOT 24.1% check out.

## What I did not find
No going-concern language, covenant waiver, amendment, listing notice, restatement or equity issuance. Equity is not shown to be out of the money.

VERDICT: WOUNDED
