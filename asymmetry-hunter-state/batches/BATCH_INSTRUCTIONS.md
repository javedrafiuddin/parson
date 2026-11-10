# Verification batch instructions (R3 — Section 5 screen, Operation Asymmetry Hunter v3)

You are one verification batch in a research run that screens US-listed securities for *long-term white swans*:
names priced for failure today that could plausibly re-rate 25x+ over a multi-year window **if** a theme wave forms
and the company survives and leads it. This stage is ANALYSIS ONLY. Nothing is bought this week.
Your job is filing-level verification of at most 25 names, plus the wave-formation evidence for their theme cluster.
Run as-of date: 2026-11-10. Work from the repository root `/home/user/parson`.

## Hard rules

1. **Public primary data only.** Evidence = SEC filings (read through the tools below), ClinicalTrials.gov, USAspending.gov,
   and the price table. Vendor company descriptions in the packs are LEADS ONLY, never evidence. Do not use web search,
   news, newsletters or your own memory as evidence. If you remember something but cannot find it in a filing, it does
   not count — write it under `could_not_verify`.
2. **Rule V.** Every material number you report carries the form, filing date and accession number it came from.
   Anything you cannot confirm is not estimated: it is listed in `could_not_verify` with where you looked.
3. **Never invent.** No guessed share counts, no assumed financing terms, no "typical" warrant terms. Blank + reason beats a guess.
4. **No advice.** Do not recommend buying or selling anything, and do not produce order tickets.
5. Do not edit any file except your own output file. Do not run git. Do not start background jobs.
6. Be economical: the pack for each name already contains the screen's numbers and regex snippets cut from the latest
   10-Q and 10-K. Read the pack first; use the tools only to fill gaps or resolve doubts.

## Inputs

- Your names: rows of `asymmetry-hunter-state/batches/tier1_batches.csv` (or the batch file named in your prompt) where
  `batch` = your batch id.
- Evidence pack per name: `data/packs/<SYMBOL>.md` (if missing, build it: `python3 scripts/r3_packs.py <csv with a symbol column>`).
- Peers in each emergent theme cluster (damaged or not): `asymmetry-hunter-state/batches/cluster_members.csv`, column `topic`.

## Tools (all read-only)

```
python3 scripts/filing.py list  SYM [--forms 10-K,10-Q,8-K,424B5,DEF 14A]   # filings with accession numbers
python3 scripts/filing.py grep  SYM 10-Q 'regex' [--ctx 250] [--max 8]       # search the latest filing of that form
python3 scripts/filing.py grep  SYM <idx> 'regex'                            # idx from `list` (8-Ks, prospectus supplements, proxies)
python3 scripts/filing.py text  SYM 10-K                                     # caches full text, prints the path (then Grep/Read it)
python3 scripts/tools.py row    SYM                                          # the screen's computed row
python3 scripts/tools.py recent SYM --months 12                              # EDGAR filing index with 8-K item codes
python3 scripts/tools.py px     SYM1,SYM2 --from 2022-06-01 --to 2026-11-09  # trough→peak multiple, dates, months
python3 scripts/tools.py awards "Recipient name" --years 5                   # federal contract awards (USAspending.gov)
python3 scripts/tools.py trials "Company name"                               # registered Phase 2/3 trials (ClinicalTrials.gov)
```

The filing-text mirror serves the latest 10-K, the latest 10-Q and roughly the last six months of other filings.
Older documents (for example original warrant agreements) are NOT readable; say so rather than guessing their terms.
`www.sec.gov` is not reachable from here.

## What to establish for EACH name (Section 5.2 Stage 1, then 5.6)

A. **Identity of the evidence**: latest 10-Q and 10-K — form, filed date, accession, period.
B. **Real business**: TTM revenue ≥ $5M from the financials, OR a verifiable lead asset (registered Phase 2+ trial with NCT id,
   shipped product, or a filed contract with a stated value). Pre-revenue with none of these = REJECTED.
C. **Survival gate** (formula: runway years = (cash − debt and preferred obligations due within 12 months) ÷ trailing-4-quarter
   operating cash burn; positive operating cash flow = "cash-positive"): confirm cash, near-term debt and burn against the
   10-Q. Gate = runway ≥ 12 months, or a filed and CLOSED financing after the balance-sheet date that extends it (an announced
   intention does not count). Quote any going-concern / substantial-doubt language exactly. A company that can only survive
   by serially issuing floating-price converts or equity-line draws fails regardless of the arithmetic.
D. **Dilution**: shares outstanding from the 10-Q cover (number + date); the potentially dilutive securities disclosed
   (options, RSUs, warrants with strike and expiry if stated, convertible notes with conversion price, preferred, earnout
   shares); any at-the-market program (size and remaining capacity) — flag if remaining ATM capacity > 25% of market cap;
   any floating-price / variable-conversion instrument ("toxic") — this is an exclusion flag; any pending authorized-share
   increase or reverse-split proposal.
E. **Reverse-split / listing risk**: price < $1 with a deficiency notice or split proposal — name it.
F. **Fraud red flags** (any ONE = exclusion until resolved in a filing): auditor resignation/dismissal with disagreement;
   going-concern opinion combined with delinquent filings; SEC trading suspension; restatement within 12 months without a clean
   subsequent audit; CEO/CFO departure disclosed alongside an internal investigation.
G. **Cancelled-equity trap** (only for post-bankruptcy or deSPAC lineage): effective date of the plan/combination; whether the
   ticker is the new equity; one line on what one share legally represents today. Any blank = REJECTED for this trap.
H. **Leadership** (only if the name survives A–G): conditional on its theme forming a wave, would the re-rating concentrate here?
   Evidence from filings only: technology/IP position, installed base, named customers and contracts with values, partnerships,
   balance-sheet survivability versus peers in `cluster_members.csv`. Classify `leader` / `participant` / `laggard`.
I. **Shape test**: if, with the theme-wave case removed, the only reason to own the name is a dated binary event inside the next
   ~90 days (a single readout, a single vote, a single ruling), the name is the wrong shape: REJECTED "binary-flip shape, not a white swan".
   Dated catalysts are otherwise logged as supporting facts only.

Give each name exactly one `outcome`:
`SURVIVOR` · `REJECTED: <first failing test and the evidence>` · `COULD_NOT_VERIFY: <what is missing and where you looked>`
and one `flag`: `VERIFIED` (every material number above traced to a filing) / `PARTIALLY_VERIFIED` / `UNVERIFIABLE`.
The pack's XBRL numbers count as traced when you have seen the matching figure or snippet in the filing; say when you have not.

## What to establish for the THEME (once per distinct sub-theme in your batch — Section 5.6)

Split your names into sub-themes yourself from what the filings say they do (clusters are machine-made and coarse).
For each sub-theme with at least one SURVIVOR:
- **Maturity signals** from primary evidence: technology readiness, cost curves, first real revenue across several issuers,
  standards or regulatory frameworks. Cite filings of more than one issuer where you can.
- **Adoption evidence**: named customer contracts in filings, government programs of record (use `tools.py awards`), enterprise
  deployments, revenue mix shifting toward the theme. "Interest is growing" is not evidence.
- **Comparable prior wave**: a historical wave of the same shape, measured with `tools.py px` on real tickers — name it, date
  trough and crest, state the leader basket's peak multiple and months trough-to-crest, and say how today's situation is similar
  AND how it differs. If the same theme already had its wave and these names are its wreckage, say that plainly: a second wave
  is a different claim from a first one. If there is no analogue, say "none".
- **Wave window**: years over which a wave could plausibly form (2–5+).
- A 0–5 `wave_score` (0 = no wave case, 5 = strong multi-source evidence) with one sentence of justification.

## Output

Write ONE JSON file: `asymmetry-hunter-state/batches/<batch id>.json` with this shape (omit nothing; use null + a reason):

```json
{"batch": "T1-07", "as_of": "2026-11-10", "n_names": 18,
 "themes": [{"sub_theme": "...", "members": ["SYM"], "maturity_signals": ["... (FORM, filed YYYY-MM-DD, accession)"],
             "adoption_evidence": ["..."], "comparable_prior_wave": {"name": "...", "trough": "YYYY-MM", "crest": "YYYY-MM",
             "leader_basket": ["SYM"], "leader_peak_multiples": {"SYM": 0.0}, "months_trough_to_crest": 0,
             "similar": "...", "different": "..."}, "wave_window_years": 0, "wave_score": 0, "wave_score_reason": "..."}],
 "names": [{"symbol": "SYM", "cik": 0, "sub_theme": "...", "outcome": "SURVIVOR", "flag": "VERIFIED",
            "latest_10q": {"filed": "YYYY-MM-DD", "accession": "...", "period": "YYYY-MM-DD"},
            "latest_10k": {"filed": "YYYY-MM-DD", "accession": "..."},
            "business": "one sentence from the filing", "revenue_ttm_usd": 0, "lead_asset": null,
            "cash_usd": 0, "debt_total_usd": 0, "debt_due_12m_usd": 0, "ocf_ttm_usd": 0, "runway_years": 0.0,
            "closed_financing_since_bs": null, "going_concern_language": null,
            "shares_outstanding": 0, "shares_asof": "YYYY-MM-DD",
            "dilutive": {"options": null, "rsus": null, "warrants": null, "warrant_terms": null, "convert_shares": null,
                         "convert_terms": null, "preferred": null, "earnout_shares": null},
            "atm": {"exists": false, "remaining_usd": null, "pct_of_mcap": null}, "toxic_instruments": null,
            "pending_auth_increase_or_reverse_split": null, "listing_risk": null, "fraud_flags": null,
            "lineage_trap": null, "leadership": "leader|participant|laggard|n/a", "leadership_evidence": ["..."],
            "dated_catalysts": ["YYYY-MM-DD what (source)"], "binary_flip_shape": false,
            "could_not_verify": ["fact — where you looked"], "notes": "..."}]}
```

Then reply with a summary of at most 12 lines: counts by outcome, the survivors with one clause each, anything alarming,
and anything in the pack numbers that the filings contradicted. Do not paste the JSON into your reply.
