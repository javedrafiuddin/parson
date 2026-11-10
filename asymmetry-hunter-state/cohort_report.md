# Cohort report — Section 8 (white-swan and graveyard cohorts)

Built 2026-11-10. Code: `ah/cohort.py`, `ah/labels.py`, `ah/model.py`, `scripts/r4_build_cohort.py`, `r4_model.py`,
`r4_baserate_model.py`, `r4_wave_rates.py`. Tables: `data/derived/cohort_bases.parquet`, `model_validation.json`,
`baserate_validation.json`, `wave_rates.json`.

## Verdict first

- **Swan class: validation FAILED / not demonstrated.** No model beats the human rubric at ranking future swans. At a full
  5-year purge only 2 of 4 test years can be evaluated at all (the early training windows hold 3–9 swans); in those two
  the elastic-net ranker found 3 swans in its top 50s versus 3 for the rubric and 1.2 expected at random,
  and its probabilities were far worse than the base-rate forecast. The elastic-net swan model is **retired**; gradient
  boosting was a challenger only and was not promoted.
- **Degradation applied (8.6):** P(swan) is taken from a base-rate table (unweighted logistic on four pre-specified rubric
  buckets). Under a partially purged 3-year test both the table and the rubric found about three times as many swans as
  random selection (5 and 5 vs 1.6 expected in the top 50s over four test years) — a small-sample result, labelled PARTIALLY_PURGED.
- **Graveyard class: validation PASSED.** The elastic-net P(zero) model beat the rubric, random selection, and the base-rate
  forecast (Brier and log-loss) in 4 of 4 fully purged test years: 82 wipeouts in its top 50s vs 32 for the rubric and 22 at random.
- This line goes on the first page of the buy set: *"Cohort validation: swan ranking FAILED its benchmarks (no model beats the rubric;
  fully purged test not feasible before 2020); wipeout model PASSED 4/4 purged folds."*

## Data sources and their known gaps

| Table | Source | Gap |
|---|---|---|
| Security master | SEC XBRL frames, every CIK reporting cover-page shares or public float 2009Q2–2026Q3: 16,594 CIKs | XBRL era only (small companies from mid-2011). Pre-2011 deaths are absent. Entities that never filed XBRL are absent |
| Fundamentals | SEC companyfacts, value as FIRST filed + filing date | Dimensional facts (per-class share counts) are not in companyfacts; multi-class and ADS share counts are unreliable |
| Filing events | SEC submissions index (latest 1,000 filings per CIK; 3,269 CIKs have older pages not pulled) | A bankruptcy 8-K older than the latest 1,000 filings of a still-filing estate can be missed |
| Prices | Yahoo chart API (split-adjusted daily closes) for securities quoted today | **Dead tickers are purged**: 20 of 25 known-dead test tickers returned nothing. No bid/ask history — entry at an assumed ask, exit at an assumed bid (2% round trip, listed common; ASSUMED) |
| Dead-name prices | SEC fails-to-deliver files would supply them | `www.sec.gov` refuses this environment — not available |

## Construction, with counts at every step

| Step | Count |
|---|---|
| CIK-dates with a balance sheet known before a quarter-end base date (2012Q2–2025Q3) | 391,355 |
| … that were active 10-K/10-Q filers at the base date | 346,854 |
| Priced CIKs (a line is quoted today) | 5,404 |
| Dropped: priced CIK with no quote near that base date (pre-listing) | 5,503 |
| Active-filer CIK-dates kept | 341,351 (S1_PRICED 145,917; S2_UNPRICED 195,434) |
| Buyable bases (priced-for-failure AND tradable at the base date) | S1 55,791; S2 36,740 |
| … of which matured (5-year window closed by 2026-11-09) | 58,644 (S1 28,757; S2 29,887) |

Entry condition as implemented: S1 uses the exact Section 5.2 tests on prices (drawdown ≥ 60% from the split-adjusted 3-year
high, or EV < 2.0x TTM revenue, or cap < $500M with TTM revenue > $20M) and 20-day ADV ≥ $250k. S2 has no prices, so market
value is the latest filed public float (`FLOAT_PROXY`), drawdown is float vs its 3-year maximum, and tradability is float ≥
$56M — the float level at which half of priced names clear the $250k ADV floor (calibrated on S1).

## Pre-flight class count (8.6) — matured bases, 2012Q2–2021Q3

| Class | S1_PRICED name-dates | S2_UNPRICED name-dates | Distinct CIKs |
|---|---|---|---|
| SWAN (peak ≥ 25x within 5y, or 5y terminal ≥ 10x net) | 363 | 0 by construction | 121 |
| … peak ≥ 25x | 204 | — | 77 |
| … 5y terminal ≥ 10x | 276 | — | 91 |
| GRAVEYARD (S1: ≥ 95% loss at 5y; S2: bankruptcy 8-K) | 1,752 | 2,592 | 790 (incl. broad) |
| GRAVEYARD_BROAD (S2: went dark / deregistered, no merger evidence) | — | 924 | |
| MUDDLE (S2: merged/acquired, or still filing at window end) | 26,642 | 25,664 | |
| POSSIBLE_SWAN_UNPRICED (S2: float-implied value ≥ 10x) — label unknown | — | 707 | 130 |

Swan CIKs by base year: {'2012': 2, '2013': 1, '2014': 1, '2015': 8, '2016': 20, '2017': 19, '2018': 24, '2019': 34, '2020': 67, '2021': 15}. Two thirds of all swan companies come from 2018–2020 bases: in wave terms
this is a handful of observations (the 2020–21 melt-up above all), not 121 independent ones.

**True base rates (before any modelling):** swan 0.62% of matured name-dates (lower bound; up to 1.82% if every
unpriced "possible" were real); 25x-peak alone 0.35%; graveyard 8.98%. On June bases only: swan
0.56% (85 of 15,134), 25x peak 0.32%.
A peak of 190x or more happened on 7 name-dates of 2 companies in 28,757 priced bases.

A model that predicts "never a swan" is 99.4% accurate and worthless; accuracy is not reported anywhere.

## Imbalance and survivorship handling actually applied

- Class weights / case-control sampling only for fitting; every probability shifted back to true prevalence on the logit
  (`model.prior_correct`). The base-rate table model is fitted unweighted, so it sits at true prevalence by construction.
- Trap 1 (training only on survivors): the population is every active filer, 29,887 of 58,644 matured bases are dead/unpriced names.
- Trap 2 (current ticker as identity): identity is CIK + date; tickers are attributes. A reorganised issuer with a new CIK appears as a
  merged/acquired S2 name plus a new S1 name — recorded, not repaired.
- Trap 3 (restated financials): features read the first-filed value of each period and only filings dated strictly before the
  base date (tests `test_pit_panel_never_sees_later_filings`, `test_as_first_filed_not_restated`).
- Trap 4 (untradable fantasy entries): entry needs a quote within 7 days before and 10 days after the base date and ADV ≥ $250k at the base.
- Trap 5 (warrant agreements): **the warrant cohort could not be built.** Dead warrants have no prices and their agreements are not
  readable here; terms-table coverage of historical warrant bases is 0%. Warrants are judged on the underlying's cohort plus the
  instrument's own terms; there is no measured warrant base rate in this run.
- No price-derived feature enters any model: price history exists only for survivors and would leak the outcome.

## Measured replacements for the Section 6.1 placeholders (June bases, both subsets)

| Factor | Placeholder | Measured | Definition used |
|---|---|---|---|
| P(survival) | 0.50 | 0.655 | listed standalone 5 years later (25.5% were acquired/merged inside 5 years, 8.9% went to zero/bankrupt/dark) |
| P(theme wave) | 0.125 | 0.0252 | share of SIC-3 industry-year episodes (≥ 8 bases) whose leader basket (top quintile by 5y peak) had a median peak ≥ 10x: 11 of 436; every one in 2018–2021 bases |
| P(company leads) | 0.225 | 0.393 | in wave episodes, share of surviving names whose own peak was at least half the leader basket's (0.255 of all names) |
| P(holder captures) | 0.15 | 0.604 | common stock, of names that peaked ≥ 25x: share still ≥ 10x at year 5 (n = 48) |
| Product | 0.00211 (1-in-474) | 0.00392 (1-in-255) | cross-check: directly measured 25x-peak rate on the same bases = 0.00317 |

The measured product governs; the placeholder is retired. Note the two differ in target: the placeholder was pitched at a
QBTS-class (190x) outcome in a convex instrument; the measured figure is a ≥ 25x peak in common stock.
P(theme wave) is the weakest link and is almost entirely an era effect: by base year it is {'2012': 0.0, '2013': 0.0, '2014': 0.0, '2015': 0.0, '2016': 0.0, '2017': 0.0, '2018': 0.02, '2019': 0.019, '2020': 0.131, '2021': 0.02}.

## Validation (8.5) — purged walk-forward, expanding window, annual June test blocks, quarterly training pool

### A. Swan, elastic-net champion, FULLY PURGED (5-year labels, 5-year purge)

| Test year | Train years | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | — | — | — | — | — | — | — | — | skipped: train positives 3 (< 8), test n 1533, test positives 7 |
| 2019 | — | — | — | — | — | — | — | — | skipped: train positives 5 (< 8), test n 1565, test positives 12 |
| 2020 | 2012-2015 | 9 | 30/1829 | 0.0473 vs 0.0164 | 0.5330 vs 0.1232 | 2 | 2 | 0.86 (p95 2.0) | |
| 2021 | 2012-2016 | 31 | 12/1679 | 0.2238 vs 0.0071 | 2.5371 vs 0.0483 | 1 | 1 | 0.35 (p95 1.0) | |

### B. Swan, shallow GBM challenger, FULLY PURGED

| Test year | Train years | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | — | — | — | — | — | — | — | — | skipped: train positives 3 (< 8), test n 1533, test positives 7 |
| 2019 | — | — | — | — | — | — | — | — | skipped: train positives 5 (< 8), test n 1565, test positives 12 |
| 2020 | 2012-2015 | 9 | 30/1829 | 0.0164 vs 0.0164 | 0.2166 vs 0.1232 | 1 | 2 | 0.86 (p95 2.0) | |
| 2021 | 2012-2016 | 31 | 12/1679 | 0.0071 vs 0.0071 | 0.0727 vs 0.0483 | 0 | 1 | 0.35 (p95 1.0) | |

### C. Swan, base-rate table model (the degradation path), FULLY PURGED 5y

| Test year | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: table model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|
| 2018 | — | — | — | — | — | — | — | skipped: train positives 3 (< 8); test positives 7 |
| 2019 | — | — | — | — | — | — | — | skipped: train positives 5 (< 8); test positives 12 |
| 2020 | 9 | 30/1829 | 0.0164 vs 0.0164 | 0.1215 vs 0.1232 | 1 | 2 | 0.86 (p95 2.0) | |
| 2021 | 31 | 12/1679 | 0.0072 vs 0.0071 | 0.0606 vs 0.0483 | 0 | 1 | 0.35 (p95 1.0) | |

### D. Swan, base-rate table model, PARTIALLY_PURGED (3-year labels with a full 3-year purge)

| Test year | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: table model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|
| 2016 | — | — | — | — | — | — | — | skipped: train positives 2 (< 8); test positives 3 |
| 2017 | — | — | — | — | — | — | — | skipped: train positives 2 (< 8); test positives 5 |
| 2018 | — | — | — | — | — | — | — | skipped: train positives 2 (< 8); test positives 11 |
| 2019 | — | — | — | — | — | — | — | skipped: train positives 6 (< 8); test positives 9 |
| 2020 | 17 | 19/1829 | 0.0103 vs 0.0104 | 0.0691 vs 0.0777 | 1 | 3 | 0.53 (p95 2.0) | |
| 2021 | 46 | 2/1679 | 0.0012 vs 0.0012 | 0.0122 vs 0.0092 | 0 | 0 | 0.06 (p95 1.0) | |
| 2022 | 96 | 18/2179 | 0.0082 vs 0.0082 | 0.0499 vs 0.0523 | 3 | 0 | 0.39 (p95 2.0) | |
| 2023 | 161 | 29/2173 | 0.0132 vs 0.0133 | 0.0799 vs 0.0792 | 1 | 2 | 0.63 (p95 2.0) | |

The 5-year swan label cannot be validated at full purge inside a 2012–2026 window: the purge leaves 3, 5, 9 and 31 training
swans for the four test years. D is the compromise and is marked PARTIALLY_PURGED: the label horizon is shortened to 3 years.

### E. Graveyard (zero / delisted), elastic-net, FULLY PURGED

| Test year | Train years | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | 2012-2013 | 330 | 137/1533 | 0.0797 vs 0.0818 | 0.2877 vs 0.3040 | 18 | 10 | 4.47 (p95 8.0) | |
| 2019 | 2012-2014 | 732 | 146/1565 | 0.0816 vs 0.0851 | 0.2930 vs 0.3133 | 20 | 6 | 4.64 (p95 8.0) | |
| 2020 | 2012-2015 | 1184 | 195/1829 | 0.0896 vs 0.0963 | 0.3068 vs 0.3461 | 21 | 6 | 5.31 (p95 9.0) | |
| 2021 | 2012-2016 | 1689 | 251/1679 | 0.1233 vs 0.1325 | 0.4098 vs 0.4520 | 23 | 10 | 7.52 (p95 11.0) | |

### F. Graveyard, shallow GBM challenger, FULLY PURGED

| Test year | Train years | Train positives | Test positives / n | Brier model vs climatology | Log-loss model vs climatology | Hits in top 50: model | rubric | random mean | note |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | 2012-2013 | 330 | 137/1533 | 0.0711 vs 0.0818 | 0.2463 vs 0.3040 | 20 | 10 | 4.47 (p95 8.0) | |
| 2019 | 2012-2014 | 732 | 146/1565 | 0.0779 vs 0.0851 | 0.2705 vs 0.3133 | 15 | 6 | 4.64 (p95 8.0) | |
| 2020 | 2012-2015 | 1184 | 195/1829 | 0.0844 vs 0.0963 | 0.2847 vs 0.3461 | 20 | 6 | 5.31 (p95 9.0) | |
| 2021 | 2012-2016 | 1689 | 251/1679 | 0.1226 vs 0.1325 | 0.4033 vs 0.4520 | 12 | 10 | 7.52 (p95 11.0) | |

GBM was not promoted for either target (it did not beat elastic-net on precision at the top).

## Sensitivity sweep

Configurations: swan threshold 20x / 25x / 35x; window 4 / 5 / 6 years; costs 0.5x / 1x / 2x; cadence shifted (Mar+Sep only,
Jun+Dec only); unpriced possibles counted as swans. Median configuration: 25x, 5 years, 1x cost, all quarters.
- Retired elastic-net swan model: 1,002 of 1,637 names FRAGILE (rank range wider than half the field) — one more reason it is retired.
- Base-rate table model: 148 of 1,637 FRAGILE. Its P(swan) across today's field: median 0.39%, 90th pct 2.71%, max 10.54%.

## What the cohort says about expected value (5-year hold, net of the 2% assumed round trip; S2 merged names carried at 1.0x)

| Stratum | n | Mean 5y multiple − 1 | … White Swan row capped at 25x | Median multiple | P(zero) | P(≥ 10x terminal) |
|---|---|---|---|---|---|---|
| All matured bases | 58,644 | +0.32 | +0.27 | 1.00 | 10.2% | 0.47% |
| Drawdown < 60% | 45,323 | +0.28 | +0.28 | 1.00 | 5.5% | 0.23% |
| Drawdown 60–80% | 8,244 | +0.31 | +0.28 | 1.00 | 19.8% | 0.82% |
| Drawdown 80–90% | 2,634 | +0.43 | +0.28 | 0.55 | 32.7% | 1.78% |
| Drawdown ≥ 90% | 2,443 | +0.98 | +0.12 | 0.32 | 40.0% | 2.33% |
| Drawdown ≥ 80%, cap $32–100M | 1,569 | +1.12 | +0.21 | 0.37 | 37.4% | 2.29% |
| Drawdown ≥ 80%, cap $100–316M | 1,381 | +1.15 | +0.39 | 0.88 | 30.9% | 2.39% |
| Drawdown ≥ 80%, cap < $32M | 953 | −0.20 | −0.21 | 0.06 | 58.2% | 1.68% |

By base year the ≥ 80%-drawdown stratum returned −0.20, −0.18, −0.14, −0.04 (2012–2015), +2.26, +1.48 (2016–2017), −0.06, +0.19
(2018–2019), +2.61 (2020), −0.31 (2021). **Six of ten base years lost money; the average is positive because of two eras.**
The most likely single outcome in the deep-drawdown strata is losing half or more; one base in three goes to zero.

Counter-intuitive finding recorded honestly: inside the deep-drawdown stratum, names with ≥ 2 years of runway did *not* show
higher swan rates than short-runway names (0.5% vs 2.4% terminal ≥ 10x); cash-flow-positive names showed the best (3.1%).
Long runway lowers P(zero); it has not, historically, raised P(swan).

Model version frozen for this run: `ah-v3-e679a99d598d` (wipeout model) + base-rate table v1.
