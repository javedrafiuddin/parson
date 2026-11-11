# Ranked table — R5/R6 result: **NO TRADE**

**NO TRADE: the filter does not beat the base rate enough to make EV positive.**

As-of 2026-11-11. Rule: a name enters the buy set only with LIFT ≥ 2.5x over the measured base rate AND EV per $1 > 0 at its own filtered
numbers AND a plausible ≥ 10x path (Sections 6.2–6.3), AND a VERIFIED row (Rule V), AND survival of its red-team pass (R6). No name meets all five.

## The arithmetic

Measured base (cohort): p4_base = survival 0.655 × wave 0.0252 × leads 0.393 × captures 0.604 = **0.00392 (1-in-255)**.

LIFT = (survival_f ÷ 0.655) × (wave_f ÷ 0.0252) × (leads_f ÷ 0.393) × (captures_f ÷ 0.604). Ceilings available to any name in this field:
- wave: the strongest sub-theme found anywhere scored 2 of 5 → 0.05 → ≤ 1.98x
- leads: "leader" 0.55 → 1.40x; "participant" 0.25 → 0.64x; "laggard" 0.10 → 0.25x
- captures (common stock, trim plan): 0.68 → 1.13x
- survival: capped at 0.95 → ≤ 1.45x

So a participant can reach at most 1.45 × 1.98 × 0.64 × 1.13 = **2.07x** (< 2.5x) and a laggard at most 0.81x. Only a leader in a wave-score-2 theme can reach 2.5x.

### The ten names that reached full math (after the R6 red team)

| Name | LIFT | p4_filtered | P(zero) | Plausible ceiling | EV per $1 (5y) |
|---|---|---|---|---|---|
| VRRM | 2.2x | 0.0088 (base 0.00392) | 0.192 | 18.7x | +0.201 |
| KLC | 2.3x | 0.0092 (base 0.00392) | 0.156 | 16.3x | +0.232 |
| ALIT | 1.8x | 0.0071 (base 0.00392) | 0.348 | 21.1x | +0.031 |
| FMC | 2.4x | 0.0095 (base 0.00392) | 0.373 | 10.6x | -0.508 |
| RXST | 0.4x | 0.0014 (base 0.00392) | 0.107 | 17.1x | +0.072 |
| FLNC | 5.9x | 0.0230 (base 0.00392) | 0.164 | 7.4x | +0.061 |
| METC | 2.5x | 0.0098 (base 0.00392) | 0.219 | 10.1x | -0.046 |
| TE | 1.4x | 0.0056 (base 0.00392) | 0.172 | 6.0x | +0.185 |
| ABAT | 1.2x | 0.0049 (base 0.00392) | 0.375 | 8.8x | -0.271 |
| BLNK | 1.6x | 0.0061 (base 0.00392) | 0.216 | 11.0x | +0.005 |

VRRM, KLC, ALIT and FMC were the four finalists before R6. The red team (memos in `redteam/`, answers in `redteam/ANSWERS.md`) found filing-backed
damage in all four: a terminated anchor contract and 2029 notes (VRRM); a 2028 term-loan wall with refinancing talks abandoned (ALIT); $1.58B of
leases and falling occupancy (KLC); revenue −80%, negative operating cash flow, covenant re-test at 6.75x (FMC). After the corrections, every one is below 2.5x.

### The 98 pool names verified at filing level on 2026-11-11 (batches VA-01..VA-11)
80 SURVIVOR · 10 REJECTED · 8 COULD_NOT_VERIFY. Of the 80: 24 VERIFIED, 56 PARTIALLY_VERIFIED (Rule V: the latter cannot be ranked).
Leaders: ARDX, IRWD, SAFE, NVCR, PRCT, WGS, AXTI, COUR, BFAM, BRBR, UPST. Leaders in a wave-score-2 theme: NVCR, WGS, AXTI, UPST — all PARTIALLY_VERIFIED,
and all with a plausible ceiling below 10x (1.5x their own 3-year high: NVCR 4.0x, WGS 3.8x, AXTI 4.9x, UPST 6.0x; AXTI and WGS already ran 121x and 135x in 2022–26).
Every other leader's ceiling is 3.9x–8.4x except BRBR (12.4x), whose wave score is 0 → lift ≤ 0.40 × 1.45 × 1.40 × 1.13 = 0.92x.
**No verified-batch name can clear the bar; none was carried into full math.**

## What the verdict means
The $800 is deployed nowhere and stays as cash. This is the system working as specified, not a failure to find something:
the field was screened from 14,177 securities; the cohort says deep-drawdown names returned money in only four of ten base years; and every name
that looked like an exception lost its edge once its filings were read adversarially.
