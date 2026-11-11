# ALIT (Alight) — red-team memo (R6, as-of 2026-11-10)

Sources: 10-Q filed 2026-11-03 acc 0001628280-26-069567 ("10-Q"); 8-K filed 2026-11-03 acc 0001628280-26-069535 ("Q3 8-K");
8-K filed 2026-10-14 acc 0001628280-26-065893 ("Cleansing 8-K"); filing index via tools.py recent (2026-11-10).

## Kill arguments

1. **The entire capital structure matures 2028-08-31 and a lender negotiation just failed.** Debt is a single Seventh Incremental
   Term Loan, $1,991M, maturity August 31, 2028; the $330M revolver (undrawn) runs to May 31, 2030 (10-Q, Note 8 Debt).
   The Cleansing 8-K (Item 7.01) says Alight "has been engaged in confidential discussions with certain lenders ... and their financial
   and legal advisers regarding potential refinancing and/or extension", "a definitive agreement with terms that are satisfactory to Alight
   has not yet been reached, and at this time the Company has elected not to actively pursue a Potential Transaction", and it published
   lender projections ("Cleansing Materials") under confidentiality agreements. Lenders with their own financial advisers plus a failed
   talk is how a negotiated restructuring is usually staged. The 10-Q also books "$6 million of certain professional fees incurred in
   connection with our debt refinancing activities" (Q3 and 9M 2026). The FY2027 10-K (filed ~Feb 2028) will be prepared with the
   whole term loan due within 12 months, so the going-concern test bites then unless refinanced.
2. **The franchise is shrinking and management says it will keep shrinking.** Q3 2026 revenue $500M vs $533M (-6.2%), "driven by lower
   Net Commercial Activity ... the impact from prior year client losses and lower bookings ... expected to continue to impact revenue growth
   during the remainder of fiscal year 2026 and fiscal year 2027" (10-Q MD&A). Q3 gross profit $135M vs $178M (-24%). Q3 continuing
   operating loss $(61)M with no impairment in the quarter. FY2026 outlook: revenue $2,115–2,125M, Adjusted EBITDA $410–420M (Q3 8-K).
3. **Why it fell: goodwill write-downs confirm the franchise impairment.** Goodwill impairment $1,338M in Q3 2025 and $2,321M in 9M 2025
   (10-Q income statement); goodwill is now $83M on $4,194M of assets (r5 sheet, same 10-Q). A 1-for-20 reverse split took effect
   2026-06-30 (10-Q) after an Item 3.01 listing notice (8-K 2026-03-27 acc 0001628280-26-021571).
4. **Interest cost steps up as hedges roll off in December 2026.** Swaps fixing the term loan at 2.554% ($596M notional) and 3.9025%
   ($125M, plus another $150M tranche) all expire December 2026 (10-Q, Interest Rate Swaps table); after that the loan floats at SOFR + margin
   (the Sixth Incremental tranche was repriced to SOFR + 1.75%; 10-Q Note 8), and a refinancing in today's conditions would likely cost more.
5. **Junior claims ahead of equity: TRA.** TRA liability $448M at 2026-09-30 (current $20M, long-term $428M); $136M paid in 2026. The TRA
   Party Representative disputes that and claims about $65M more plus interest ("October 2026 Communication"); the company is contesting it
   (10-Q Note 15). Claims ahead of common equity: $1,991M debt + $448M TRA + leases (operating $61M, finance $20M current + more) ≈ $2.5B+
   against $212M unrestricted cash.
6. **Equity is not out of the money today.** Enterprise value is about $336M market cap + $1,991M + $448M TRA − $212M ≈ $2.56B, about 6.1x the
   midpoint of FY2026 Adjusted EBITDA guidance; gross debt is about 4.8x. YTD free cash flow is $108M (Q3 8-K). No going-concern, substantial-doubt
   or material-weakness language found in the 10-Q; no covenant default disclosed; the company raised its 2026 outlook (Q3 8-K headline).

## Ranked-table numbers found wrong or misleading
- "debt $1,991M vs cash $448M": $448M is cash *including restricted cash*. Unrestricted cash is $212M (10-Q; Q3 8-K: "total debt net of cash
  and cash equivalents was $1,779 million"). $448M is also, coincidentally, the TRA liability.
- "~1.1x operating cash flow" is market cap/OCF; it ignores $1.78B net debt and the $448M TRA. EV/TTM OCF is about 8.4x.
- The kill trigger ("FY2027 revenue < $1.7B or covenant waiver/default") misses the binding event: the 2028-08-31 maturity of all funded debt,
  and an amend-and-extend or exchange that could dilute or prime equity well before revenue gets anywhere near $1.7B.
- Quote source says "Nasdaq quote API"; the 10-Q cover lists ALIT on the NYSE (10-Q cover). The venue is wrong, though the quote may still be usable.

VERDICT: WOUNDED
