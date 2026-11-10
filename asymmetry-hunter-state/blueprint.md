# Operation Asymmetry Hunter v3 — R1 Blueprint (buildable specifications)

As-of: 2026-11-10 (Tue). No candidate names appear in this document.
Code lives in `ah/` (package) and `scripts/` (stage runners). State lives in `asymmetry-hunter-state/`.

## 0. Environment facts that shape the build (measured 2026-11-10, not assumed)

| Source | Status in this environment | Used for |
|---|---|---|
| `data.sec.gov` submissions API | reachable | entity master, filing index with EDGAR **accepted** timestamps, 8-K item codes |
| `data.sec.gov` XBRL companyfacts | reachable | every reported value of ~110 concepts with accession + filed date (as-first-filed versions kept) |
| `data.sec.gov` XBRL frames | reachable | survivorship-free CIK master 2009Q2–2026Q3 (16,594 CIKs) |
| `efts.sec.gov` full-text search | reachable | locating exhibits (EX-4.x warrant agreements, indentures) by accession; hit metadata only |
| `www.sec.gov` (Archives, FTD files, ticker files) | **REFUSED by SEC's automated-access policy for this machine** | — (blocker B1) |
| Nasdaq Trader symbol directory | reachable | full listed field (13,241 non-test securities) |
| `api.nasdaq.com` | reachable | screener, real-time bid/ask, 10y history, option chains, short interest, filing list |
| `app.quotemedia.com` (via Nasdaq filing links) | reachable | **filing text** (10-K/10-Q/8-K/S-1 with exhibits) — substitute for www.sec.gov Archives |
| Yahoo chart API | reachable | daily OHLCV + splits for currently quoted symbols; **purges most dead tickers** |
| FINRA Reg SHO daily short volume | reachable 2020+ | short volume |
| ClinicalTrials.gov v2 API, USAspending API | reachable | trial registry, federal awards |
| OTC Markets site | returns a maintenance page | — (OTC discovery done through EDGAR `exchanges` field instead) |
| Stooq | connection dropped | — |

**Blocker B1 and its consequence, stated up front:** with `www.sec.gov` refused, there is no free
survivorship-free *price* source (the SEC fails-to-deliver files, which carry closing prices for dead names,
live there). Prices therefore exist only for securities still quoted today. The cohort design in §8 is built
around that gap rather than pretending it away: dead names are kept in the population through EDGAR
(XBRL public float, share counts, terminal filing events), and are a labelled subset (`S2_UNPRICED`).

## 4. Universe specification (R2)

Field enumeration (list-building mechanics, no theme input anywhere):

1. `LISTED`: every non-test row of `nasdaqlisted.txt` + `otherlisted.txt` (Nasdaq Trader). Security type is
   parsed from the exchange's own security description: common / adr / warrant / unit / right /
   convertible_or_preferred / note / fund_or_etn / other. ETFs carry the file's ETF flag.
2. `OTC_SEC`: every CIK in the EDGAR master whose `exchanges` field lists OTC and which filed a 10-K **and**
   a 10-Q in the trailing 12 months (submissions index). Pink/no-information/delinquent = excluded outright.
3. Cross-cutting tags derived from filings, not from any hand list: `SPAC` (trust assets tagged in XBRL, SIC 6770),
   `deSPAC` (former SIC 6770 / former name pattern + 8-K item 2.01), `post-bankruptcy` (8-K item 1.03 within 36
   months), `biotech-platform` (SIC 2833–2836, 8731 + ≥1 registered Phase 2/3 trial).
4. LEAPS are an overlay evaluated only for common-stock survivors (chain must exist at `api.nasdaq.com`).

Minimal floors (each is a coverage-ledger step with names in / out / cut / rule):

| Step | Rule | Evidence |
|---|---|---|
| F0 | field enumerated | symbol files + EDGAR master |
| F1 | instrument in scope: common, adr, warrant, convertible_or_preferred (drop ETFs, funds/ETNs, units, rights, straight notes) | exchange security description |
| F2 | maps to an EDGAR CIK | submissions `tickers` |
| F3 | filing floor: 10-K and 10-Q both filed within trailing 12 months (the prompt's stated floor; 20-F/40-F-only issuers fail it and are logged as such) | submissions index |
| F4 | price exists: ≥ 60 trading days of history and a quote in the last 10 sessions | Yahoo / Nasdaq |
| F5 | liquidity floor: 20-day ADV$ ≥ $250k common, ≥ $50k warrants/preferreds | computed |
| D1 | cheap damage scan (Section 5.2 priced-for-failure, any one of three) on every F5 survivor | prices + XBRL |

Names passing D1 are the R2 universe written to `universe.csv` (target 800–1,500; the actual count is whatever
the rules produce and is reported, not tuned). Only D1 survivors earn filing-level verification in R3.

## 5. Screen specification (R3) — formulas exactly as Section 5.1

```
drawdown        = 1 - last_close / max(split_adjusted_close over trailing 3 years)
fd_shares       = cover shares + options + RSUs + warrants + convert shares + preferred conversions
                  + earnouts + remaining ATM capacity / price          (all issuable at the TARGET price; no TSM)
EV              = price * fd_shares + total_debt + preferred_liquidation_value - cash
runway_years    = (cash - debt_and_preferred_due_within_12m) / TTM_operating_cash_burn      ("cash-positive" if TTM OCF > 0)
spread_pct      = (ask - bid) / ((ask + bid) / 2)
wave_window     = default 5y, argued per name, never < 2y
durability      = years until expiry / redemption / call / maturity   (common: indefinite | survival)
```

Stage 1 hard filters (order of evaluation; first failure is logged as the reason):
priced-for-failure → real business (TTM revenue ≥ $5M or verifiable lead asset) → survival gate (runway ≥ 12 months or
closed financing) → toxic-financing test → fd-share count assemblable → liquidity → fraud red flags.

Survival score (0–100, first-class factor): runway years (0–35) + financing access (0–20) + dilution trajectory (0–25)
+ floor value (0–20). Dilution trajectory: projected share count at years 1/3/5 under TTM burn funded by equity at
three price paths (flat, 3x, 10x): `shares_y = shares_0 + Σ_t burn_t / price_path_t` plus option-pool refresh at the
historical rate. Section 6 payoffs use the year-appropriate count.

Batch discipline: filing-level verification in batches of ≤ 25 names, one subagent per batch, many batches in
parallel; each batch writes survivors / rejections / unverifiables to `screen_log.md` before the next begins.
Every candidate row carries: accession number, filing date, price + source + as-of, and VERIFIED /
PARTIALLY_VERIFIED / UNVERIFIABLE.

### Warrant checklist (reusable form — any unconfirmed item = EXCLUDED)

```
WARRANT CHECKLIST            ticker: ________   underlying: ________   CIK: ________
Source exhibit (form / exhibit no. / accession / filing date): ______________________________
[ ] 1 Underlying security and exercise price (strike): $______ per share; shares per warrant: ____
[ ] 2 Expiry date: ____-__-__   (years remaining: ____ ; must cover first 3 years of wave window)
[ ] 3 Redemption / call trigger price: $______ ; measurement (e.g. 20 of 30 trading days); notice period: ___ days
[ ] 4 Cashless-exercise table on redemption: yes / no ; make-whole table located: yes / no
[ ] 5 Anti-dilution / reverse-split adjustment clause located (section ref): ______
[ ] 6 Public vs sponsor/private warrant terms differ? yes / no ; which series is this ticker: ______
[ ] 7 Exercise cash for intended position: quantity ____ x strike $____ = $______
[ ] 8 Active ATM > 25% of market cap? (EXCLUSION for warrants)  yes / no
[ ] 9 Value at redemption trigger: cash-exercise path $____ ; cashless-table path $____ ; implied cap multiple ____x
[ ] 10 Quoted spread ≤ 15% of mid: bid ____ ask ____ spread ___%
Result: PASS / EXCLUDED (item no. ____ unconfirmed)        Verified by: batch ____  date ____
```

### deSPAC / post-bankruptcy form (any blank = EXCLUDED)

```
[ ] 1 Plan / combination effective date: ____-__-__   (source: 8-K item 2.01 / plan, accession ______)
[ ] 2 Old-vs-new CUSIP confirmed: old ________ new ________ ; ticker trades NEW equity: yes / no
[ ] 3 "One share legally represents today": ______________________________________________
SPAC only: trust value/share $____ ; redemption deadline ____-__-__ ; post-merger warrant expiry clock ____
```

## 7. Execution specification

Single cost table: `ah/config.py::COST` — the screen, the ML cost model and the tickets all read this one dict.
Ticket template (one per buy-set position, issued only at the Sun Nov 15 lock):

```
PLACE AT SCHWAB: BUY [qty] [ticker] ([vehicle terms]) — LIMIT [price] — DAY
(2) Thesis (≤3 sentences: wave, leadership, durability)
(3) EV decomposition: Zero/Muddle/Re-rate/White Swan probabilities (sum 1.00), net payoff $ and %, EV after costs
(4) Bear case   (5) Invalidation: "Thesis is dead if [event] has/has not occurred by [date]"
(6) Hold/exit doctrine (7.7)   (7) ALL-IN COST ___% of position (void if > 15%)
(8) WASH-SALE WARNING: check all accounts for positions in this issuer before actuating; report answer with the fill
(9) Tradability pre-flight (7.1.1): orderable online ___ ; whole-unit ___ ; OTC fee ___
(10) Kelly tension: fractional Kelly at base rate = 0 or negative; stake exists only because of claimed LIFT ___x
Bounds: valid Mon Nov 16 only; tolerance +10% over lock; beyond = EXPIRED / NO TRADE; limit orders only for warrants/OTC;
        fill crossing >10% of mid = cost-killed; partial < 50% = keep stub, cancel remainder, no top-ups.
Quantity math: qty = floor(A / P_ask); deployed = qty x P; residual = A - deployed (stays in cash)
```

### Ledger template (`ledger.csv` — every Section 7.5 field; blank row = template)

| log_id | event_type | ts_et | ts_utc | ticker | vehicle_terms | thesis | ev_decomposition | bear_case | invalidation | doctrine_ref | sizing_math | bid_lock | ask_lock | spread_lock | bid_fill | ask_fill | spread_fill | limit_price | fill_price | quantity | fees | settled_cash_before | settled_cash_after | model_version | exit_price | exit_reason | gross_pl_usd | gross_pl_pct | net_pl_usd | net_pl_pct | hold_days | followed_doctrine | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |

`event_type` ∈ {stage event, ticket issued, actuation as reported, fill as reported, review event}.

## 8. ML mechanism specification

### 8.1 Data layer — four point-in-time tables (Parquet, queried through DuckDB views in `ah/store.py`)

Partitioning note: the prompt asks for partitioning by as_of_date and ticker. A literal (date × ticker) Hive layout
would create ~10⁷ files; tables are written as zstd Parquet shards and exposed as DuckDB views with `as_of_date`
and `ticker`/`cik` as leading sort keys. Semantics are unchanged; this is recorded as an implementation deviation.

**PRICES** — PK (ticker, date, source)

| column | type | definition |
|---|---|---|
| ticker | str | exchange symbol as in the Nasdaq Trader directory at fetch time |
| date | date | trading session |
| open, high, low, close | double | split-adjusted, not dividend-adjusted |
| adjclose | double | split- and dividend-adjusted |
| volume | double | split-adjusted share volume |
| unadj_close | double | close × Π(later split ratios) — the price a holder actually saw |
| bid, ask | double | where available (live quotes at lock; null in history) |
| halt_flag | bool | inferred: zero-volume session inside a listed window |
| source | str | `yahoo_chart_v8` / `nasdaq_historical` |
| source_timestamp | timestamp | when fetched |

**FILINGS** — two shards: filing index, PK (cik, accn); facts, PK (cik, tag, unit, start, end, val)

| column | type | definition |
|---|---|---|
| cik | int | EDGAR Central Index Key (identity key — never ticker) |
| accn | str | accession number |
| form | str | 10-K, 10-Q, 8-K, S-1, S-3, 424B*, DEF 14A, 15-12*, 25, … |
| filed | date | EDGAR filing date |
| accepted | timestamp | EDGAR accepted datetime (UTC) — **the tradable timestamp** |
| report_date / start / end | date | period covered — **never the usable date** |
| items | str | 8-K item codes (1.03 bankruptcy, 2.01 completed acquisition, 3.01 delisting notice, …) |
| tag, unit, val | str, str, double | XBRL concept and value **as originally filed** |
| version_rank | int | 1 = first filing of this (tag, period); restatements/amendments are new rows with rank 2,3… — never overwritten |
| usable_date | date | `next_session_after(max(accepted, filed))` — see worked example |

**CATALYST & WAVE CALENDAR** — PK (ticker, type, scheduled_date, source)

| column | definition |
|---|---|
| ticker, cik | identity |
| type | earnings, PDUFA, trial_readout, contract_award, index_inclusion, lockup_expiry, investor_day, wave_marker (basket change, anchor-program award, standard adoption) |
| scheduled_date | event date |
| date_first_public | when the date became public — features may use the event only if `date_first_public ≤ decision_time` |
| source | URL / accession |
| outcome_date, outcome | filled only after the fact; never a feature |

**INSTRUMENT TERMS** — PK (instrument_ticker)

| column | definition |
|---|---|
| instrument_ticker, underlying_ticker, cik | identity |
| instrument_type | warrant / LEAPS / convertible / preferred / common |
| strike, exercise_ratio | from the agreement exhibit |
| expiry | expiry or maturity date |
| redemption_trigger, redemption_notice_days, cashless_table | redemption/call terms |
| antidilution_clause | section reference |
| last_amendment_date | latest amendment located |
| instrument_end_date | min(expiry, redemption, call, maturity, delisting) — the durability fact |
| source_accn, source_exhibit, verified_flag | Rule V evidence |

**Worked example — a filing becomes usable only at max(filing_timestamp, next market open):**
A 10-Q for the period ending 2019-06-30 (`end`) is accepted by EDGAR on Thursday 2019-08-08 at 16:32 ET, after
the close. `filed` = 2019-08-08. Its facts get `usable_date` = Friday 2019-08-09 (the next open). A decision
made on the 2019-06-30 quarter-end base date therefore **cannot** see this 10-Q; it sees the 10-Q for the period
ending 2019-03-31 (accepted in May). The feature builder joins facts with `usable_date ≤ decision_date`, never
with `end ≤ decision_date`. When only the filing *date* is known (companyfacts), the rule is the conservative
one: usable the next session strictly after `filed`.

### 8.2 Cohort construction (documented with counts in `cohort_report.md`)

- Identity: CIK + date. Tickers are attributes, never keys (dead tickers are recycled).
- Population: every CIK in the frames master that was an active 10-K/10-Q filer at the base date.
- Base cadence: calendar quarter-ends, 2012Q2 … 2021Q3 for fully matured 5-year windows; later bases are kept with
  shortened (UNRESOLVED) windows, never converted to wins or zeros.
- Entry condition at each base date, using only `usable_date ≤ base_date` data: priced-for-failure (any of three
  Section 5.2 tests) AND tradability floor.
- Two labelled subsets, kept separate in every count:
  - `S1_PRICED`: the security is still quoted, so a full daily price path exists. Exact Section 5.1 formulas.
  - `S2_UNPRICED`: the entity later died/was acquired and its ticker was purged from every reachable price source.
    Market value comes from dei:EntityPublicFloat (labelled `FLOAT_PROXY`); outcome from EDGAR terminal events.
- Classes: SWAN (peak close-based multiple ≥ 25x within ≤ 5y of entry, OR terminal net multiple ≥ 10x),
  GRAVEYARD (expired worthless / delisted to no bid / > 95% down without recovery / diluted to a stub),
  MUDDLE (everything else). `S2` outcomes: bankruptcy (8-K 1.03) or deregistration without merger evidence =
  GRAVEYARD; merger/tender evidence = ACQUIRED (MUDDLE unless float-implied value ≥ 10x, then `POSSIBLE_SWAN_UNPRICED`,
  reported as an upper-bound bracket).
- Imbalance: raw counts and true base rate printed before modelling; class weights only for fitting; every output
  probability re-anchored to true population prevalence (prior-shift correction on the logit).
- Survivorship traps, each with a test in `tests/`: (1) population includes dead CIKs; (2) identity by CIK+date;
  (3) as-first-filed values only (`version_rank = 1` at decision time); (4) tradability at base date checked on
  unadjusted price and real volume; (5) warrant terms coverage rate reported, uncovered warrant bases are their own subset.

### 8.3 Label pseudocode (touches no post-decision filing revision: labels read PRICES and filing-index event dates only)

```
for each (cik, base_date) in buyable_bases:
    t0      = next_session(base_date)
    entry   = ask(t0)                      # = close(t0) * (1 + half_spread[class]) when no quote history; ASSUMED flag set
    if not tradable(t0): mark UNTRADABLE_BASE and exclude from the cohort (logged, counted)
    for H in (1y, 3y, 5y):
        window = sessions in (t0, t0 + H]
        if window has no quotes at all:            label[H] = UNRESOLVED
        elif series ends before t0 + H:
            end_event = terminal_event(cik)        # filing-index event dates only (15-12*, 25, 8-K 1.03 / 2.01)
            MFE[H]      = max(close in window) / entry                       # diagnostic + swan class only
            TERMINAL[H] = last_bid_before_end * (1 - exit_cost) / entry      # 0 if bankruptcy/cancellation
            window_shortened[H] = True
        else:
            MFE[H]      = max(close in window) / entry
            TERMINAL[H] = bid(t0 + H) / entry  - fees       # bid = close * (1 - half_spread[class])
    went_to_zero_or_delisted = 1 if (terminal_event in {expired, delisted_no_bid, bankruptcy})
                                    or min(close after t0, within 5y) <= 0.05 * entry with no later recovery above 0.05*entry at window end
    class = SWAN if MFE[5y] >= 25 or TERMINAL[5y] >= 10
            GRAVEYARD if went_to_zero_or_delisted or stub
            MUDDLE otherwise
# Split handling: closes are split-adjusted with split events known ex-post — legitimate for LABELS (outcomes),
# forbidden for FEATURES (features use unadj_close and shares as filed at decision time).
# No label reads companyfacts values filed after base_date except share counts used for the "stub" test,
# which is an outcome measurement, not a feature.
```

### 8.4 Feature schema (every feature: data with `usable_date ≤ decision_date`)

| feature | formula | source table | lag rule |
|---|---|---|---|
| drawdown_3y | 1 − price / max(unadj-consistent close, trailing 3y) | PRICES | closes ≤ decision date |
| ev_to_rev | EV / TTM revenue (EV per 5.1 on reported shares) | PRICES+FILINGS | filings usable ≤ decision |
| mcap_to_cash | market cap / cash & ST investments | PRICES+FILINGS | same |
| mcap_log | log market cap (price × cover shares; `FLOAT_PROXY` for S2) | PRICES+FILINGS | same |
| short_interest_to_float | short interest / float | Nasdaq SI (current names only; excluded from training, rubric-only) | publication date |
| cash, burn_2q | cash; mean operating cash burn of last 2 filed quarters | FILINGS | usable ≤ decision |
| runway_years | (cash − debt due < 12m) / TTM burn; cap 10; cash-positive flag | FILINGS | same |
| debt_due_12m_to_cash | current debt / cash | FILINGS | same |
| current_ratio | current assets / current liabilities | FILINGS | same |
| rev_ttm_log, rev_growth_yoy | log TTM revenue; TTM vs prior TTM | FILINGS | same |
| gross_margin | gross profit / revenue | FILINGS | same |
| rd_to_rev | R&D / revenue (capped) | FILINGS | same |
| share_growth_1y, share_growth_3y | cover shares now / 1y (3y) ago − 1 | FILINGS | same |
| warrants_converts_to_shares | (warrants + convert shares) / shares outstanding | FILINGS | same |
| s1_s3_90d | S-1/S-3/424B filed within 90 days | FILINGS index | filed ≤ decision |
| reverse_split_12m | share count fell > 40% q/q inside 12 months (or split ratio tagged) | FILINGS | same |
| auth_headroom | 1 − shares outstanding / authorized | FILINGS | same |
| issuance_rate | financing inflow TTM / market cap | FILINGS | same |
| going_concern_proxy | runway < 1y and negative equity | FILINGS | same |
| instrument_years_left, redemption_distance | durability facts | INSTRUMENT TERMS | terms known ≤ decision |
| peer_basket_ret_6m/12m, peers_up_20pct | SIC-2 basket trailing returns; count of peers up > 20% | PRICES | closes ≤ decision |
| peer_volume_trend | SIC-2 basket dollar volume, 3m vs 12m | PRICES | same |
| adv20_log, spread_assumed | 20-day ADV$; cost-table spread by class | PRICES | same |
| era controls | none as features (calendar era is a clustering unit, not a predictor) | — | — |

No feature encodes anything dated after the decision time; a unit test asserts `max(source usable_date) ≤ base_date` per row.

### 8.5 Leakage controls and validation

- Purged walk-forward, expanding window: train on bases whose 5y label window closed before the test block starts
  (purge = label-window overlap), test on the next 12 months of base dates, roll. Embargo = max label horizon in use.
  Where the 2012–2026 window cannot support a full 5y embargo on both sides, the fold is marked `PARTIALLY_PURGED`.
- Clusters kept whole: CIK; SIC-2 theme; calendar era (base year). Effective sample sizes are reported in clusters.
- Benchmarks on the identical universe and dates: (a) human rubric as code (`ah/rubric.py`), (b) random selection,
  1,000 bootstrap draws. Criteria: precision-at-top-k and Brier / log-loss vs climatology. Never accuracy.
- Sensitivity sweep: swan threshold {20, 25, 35}x; forward window {4, 5, 6}y; costs {0.5, 1, 2}× table; cadence shifted
  one quarter. Deliverable rank = range across the sweep; FRAGILE = rank range spans more than half the field.

### 8.6 Model and pre-flight

Pre-flight prints: # swan (25x peak), # 10x-terminal, # graveyard, by subset and in distinct-CIK and era clusters.
< 30 swan positives ⇒ no swan model: rubric + base-rate tables (+ graveyard model if its counts allow); boosting
forbidden. Otherwise: elastic-net logistic (champion) for P(swan by 5y) and P(zero/delisted); shallow GBM
(depth ≤ 3, strong shrinkage, min child weight) challenger, promoted only on purged OOS wins. Platt/isotonic
calibration on purged folds + true-prevalence correction. EV wiring: `EV = P(swan)·M_net − P(zero)·1 − costs`,
shown beside (never replacing) the human p4_filtered. Model frozen at R4; version hash logged on every ledger row.

### 8.7 Cross-check

Rubric + Fermi are computed and written to disk (`human_scores.parquet`, hash logged) before the model ranks are
joined. The model never receives a human score. Disagreement rules and vetoes exactly as Section 8.7.

## 9. Buy-set template (R7)

```
FINAL BUY SET — for actuation Mon Nov 16, 2026 | Funding: [settled $ as reported / AWAITING FUNDING REPORT] | Cohort validation: [verdict]
PRIMARY — #1: [one-paragraph case]
| Rank | Ticker | Vehicle (terms) | Allocation $ | Lock price (ask, as-of) | Quantity | $ deployed | Residual cash | All-in cost % |
  ... Allocation $ sums to EXACTLY $800 ; residual row printed
Per-name dossiers: ticket (7.1 format) · thesis · EV decomposition with 1/3/5y paths · bear case · invalidation · doctrine
Portfolio math (6.6) incl. the most-likely-outcome sentence
Monday in ≤ 5 lines
(Empty set = NO-TRADE verdict with arithmetic; no other form.)
```

## First 10 concrete actions (execution order)

1. Create `asymmetry-hunter-state/`, write STATE.md with the Section 0 rules restated and the waiver recorded.
2. Probe every Section 2 source from this environment; record what is reachable and what is not.
3. Build the survivorship-free CIK master from XBRL frames (2009Q2–2026Q3).
4. Pull submissions + companyfacts for every master CIK into the FILINGS tables (as-first-filed, with filed dates).
5. Enumerate the full listed field from the Nasdaq Trader directory; classify instrument types.
6. Pull full daily price history for every listed non-ETF security into PRICES.
7. Map symbols ↔ CIKs; add SEC-reporting OTC names; apply floors F1–F5 with coverage-ledger entries.
8. Run the cheap damage scan (D1) on the whole surviving field; write `universe.csv`.
9. Cluster D1 survivors by SIC and emergent theme; tag SPAC/deSPAC/post-bankruptcy/biotech-platform from filings.
10. Start R3 verification batches (≤ 25 names each, parallel) and, independently, the cohort build.
