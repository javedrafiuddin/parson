# KLC (KinderCare Learning) — red-team memo (R6, as-of 2026-11-10)

Sources: 10-Q for the quarter ended 2026-07-04, filed 2026-08-13, acc 0001193125-26-349480 ("10-Q"); 8-K filed 2026-08-14 acc 0001193125-26-352533
("Lease 8-K"); filing index via tools.py recent (2026-11-10). The Q3 10-Q (quarter ended about 2026-10-03) has not been filed on the mirror yet, so the
latest data is about four months old.

## Kill arguments

1. **The real leverage is leases, not the $926M of debt.** At 2026-07-04: long-term debt $916.1M + current $9.6M; operating lease liabilities
   $162.9M current + $1,421.3M long-term = $1,584.2M; total liabilities $2,937.4M against cash $173.7M (10-Q balance sheet). Cash paid on operating
   leases was $159.7M in 6M 2026 (10-Q supplemental cash flow). Lease-adjusted claims are about $2.51B. That makes lease-adjusted EV about
   $275.6M + $2,510M − $174M ≈ $2.6B. The equity is a thin stub (about 11% of EV) sitting on a fixed-cost rent base.
2. **Why it fell: demand is eroding at the centers.** ECE same-center occupancy was 68.6% vs 71.0% in Q2 (−240 bp) and 67.7% vs 70.0% in 6M,
   "primarily due to lower enrollment". About 70–100 bp of support came only from closing weak centers. Average weekly ECE FTEs fell 4.0% (Q2) and
   3.5% (6M) (10-Q MD&A). Q2 revenue $697.5M vs $700.1M; Q2 operating income $2.4M vs $68.7M (10-Q income statement).
3. **Goodwill was written down, and more write-downs follow mechanically from the share price.** 6M 2026 impairment losses were $314.4M, including
   a $273.5M goodwill impairment of the early-childhood reporting unit. The trigger was "market capitalization deteriorated due to a decline in stock
   price", using a market approach. Accumulated goodwill impairment is $451.5M; $692.4M of goodwill remains (10-Q goodwill note). At $2.33 vs the
   Q1 measurement, another write-down at the Q4 annual test is likely. That is non-cash, but it confirms the market prices the ECE unit below book.
4. **The footprint is shrinking under its largest landlord.** The Lease 8-K (Item 1.01) amends the KCP RE master lease covering 545 centers. As of
   the effective date the lease term ends for the "Schedule 1 Sites", and initial terms run to 2033 (most sites) and 2035 (30 sites). The closures
   help occupancy optics but cut revenue capacity.
5. **Part of last year's profit was a one-off.** Q2 cost of services rose $48.0M (+9.2%), and the 10-Q says the increase "was driven by $30.1
   million of Employee Retention Cre[dit]..." (10-Q MD&A; the excerpt is cut off there). The most likely reading is that the prior-year quarter
   included the credit; this is not verified past the excerpt. TTM operating cash flow of $209.5M (r5 sheet) is therefore not clean run-rate.
6. **Litigation tail.** A personal-injury claim was settled: $44.4M paid, $5.6M still accrued (10-Q, General Liability Claim). No stated exposure on
   other matters was found.
7. **What does NOT kill it.** The first-lien term loan matures June 2030; the revolver ($252.5M extended) matures October 2029 (10-Q debt note).
   The only financial covenant is a springing first-lien net leverage test, and it applies only when revolver draws exceed 35% of commitments. The
   company is "in compliance with the covenants" (10-Q). No going-concern, material-weakness, listing-notice or Item 3.01/4.01/4.02 8-K was found in
   the last 12 months (filing index).

## Ranked-table numbers found wrong or misleading
- "debt $926M vs cash $174M" leaves out $1,584M of operating lease liabilities. For a center operator, rent is senior-like fixed cost.
  Lease-adjusted claims are $2.51B.
- "priced at 1.3x operating cash flow" ($276M / $210M) is arithmetically right, but it is market cap, not EV. TTM OCF also carries one-off
  ERC benefit in the prior-year comparison window.
- Supporting date "Q3 10-Q ~2026-11": not yet on file as of 2026-11-10, so the thesis rests on data from the quarter ended 2026-07-04.

VERDICT: WOUNDED
