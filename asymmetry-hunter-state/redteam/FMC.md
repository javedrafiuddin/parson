# FMC (FMC Corp) — red-team memo (R6, as-of 2026-11-10)

Sources: 10-Q filed 2026-10-30 acc 0000037785-26-000171 ("10-Q"); 10-K filed 2026-02-27 acc 0000037785-26-000041 ("10-K");
Schedule 13D filed 2026-09-25 acc 0001140361-26-037699 ("13D"); filing index via tools.py recent (2026-11-10).

## Kill arguments

1. **The franchise just paid its channel to take back inventory; Q3 revenue fell 80%.** Q3 2026 revenue was $105.9M vs $542.2M (−80%); excluding
   India it fell 89%, and organic revenue fell 90%. The 10-Q says the drop was "primarily driven by a 67 percent decrease in connection with the
   commercial actions implemented in Brazil, the United States, Canada and Argentina ... pricing adjustments made on select products held by channel
   customers ... and modification of the pricing and rebate model in North America". Volume fell 21% as "channel customers sharply reduc[ed]
   replenishment orders", and price fell 2% on "competitive pressure in Latin America" (10-Q MD&A). The cash-flow statement carries "Adjustments for
   commercial actions" of $671.6M (9M 2026). This is a pricing reset on a patent-cliff portfolio, not a cyclical dip, and the cause of the 92% drawdown.
2. **The covenants have already been rewritten once, and the test returns now.** The April 2026 Amendment No. 6 suspended the maximum leverage test
   for Q1–Q3 2026. It resumes at 6.75x through 2027-12-31 and steps down to 3.75x by Q1 2029; minimum interest coverage was cut to 2.00x through
   2027-06-30; a new maximum secured leverage of 3.50x and new limits on asset transfers were added. Amendment No. 7 (June 2026) changed the lien limits
   and collateral (10-Q debt note). Testing starts again at Q4 2026, the first full quarter after an $106M-revenue quarter. TTM operating loss is
   $(2,729.5)M (r5 sheet, same 10-Q).
3. **Equity is negative, and claims dwarf the market cap.** Total stockholders' equity is $(19.4)M at 2026-09-30; total debt is $4,177.7M ($213.2M
   short-term + $3,964.5M long-term) vs cash $735.8M (10-Q balance sheet). Net debt is about $3.44B vs market cap about $841M. 9M 2026 cash interest
   paid was $143.5M (10-Q supplemental cash flow). Environmental and discontinued-ops spending of $(25.1)M + $(29.1)M (9M 2026) also ranks ahead of equity.
4. **A strategic buyer marked the shares at $13.30 only weeks ago, and the price has since fallen about 59%.** Tessenderlo Group bought 30,319,166
   new shares at $13.30 in September 2026 (proceeds $403.2M, used to repay revolver borrowings; 10-Q Note 13). It reports 20.0% beneficial ownership
   (13D). The rescue capital came in before the Q3 disclosure. Holders were diluted by about 24%, and the 10-Q bars share repurchases (other than for
   equity-compensation plans) until 2028-12-31.
5. **Cash generation is negative year to date.** 9M 2026 cash from continuing operations was $(231.3)M (10-Q). FY2025 was $(6.2)M (10-K MD&A).
   The table's "TTM $426M" equals −6.2 − 231.3 + 663.3. It is inflated by lapping a −$663.3M 9M 2025 and depends entirely on Q4 seasonal
   collections, and those collections will be smaller after the Q3 channel price resets.
6. **What does NOT kill it (yet).** The company is "in compliance with all covenants at September 30, 2026" (10-Q). No going-concern or
   substantial-doubt language was found, and no exchange offer or default is on file. New debt was raised through Item 2.03 8-Ks (e.g., 2026-10-21
   acc 0001193125-26-427896), so markets are still open to it.

## Ranked-table numbers found wrong or misleading
- "cash-positive (operating cash flow TTM $426M)": continuing operations only, and the result of a base effect. 9M 2026 continuing OCF is −$231.3M,
  FY2025 is −$6.2M, and discontinued operations used a further −$54.2M in 9M 2026. The analyst's own kill trigger, negative FY2026 OCF, needs
  Q4 2026 OCF above about $231M just to avoid it.
- "crop-protection cycle recovery": the filed cause of the collapse is company-specific channel price concessions and a new rebate model, not the cycle.
- The risk column notes the April 2026 covenant amendment, but the kill trigger ("covenant waiver ... disclosed") ignores that a covenant-relief
  amendment suspending the leverage test is already on file.
- Shares: 155.6M includes about 30.3M issued to Tessenderlo in September 2026; any pre-September per-share history is not comparable.

VERDICT: WOUNDED
