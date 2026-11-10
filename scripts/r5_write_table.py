"""Write asymmetry-hunter-state/ranked_table.md from data/derived/r5_math.json (R5 output contract, Section 9)."""
import json, pathlib, sys
import pandas as pd, numpy as np
S = pathlib.Path('asymmetry-hunter-state'); D = pathlib.Path('data/derived')
R = json.load(open(D / 'r5_math.json')); N = R["names"]; B = R["base_factors"]
p4b = B["survival"] * B["wave"] * B["leads"] * B["captures"]
CFG = json.load(open(D / 'r5_finalists.json'))
Q, fin, alloc, surv, quote_note = CFG["quotes"], CFG["finalists"], CFG["alloc"], CFG["survival_score"], CFG["quote_note"]
rows = []
for s in fin:
    v = N[s]; F = v["fermi"]; fl = v["filtered"]; t = v["traj"]; last, bid, ask = Q[s]
    lifts = {k: fl[k] / B[k] for k in B}
    rows.append("| " + " | ".join([
        f"**{s}** ({v['name']})", "Common stock (no expiry; durability = survival)",
        f"ask ${ask:.2f} / bid ${bid:.2f}, last ${last:.2f} — {quote_note}; close 2026-11-09 ${v['px']:.2f} (Yahoo, delayed)",
        f"{(ask - bid) / ((ask + bid) / 2):.1%} (quote as stated; regular-hours spread to be taken at the lock)",
        f"{v['sh'] / 1e6:,.1f}M outstanding + {v['extra'] / 1e6:,.1f}M dilutive today; year-5 projection {t['1.0']['5'] / 1e6:,.0f}M (flat) / {t['3.0']['5'] / 1e6:,.0f}M (3x) / {t['10.0']['5'] / 1e6:,.0f}M (10x)",
        f"cash-positive (operating cash flow TTM ${v['ocf'] / 1e6:,.0f}M); survival score {surv[s]}/100; debt ${v['debt'] / 1e6:,.0f}M vs cash ${v['cash'] / 1e6:,.0f}M",
        f"{v['wave_line']}. Supporting dates: {v['cats']}",
        "Indefinite vs 5-year wave window; the holder is cut off only by bankruptcy, delisting or a capped takeout",
        f"{F['p4_base']:.5f} (1-in-{1 / F['p4_base']:.0f})",
        f"{F['lift']:.1f}x = survival {lifts['survival']:.2f}x · wave {lifts['wave']:.2f}x · leads {lifts['leads']:.2f}x · captures {lifts['captures']:.2f}x (range {F['p4_low'] / F['p4_base']:.1f}x–{F['p4_high'] / F['p4_base']:.1f}x)",
        f"{F['p4_filtered']:.4f} (1-in-{1 / F['p4_filtered']:.0f}); range {F['p4_low']:.4f}–{F['p4_high']:.4f}",
        f"base-rate table P(swan) {v['p_swan_table']:.2%} (sweep {v['p_swan_table_range'][0]:.2%}–{v['p_swan_table_range'][1]:.2%}); rank {v['rank_table'][0]:.0f}–{v['rank_table'][1]:.0f} of 1,637; FRAGILE: {'yes' if v['fragile'] else 'no'}; model P(zero) {v['p_zero_model']:.1%}",
        f"{v['ev']['ev_per_dollar']:+.3f} (White Swan row at the plausibility cap {v['m_swan']:.1f}x; the 50x and 25x caps do not bind: {v['ev_cap50']:+.3f} / {v['ev']['ev_per_dollar']:+.3f})",
        v["bear"], v["inval"], f"${alloc[s]} ({CFG['alloc_note']})"]) + " |")
hdr = "| Ticker | Vehicle (terms incl. strike/expiry) | Price (ask, source, as-of) | Spread % | Fully diluted shares (today + year-5 trajectory) | Runway (years, 5.1 formula) + survival score | Wave case (one line) + dated catalysts (supporting) | Durability (instrument life vs. wave window) | p4_base | LIFT (with the factor changed) | p4_filtered | Model rank (sweep range + FRAGILE flag) | Net EV per $1 (5y, and capped at 50x/25x) | Bear case (one line) | Invalidation (dated) | Proposed allocation (7.3) |\n|" + "---|" * 16


def scen(s):
    v = N[s]; p = v["probs"]; pay = v["payoffs"]; sp = v["scenario_paths"]; a = alloc[s]
    L = [f"**{s}** — probabilities at 5 years: {p['Zero']:.3f} + {p['Muddle']:.3f} + {p['Re-rate']:.3f} + {p['White Swan']:.4f} = {sum(p.values()):.2f}", "",
         "| Scenario | P (5y) | Net multiple year 1 | year 3 | year 5 | P × multiple | $ on the proposed allocation |", "|---|---|---|---|---|---|---|"]
    for k in ("Zero", "Muddle", "Re-rate", "White Swan"):
        L.append(f"| {k} | {p[k]:.4f} | {sp[k][0]}x | {sp[k][1]}x | {pay[k]:.2f}x | {p[k] * pay[k]:.3f} | ${a * pay[k]:,.0f} |")
    e = v["ev"]; pth = v["paths"]
    L += ["", f"EV per $1 = {sum(p[k] * pay[k] for k in p):.3f} − 1 = **{e['ev_per_dollar']:+.3f}**; on ${a}: {a * e['ev_per_dollar']:+,.0f}. Breakeven on the White Swan term alone: p = 1 ÷ {v['m_swan']:.1f} = {1 / v['m_swan']:.3f} (1-in-{v['m_swan']:.0f}); given the other rows: {e['breakeven_p_swan_given_other_rows']:.4f}.",
          f"Max loss = 100% of the position. This position can expire worthless, be delisted, or go to zero. Asymmetry ratio: plausible net upside {v['m_plaus']:.1f}x ÷ 1.0.",
          f"Paths on year-5 projected shares (10x-path dilution): 25x = ${pth['25']['price']:.2f}/share → market cap ${pth['25']['cap_busd']:.1f}B; 50x = ${pth['50']['price']:.2f} → ${pth['50']['cap_busd']:.1f}B; 190x = ${pth['190']['price']:.2f} → ${pth['190']['cap_busd']:.1f}B. "
          f"Its own 3-year high was ${v['hi']:.2f} ({v['hi_d']}), {v['hi'] / v['px']:.1f}x today's price; 25x would be {25 * v['px'] / v['hi']:.1f}x that high, so the plausible ceiling is set at 1.5x the old high, diluted = {v['m_plaus']:.1f}x. The 50x and 190x paths are not plausible for this name and carry no probability.",
          f"Fractional Kelly (diagnostic only): at the base rate {v['kelly_base']:+.3f} (the base-rate-correct stake is $0); at the filtered probability {v['kelly_filtered']:+.3f} — also negative on the swan term alone. Any stake rests on the muddle and re-rate rows of the cohort and on the claimed lift, not on Kelly.",
          f"Evidence: {v['acc']}.", ""]
    return "\n".join(L)


vsum = pd.DataFrame([{"Ticker": s, "LIFT": f"{v['fermi']['lift']:.1f}x", "p4_filtered": f"{v['fermi']['p4_filtered']:.4f}", "P(zero) used": f"{v['p_zero_used']:.3f}", "Plausible ceiling": f"{v['m_plaus']:.1f}x",
                      "EV per $1": f"{v['ev']['ev_per_dollar']:+.3f}", "Year-5 shares ÷ today (flat)": f"{v['traj']['1.0']['5'] / v['sh']:.2f}x"} for s, v in N.items()])
p = float(np.mean([N[s]["fermi"]["p4_filtered"] for s in fin])); n = len(fin); neff = n / (1 + (n - 1) * 0.5)
txt = f"""# Ranked table — R5 (white-swan math and finalists)

**Staleness.** {CFG['staleness']}
Nothing comes from training knowledge. Only VERIFIED rows appear in this table.

**What kind of result this is.** Ten names reached the math; four clear both bars of the NO-TRADE test (LIFT ≥ 2.5x and positive EV) *and*
have a plausible ≥ 10x path. All four are the same kind of thing — cash-generative companies with heavy debt, down 92–94% — so they are
close to one bet, not four. Their lift sits exactly at the 2.5x bar on the Fermi mapping (range 0.6x–6.8x). The swan-ranking model failed
validation (see `cohort_report.md`); these ranks rest on measured base-rate tables and the validated wipeout model.

{hdr}
{chr(10).join(rows)}

{CFG['alloc_footer']}

## Fermi decomposition — measured base, filtered estimate, shown separately

Base factors measured on the cohort (retiring the 0.50 × 0.125 × 0.225 × 0.15 placeholders): survival {B['survival']:.3f} × theme wave {B['wave']:.4f} ×
leads {B['leads']:.3f} × captures {B['captures']:.3f} = **p4_base {p4b:.5f} (1-in-{1 / p4b:.0f})** for a ≥ 25x peak in common stock.

| Factor | Base | Filtered (these names) | Evidence | What would lower it |
|---|---|---|---|---|
| Survival | {B['survival']:.3f} | 0.51–0.53 | cohort: ≥ 90%-drawdown, cash-flow-positive names were listed standalone 5 years later 48.6% of the time (36.7% acquired, 16.3% dead); scaled by the wipeout model | a covenant waiver, a going-concern paragraph, loss of the anchor customer |
| Theme wave | {B['wave']:.4f} | 0.05 (score 2 of 5) | no theme; the "wave" is a re-rating of levered fallen leaders, which happened after the 2020 and 2022 troughs (measured: 101 and 124 names rose ≥ 25x trough-to-peak) and not in 2015–18 (11 names) | credit conditions tightening further; no trough inside the window |
| Leads | {B['leads']:.3f} | 0.55 | each is the largest or a leading operator in its niche per its own 10-K | franchise erosion showing in revenue |
| Captures | {B['captures']:.3f} | 0.68 | common stock; 60% of names that peaked ≥ 25x still held ≥ 10x at year 5, 77% held ≥ 5x; a written trim plan sits between | a capped takeout below the path; missing the trim |

Dependence caveat: these factors are NOT independent — a company that leads a forming wave is likelier to survive, raise cheap capital,
and be capturable — so the product is a rough skeleton, not a measurement. The range column recomputes with every factor at its
defensible low and high; a point estimate presented as precise would be a failure of this section.

Two cross-readings of the same names: the base-rate table puts their P(swan) at 2.1–2.6% (5–7x the base), and the cohort stratum they sit in
(≥ 90% drawdown, cash-flow-positive, n = 811) returned +2.30 per $1 on average and +0.63 with winners capped at 25x, with 17% going to zero —
but six of ten base years in the wider deep-drawdown stratum lost money.

## Scenario paths and EV, per finalist

{chr(10).join(scen(s) for s in fin)}

## All ten names that reached the math

{vsum.to_markdown(index=False)}

## Rejection log (R5 and the R3 names examined at filing level)

| Name | Stage failed | Reason |
|---|---|---|
""" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in CFG["rejections"]) + f"""

## Human–model cross-check (8.7)

Human rubric and Fermi were computed and written (`data/derived/r3_pool.parquet`, `r5_math.json`) without the model score as an input; the model
never receives a human score. Of the 113-name verified-eligible pool: 20 names had model top-quartile and human top-half standing (agree);
9 were model-top / human-bottom and 17 model-bottom / human-top — those 26 are excluded from the buy set as unresolved disagreements and
stay available to the shadow book only. For the finalists: EV signs agree, and P(zero) differs between the model and the value used by 5–7 points
(threshold 25). None is flagged FRAGILE.

## Coverage-ledger totals

14,177 securities enumerated → 1,930 universe → 1,723 pass Stage 1 (code) → 407 first-tier names with evidence packs (after the 29-name plausibility
pre-check) → 113 pass real business, ≥ 2 years runway or cash-positive, no going-concern language, cap $30M–$3B → 20 with model and rubric in
agreement → 15 read at filing level → 10 into the math → **{n} finalists**. Names not reached are unverified, not rejected: the first tier's other
294 names, tier 2 (299) and tier 3 (902) never received filing-level verification — a budget decision made on 2026-11-10 when the
5-hour limit ended the planned 25-batch swarm.

## Portfolio math (6.6)

The finalists share one wave-dependence cluster (levered cash-generative fallen leaders). With a within-cluster correlation of 0.5,
effective N = {n} ÷ (1 + {n - 1} × 0.5) = **{neff:.1f}**, not {n}. At the mean p4_filtered of {p:.4f}: P(at least one 25x+ hit by year 5) = 1 − (1 − {p:.4f})^{neff:.1f} =
**{1 - (1 - p) ** neff:.3f}**; expected hits = {neff * p:.3f}; expected non-swans = {neff * (1 - p):.2f} of {neff:.1f}. *(Footnote — naive, assumes independence, do not use:
1 − (1 − {p:.4f})^{n} = {1 - (1 - p) ** n:.3f}.)*

The most likely single outcome, by far, is that no position swans: the set's return is then decided by how many merely survive and re-rate
versus how many are restructured to zero, and because they share a cause, they are likely to do the same thing together.
Survivorship warning: QBTS is a survivor being reverse-engineered and is evidence of nothing about likelihood; the graveyard is the base case.
"""
(S / 'ranked_table.md').write_text(txt); print("ranked_table.md", len(txt))
