# Red-team brief (R6) — your only job is to kill these theses

Work in `/home/user/parson`. Run as-of 2026-11-10. You are independent of the analyst who selected these names; do not try to be balanced.
Four common stocks were selected as "levered, cash-generative fallen leaders priced for failure" that might re-rate ≥ 10x over five years if they
merely survive: **VRRM** (Verra Mobility), **ALIT** (Alight), **KLC** (KinderCare Learning), **FMC** (FMC Corp). The analyst's case and numbers are in
`asymmetry-hunter-state/ranked_table.md`. Find the reason each is in the graveyard to stay.

Rules: public primary data only (SEC filings via the tools below, the price table); no web search, no news, no memory as evidence; cite form, filing
date and accession for every claim; never guess a number; no investment advice; edit nothing except your memo files; no git; at most ~15 tool calls per name.

Tools (read-only):
```
python3 scripts/r5_sheet.py SYM                         # filed balance sheet, TTM flows, filing-index events, text checks
python3 scripts/tools.py recent SYM --months 12         # EDGAR filing index with 8-K item codes
python3 scripts/filing.py list SYM --forms 10-K,10-Q,8-K
python3 scripts/filing.py grep SYM 10-Q 'regex' --ctx 250 --max 6    # also 10-K, or an index number from `list` for an 8-K
python3 scripts/tools.py px SYM --from 2023-11-01       # price path
```
The mirror serves the latest 10-K, the latest 10-Q and about six months of other filings; www.sec.gov is not reachable.

Look specifically for: why the stock fell 92–94% (find the cause in the 10-Q/10-K/8-Ks, do not assume); debt maturities, covenant amendments, waivers,
springing covenants, mandatory prepayments; whether equity is out of the money relative to total claims (debt + preferred + leases + legal accruals);
anchor-customer contract status and renewal dates; going-concern or substantial-doubt language; material weakness, restatement, auditor change,
late filings; pending litigation or regulatory action with stated exposure; impairments and what they imply about the franchise; share issuance,
reverse splits, listing-compliance notices; insider or sponsor behaviour disclosed in filings; anything in the last 60 days of 8-Ks.

Write one memo per name to `asymmetry-hunter-state/redteam/<SYM>.md`: numbered kill arguments, each with its evidence and citation, then a verdict line
`VERDICT: KILL` (a filing-backed reason the equity is very likely worthless or the numbers in the ranked table are materially wrong), `WOUNDED`
(serious, quantified, but not fatal) or `SURVIVES` (you tried and found nothing filing-backed). Also list numbers in the ranked table you found to be wrong.
Reply with at most 12 lines: verdict per name and the single strongest argument for each.

**SAVE AS YOU GO.** Work one name at a time in the order VRRM, ALIT, KLC, FMC and write that name's memo file BEFORE starting the next name. If a memo file already exists for a name, skip that name. A usage limit may stop you at any moment; only what is on disk survives.
