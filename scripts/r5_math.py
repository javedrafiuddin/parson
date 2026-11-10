"""R5: Section 6 math for the verified R3 survivors. Every probability traces to a measured cohort table, the validated
wipeout model, or a stated judgement mapping; every intermediate is written out. Output: ranked_table.md + r5_math.json"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah import ev as EV, rubric
from ah.config import DERIVED, STATE

# ---------- measured cohort tables (matured exact bases, both subsets; S2 merged/alive carried at 1.0x, bankrupt/dark at 0) ----------
Q = pd.read_parquet(DERIVED / "cohort_bases.parquet")
M = Q[Q.matured & Q.base_exact].copy()
s1 = M.subset == "S1_PRICED"
M["dd"] = np.where(s1, M.drawdown_3y, M.float_dd)
M["ddb"] = pd.cut(M.dd.fillna(0), [-10, 0.6, 0.8, 0.9, 1.01], labels=["<60", "60-80", "80-90", ">=90"]).astype(str)
ry = M.runway_years.replace(np.inf, 99)
M["runb"] = np.where(M.ocf_ttm > 0, "cashpos", np.where(ry >= 2, ">=2y", np.where(ry >= 0, "<2y", "unk")))
evn = M.s2_event
M["term"] = np.where(s1, M.term_5y, np.where(evn.isin(["BANKRUPTCY", "DARK_OR_DEREGISTERED"]), 0.0, 1.0))
M["alive"] = (s1 & (M.term_5y > 0.05)) | (~s1 & (evn == "STILL_FILING_UNPRICED"))
M["acq"] = ~s1 & (evn == "MERGED_OR_ACQUIRED")
M["dead"] = (s1 & (M.term_5y <= 0.05)) | (~s1 & evn.isin(["BANKRUPTCY", "DARK_OR_DEREGISTERED"]))
def strat(g):
    t = g.term
    z, mu, rr, sw = t < 0.1, (t >= 0.1) & (t < 3), (t >= 3) & (t < 10), t >= 10
    return dict(n=int(len(g)), p_zero=float(z.mean()), p_muddle=float(mu.mean()), p_rerate=float(rr.mean()), p_swan10=float(sw.mean()),
                p_peak25=float((g.mfe_5y >= 25).mean()), M_muddle=float(t[mu].mean()), M_rerate=float(t[rr].mean()) if rr.any() else 4.9,
                M_swan=float(t[sw].mean()) if sw.any() else np.nan, alive=float(g.alive.mean()), acq=float(g.acq.mean()), dead=float(g.dead.mean()),
                ev_mean=float(t.mean() - 1), ev_cap25=float(t.clip(upper=25).mean() - 1), median=float(t.median()))
ST = {k: strat(g) for k, g in M.groupby(["ddb", "runb"]) if len(g) >= 60}
ALL = strat(M)
WR = json.load(open(DERIVED / "wave_rates.json"))
BASE = {"survival": WR["survival"]["p_listed_standalone_5y"], "wave": WR["episodes"]["p_wave"],
        "leads": WR["episodes"]["p_leads_given_wave_alive_names"], "captures": WR["capture"]["p_term10_given_peak25"]}
WAVE = {0: 0.010, 1: BASE["wave"], 2: 0.05, 3: 0.08, 4: 0.11, 5: 0.131}     # 5 = best measured era (2020 bases); 1 = all-era measured rate
LEAD = {"leader": 0.55, "participant": 0.25, "laggard": 0.10, "n/a": BASE["leads"]}
CAPT = (0.60, 0.68, 0.77)   # common stock: hold-only measured (0.604) .. with a pre-written trim plan (>=5x kept: 0.771)

# ---------- verified inputs (from filings; accession numbers in the evidence column) ----------
N = [
 dict(sym="VRRM", name="Verra Mobility", px=2.13, hi=30.84, hi_d="2024-07-23", sh=152.0e6, extra=4.3e6, cash=140.1e6, debt=1032.6e6, due=9.5e6, ocf=251.7e6, rev=1003.9e6, run="cashpos",
      acc="10-Q filed 2026-10-30, 0001628280-26-068455", wave=2, lead="leader", cluster="levered cash-generative fallen leaders", kind="S",
      wave_line="No theme wave; stub re-rating if tolling/photo-enforcement cash flow holds. Analogue: 2022-25 levered fallen leaders (CVNA 129x in 37 months, measured)",
      cats="FY2026 10-K ~2027-02; NYCDOT contract status in each 10-Q", bear="NYCDOT (24.1% of Q3 revenue) and one of the three large Commercial Services customers (which gave, then withdrew, a termination notice in 2026) leave; $1.03B term loan (2032) then exceeds what the remaining cash flow supports",
      inval="Thesis is dead if FY2027 operating cash flow (10-K due by 2028-03-15) is below $100M, or NYCDOT is no longer a customer by then"),
 dict(sym="KLC", name="KinderCare Learning", px=2.33, hi=29.41, hi_d="2024-10-30", sh=118.5e6, extra=0.3e6, cash=173.7e6, debt=925.7e6, due=9.6e6, ocf=209.5e6, rev=2735.0e6, run="cashpos",
      acc="10-Q filed 2026-08-13, 0001193125-26-349480", wave=2, lead="leader", cluster="levered cash-generative fallen leaders", kind="S",
      wave_line="No theme wave; largest US child-care operator priced at 1.3x operating cash flow. Same stub-recovery analogue",
      cats="Q3 10-Q ~2026-11; FY2026 10-K ~2027-03", bear="Enrollment and subsidy funding fall; $407M operating loss (impairments) repeats; $926M debt against shrinking cash flow",
      inval="Thesis is dead if FY2027 operating cash flow (10-K due by 2028-03-31) is below $100M or a covenant waiver/default is disclosed before then"),
 dict(sym="ALIT", name="Alight", px=12.65, hi=206.40, hi_d="2024-03-21", sh=26.44e6, extra=0.3e6, cash=448.0e6, debt=1991.0e6, due=20.0e6, ocf=305.0e6, rev=2198.0e6, run="cashpos",
      acc="10-Q filed 2026-11-03, 0001628280-26-069567", wave=2, lead="leader", cluster="levered cash-generative fallen leaders", kind="S",
      wave_line="No theme wave; benefits-administration leader at ~1.1x operating cash flow after a reverse split approved 2026-06-10",
      cats="FY2026 10-K ~2027-02", bear="Client attrition to AI-native platforms; $1.99B debt; 1-for-20 reverse split effective 2026-06-30 and an 8-K item 3.01 listing notice in the last 12 months; TTM net loss $1.0B",
      inval="Thesis is dead if FY2027 revenue (10-K due by 2028-03-15) is below $1.7B or a covenant waiver/default is disclosed before then" ),
 dict(sym="FMC", name="FMC Corp", px=5.41, hi=67.53, hi_d="2024-05-10", sh=155.56e6, extra=3.4e6, cash=735.8e6, debt=4177.7e6, due=222.8e6, ocf=426.0e6, rev=2814.9e6, run="cashpos",
      acc="10-Q filed 2026-10-30, 0000037785-26-000171", wave=2, lead="leader", cluster="levered cash-generative fallen leaders", kind="S",
      wave_line="No theme wave; crop-protection cycle recovery. Equity is negative (-$19M) after $4.3B of TTM losses",
      cats="FY2026 10-K ~2027-02", bear="Negative book equity, $4.18B debt, covenant headroom after 8-K items 2.05/2.06 charges; a debt-for-equity exchange leaves holders a stub; revolver covenants were amended in April 2026",
      inval="Thesis is dead if a covenant waiver, default or debt exchange is disclosed, or FY2026 operating cash flow (10-K due by 2027-03-01) is negative" ),
 dict(sym="RXST", name="RxSight", px=4.86, hi=64.29, hi_d="2024-05-15", sh=41.93e6, extra=6.8e6, cash=254.7e6, debt=0.0, due=0.0, ocf=23.7e6, rev=115.3e6, run="cashpos", burn_override=18.0e6,
      acc="10-Q filed 2026-11-03, 0001193125-26-445381", wave=0, lead="n/a", cluster="net-cash single-product medtech", kind="N",
      wave_line="No wave case and no analogue claimed. Trades below cash + short-term investments ($254.7M vs $204M cap); floor value, not a theme",
      cats="FY2026 10-K ~2027-02", bear="LAL volumes keep falling (23,128 in Q3-2026 vs 26,045 a year earlier; 3 LDDs sold vs 25); cash is spent defending a shrinking franchise",
      inval="Thesis is dead if cash + short-term investments fall below $150M in any 10-Q/10-K filed by 2028-03-15"),
 dict(sym="FLNC", name="Fluence Energy", px=5.40, hi=32.23, hi_d="2026-02-03", sh=184.6e6, extra=19.0e6, cash=365.0e6, debt=400.0e6, due=0.0, ocf=-100.8e6, rev=2631.9e6, run=">=2y",
      acc="10-Q filed 2026-08-05, 0001868941-26-000029", wave=3, lead="leader", cluster="grid storage / power", kind="T",
      wave_line="Grid-scale storage: $2.6B revenue shows a real market; the energy/power cluster's leader basket rose 30x (2019-21) and 16x (2022-26), measured. Backlog figure not retrieved",
      cats="FY2026 10-K ~2026-11-25", bear="9% gross margin against Chinese integrators and Tesla; cash burn resumes; $400M 2030 converts (conversion ~$21) sit above the equity",
      inval="Thesis is dead if cash falls below $150M or going-concern language appears in any filing through the FY2027 10-K (due by 2027-12-15)", partial="convertible principal and backlog not re-traced to the note"),
 dict(sym="METC", name="Ramaco Resources", px=6.82, hi=54.55, hi_d="2025-10-14", sh=434.3e6/6.82, extra=345e6/32.0, cash=233.8e6, debt=453.6e6, due=0.0, ocf=-52.8e6, rev=544.5e6, run=">=2y",
      acc="10-Q filed 2026-11-03, 0001104659-26-122070", wave=3, lead="participant", cluster="critical minerals / coal", kind="T",
      wave_line="Critical-minerals onshoring had its wave in 2025 (this name's own high was 2025-10-14); a second wave is the claim. The 10-Q itself says reserves at Brook Mine are not established",
      cats="Brook Mine technical reports; FY2026 10-K ~2027-03", bear="Met-coal operations burn cash (-$52.8M TTM) under $453.6M of notes; Brook Mine never reaches reserves; share count not confirmed from the cover (COULD NOT VERIFY)",
      inval="Thesis is dead if no mineral reserve is reported for Brook Mine by 2028-12-31 and FY2027 operating cash flow is negative", partial="share count taken from market cap / price"),
 dict(sym="TE", name="T1 Energy", px=2.29, hi=12.04, hi_d="2026-06-02", sh=294.5e6, extra=24.6e6 + 345e6/6.0, cash=156.4e6, debt=583.4e6, due=51.6e6, ocf=3.9e6, rev=996.9e6, run="cashpos", burn_override=60e6,
      acc="10-Q filed 2026-08-12, 0001992243-26-000022", wave=2, lead="participant", cluster="US solar manufacturing", kind="T",
      wave_line="US solar onshoring is policy-made demand; one customer was 78% of sales (10-K). Six 8-K item 3.02 equity issuances and four resale prospectuses in 12 months",
      cats="Q3 10-Q ~2026-11", bear="Customer concentration, $583M debt incl. converts at ~$6, $189M capex with ~$4M operating cash flow: survives by issuing stock",
      inval="Thesis is dead if going-concern language appears or the largest customer is lost by the FY2027 10-K (due by 2028-03-31)"),
 dict(sym="ABAT", name="American Battery Technology", px=1.42, hi=11.33, hi_d="2025-10-14", sh=142.6e6, extra=13.0e6, cash=49.5e6, debt=8.0e6, due=8.0e6, ocf=-24.2e6, rev=21.7e6, run=">=2y",
      acc="10-K filed 2026-09-14, 0001493152-26-042497", wave=2, lead="participant", cluster="critical minerals / coal", kind="T",
      wave_line="Battery-materials recycling and a lithium claystone project; gross profit is negative (-$3.1M TTM). Funded by an ATM and a new S-3 (2026-09-18)",
      cats="Q1 FY2027 10-Q ~2026-11-14", bear="Two years of cash at the current burn, negative gross margin, ATM dilution; the 12-month liquidity statement is all management gives",
      inval="Thesis is dead if shares outstanding exceed 285M (2x) by the FY2028 10-K (due by 2028-09-30) or cash falls below 12 months of burn"),
 dict(sym="BLNK", name="Blink Charging", px=0.517, hi=4.44, hi_d="2023-11-15", sh=145.2e6, extra=11.6e6, cash=30.5e6, debt=0.0, due=0.0, ocf=-6.0e6, rev=96.5e6, run=">=2y",
      acc="10-Q filed 2026-11-05, 0001437749-26-035322", wave=2, lead="participant", cluster="EV charging", kind="T",
      wave_line="EV charging had its wave in 2020-21 (this name rose 27x then, measured). Revenue is down 38% from its 2024 peak",
      cats="Nasdaq bid-price cure deadline (two 8-K item 3.01 notices in 12 months)", bear="Sub-$1 price with a Nasdaq bid-price deficiency (reverse split likely), late 10-K (NT filed 2026-03-16), S-1 offering Dec 2025, new S-3 Oct 2026, ATM reactivated",
      inval="Thesis is dead if FY2026 revenue (10-K due by 2027-03-31) is below $80M or going-concern language appears"),
]
sc = pd.read_parquet(DERIVED / "baserate_scores.parquet").drop_duplicates("symbol").set_index("symbol")
rows, J = [], {}
for d in N:
    s = d["sym"]; r = sc.loc[s]
    dd = 1 - d["px"] / d["hi"]
    ddb = "<60" if dd < 0.6 else "60-80" if dd < 0.8 else "80-90" if dd < 0.9 else ">=90"
    S = ST.get((ddb, d["run"]), ALL)
    mcap = d["px"] * d["sh"]
    pz_model = float(r.p_zero); pz = 0.5 * (pz_model + S["dead"])          # human-set: mean of validated model and stratum wipeout rate
    # ---- Fermi: base (measured) vs filtered ----
    surv_f = min(0.95, S["alive"] * (1 - pz) / max(1 - S["dead"], 1e-9))
    filt = {"survival": surv_f, "wave": WAVE[d["wave"]], "leads": LEAD[d["lead"]], "captures": CAPT[1]}
    lo = {"survival": max(0.2, surv_f - 0.15), "wave": WAVE[max(d["wave"] - 1, 0)], "leads": max(0.10, LEAD[d["lead"]] - 0.15), "captures": CAPT[0]}
    hi = {"survival": min(0.97, surv_f + 0.10), "wave": WAVE[min(d["wave"] + 1, 5)], "leads": min(0.70, LEAD[d["lead"]] + 0.15), "captures": CAPT[2]}
    F = EV.fermi(filt, BASE, lo, hi)
    # ---- dilution trajectory (5.3) and the 25x/50x/190x paths (6.3) ----
    burn = d.get("burn_override", max(-d["ocf"], 0.0))
    traj = rubric.dilution_trajectory(d["sh"], d["px"], d["cash"], d["due"], burn, overhang_shares=d["extra"])
    sh5 = {m: traj[m][5] for m in traj}
    paths = {m: {"price": d["px"] * m, "cap_busd": d["px"] * m * sh5[10.0] / 1e9} for m in (25, 50, 190)}
    # ---- plausibility cap (6.3): 1.5x the 3-year-high price, diluted ----
    m_plaus = 1.5 * d["hi"] / d["px"] * (d["sh"] / sh5[10.0])
    m_swan = min(25.0, m_plaus)
    swan_class = m_plaus >= 10.0
    # ---- scenario table at 5 years ----
    p_sw = F["p4_filtered"]; p_rr = S["p_rerate"]; p_mu = 1 - pz - p_rr - p_sw
    probs = {"Zero": pz, "Muddle": p_mu, "Re-rate": p_rr, "White Swan": p_sw}
    dil5 = d["sh"] / sh5[1.0]                                              # per-share erosion on the flat path applies to Muddle
    pay = {"Zero": 0.0, "Muddle": S["M_muddle"] * min(1.0, dil5 + 0.15), "Re-rate": S["M_rerate"], "White Swan": m_swan}
    E = EV.ev(probs, pay)
    E50 = EV.ev(probs, {**pay, "White Swan": min(50.0, m_plaus)})["ev_per_dollar"]
    pathsY = {"Zero": (0.6, 0.2, 0.0), "Muddle": (0.9, 0.95, round(pay["Muddle"], 2)), "Re-rate": (1.1, 2.2, round(pay["Re-rate"], 1)), "White Swan": (1.2, round(m_swan ** 0.6, 1), round(m_swan, 1))}
    kelly_base = EV.kelly(EV.p4(BASE), m_swan); kelly_f = EV.kelly(p_sw, m_swan)
    J[s] = dict(d, dd=dd, stratum=[ddb, d["run"]], stratum_table=S, mcap=mcap, p_zero_model=pz_model, p_zero_used=pz, p_swan_table=float(r.p_swan_table), p_swan_table_range=[float(r.p_swan_min), float(r.p_swan_max)],
                rank_table=[float(r.rank_min), float(r.rank_max)], fragile=bool(r.FRAGILE), fermi=F, filtered=filt, low=lo, high=hi, traj=traj, paths=paths, m_plaus=m_plaus, m_swan=m_swan, swan_class=bool(swan_class),
                probs=probs, payoffs=pay, ev=E, ev_cap50=E50, scenario_paths=pathsY, kelly_base=kelly_base, kelly_filtered=kelly_f, runway_years=(None if burn == 0 else (d["cash"] - d["due"]) / burn))
json.dump({"base_factors": BASE, "wave_map": WAVE, "lead_map": LEAD, "capture_range": CAPT, "all_bases": ALL, "names": J}, open(DERIVED / "r5_math.json", "w"), indent=1, default=str)
pd.set_option("display.width", 250)
T = pd.DataFrame([{"sym": s, "dd": round(v["dd"], 3), "mcap_m": round(v["mcap"] / 1e6), "pz_model": round(v["p_zero_model"], 3), "pz_used": round(v["p_zero_used"], 3), "p4_base": round(v["fermi"]["p4_base"], 5),
                   "p4_f": round(v["fermi"]["p4_filtered"], 4), "lift": round(v["fermi"]["lift"], 1), "p4_lo": round(v["fermi"]["p4_low"], 4), "p4_hi": round(v["fermi"]["p4_high"], 4), "p_table": round(v["p_swan_table"], 4),
                   "M_plaus": round(v["m_plaus"], 1), "swan_class": v["swan_class"], "EV": round(v["ev"]["ev_per_dollar"], 3), "EV_cap50": round(v["ev_cap50"], 3), "kelly_f": round(v["kelly_filtered"], 4),
                   "sh5_flat/sh0": round(v["traj"][1.0][5] / v["sh"], 2), "cap25x_$B": round(v["paths"][25]["cap_busd"], 1)} for s, v in J.items()])
print(T.to_string(index=False))
print("base factors", {k: round(v, 4) for k, v in BASE.items()}, "p4_base", round(EV.p4(BASE), 5))
print({k: {kk: round(vv, 3) for kk, vv in v.items() if kk in ("n", "p_zero", "p_rerate", "p_swan10", "M_muddle", "M_rerate", "alive", "dead", "ev_mean", "ev_cap25")} for k, v in ST.items() if k[0] in ("80-90", ">=90")})
