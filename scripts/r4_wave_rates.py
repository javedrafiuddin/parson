"""Measured replacements for the Section 6.1 calibration placeholders, from the cohort.
Theme proxy = SIC-3 industry group; episode = (SIC-3, June base year) with >= 8 buyable bases (both subsets).
Wave formed  = the episode's leader basket (top quintile of names by 5y peak multiple, min 3 names) has a MEDIAN
               peak multiple >= 10x within 5 years.
Leads        = a name's own peak multiple >= half the leader basket's median peak multiple.
Writes data/derived/wave_rates.json"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah.config import DERIVED
from ah import model

Q = pd.read_parquet(DERIVED / "cohort_bases.parquet")
M = Q[Q.matured & Q.base_exact & (Q.base_date.dt.month == 6)].copy()
M["sic3"] = pd.to_numeric(M.sic, errors="coerce") // 10
M["year"] = M.base_date.dt.year
M["sector"] = M.sic.map(model.sector_of)
s1 = M.subset == "S1_PRICED"
out = {}
# ---- survival: listed standalone five years later ----
alive = (s1 & (M.cls != "GRAVEYARD")) | (~s1 & (M.s2_event == "STILL_FILING_UNPRICED"))
acq = ~s1 & (M.s2_event == "MERGED_OR_ACQUIRED")
dead = (s1 & (M.cls == "GRAVEYARD")) | (~s1 & M.s2_event.isin(["BANKRUPTCY", "DARK_OR_DEREGISTERED"]))
out["survival"] = {"n": int(len(M)), "p_listed_standalone_5y": float(alive.mean()), "p_acquired_or_merged_within_5y": float(acq.mean()),
                   "p_zero_bankrupt_dark_or_95pct_loss": float(dead.mean())}
M["alive"], M["acq"], M["dead"] = alive, acq, dead
dd = np.where(s1, M.drawdown_3y, M.float_dd)
M["dd_b"] = pd.cut(dd, [-10, 0.6, 0.8, 0.9, 1.01], labels=["<60%", "60-80%", "80-90%", ">=90%"])
ry = M.runway_years.replace(np.inf, 99)
M["run_b"] = pd.cut(ry.fillna(-1), [-1.5, -0.5, 1, 2, 98, 100], labels=["unknown", "<1y", "1-2y", ">2y", "cash-positive"])
out["survival_by_drawdown_runway"] = {f"{a}|{b}": {"n": int(len(g)), "alive": round(float(g.alive.mean()), 3), "acquired": round(float(g.acq.mean()), 3), "dead": round(float(g.dead.mean()), 3)}
                                     for (a, b), g in M.groupby(["dd_b", "run_b"], observed=True) if len(g) >= 40}
# ---- waves ----
ep = []
for (k, y), g in M.groupby(["sic3", "year"]):
    if len(g) < 8:
        continue
    p = g[g.subset == "S1_PRICED"].mfe_5y.dropna().sort_values(ascending=False)
    if len(p) < 3:
        continue
    nlead = max(3, int(np.ceil(0.2 * len(g))))
    basket = p.head(nlead)
    med = float(basket.median())
    wave = med >= 10
    leads = int((p >= 0.5 * med).sum()) if wave else 0
    ep.append({"sic3": int(k), "year": int(y), "n": int(len(g)), "n_priced": int(len(p)), "leader_median_peak": med, "leader_mean_peak": float(basket.mean()),
               "wave": bool(wave), "n_leaders": leads, "frac_lead": leads / len(g) if wave else np.nan,
               "frac_lead_among_alive": leads / max(int(g.alive.sum()), 1) if wave else np.nan})
E = pd.DataFrame(ep)
out["episodes"] = {"n_episodes": int(len(E)), "n_waves_median10x": int(E.wave.sum()), "p_wave": float(E.wave.mean()),
                   "n_waves_mean10x": int((E.leader_mean_peak >= 10).sum()), "p_wave_mean_def": float((E.leader_mean_peak >= 10).mean()),
                   "p_wave_by_year": E.groupby("year").wave.mean().round(3).to_dict(),
                   "distinct_sic3_with_any_wave": int(E[E.wave].sic3.nunique()), "distinct_sic3": int(E.sic3.nunique()),
                   "p_leads_given_wave_all_names": float(E[E.wave].n_leaders.sum() / E[E.wave].n.sum()) if E.wave.any() else None,
                   "p_leads_given_wave_alive_names": float(E[E.wave].frac_lead_among_alive.mean()) if E.wave.any() else None}
out["wave_episodes_list"] = E[E.wave].sort_values("leader_median_peak", ascending=False).head(40).to_dict("records")
# ---- holder capture for common stock: of names whose peak reached 25x, how many still held >= 10x at year 5 ----
pk = M[s1 & (M.mfe_5y >= 25)]
out["capture"] = {"n_peak25": int(len(pk)), "p_term10_given_peak25": float((pk.term_5y >= 10).mean()) if len(pk) else None,
                  "p_term5_given_peak25": float((pk.term_5y >= 5).mean()) if len(pk) else None,
                  "median_term_given_peak25": float(pk.term_5y.median()) if len(pk) else None}
# ---- direct stratum base rates (annual June bases, both subsets; S2 swans counted as zero => lower bound) ----
M["swan"] = (M.cls == "SWAN").astype(int)
M["peak25"] = (M.mfe_5y >= 25).fillna(False).astype(int)
M["mc_b"] = pd.cut(np.log10(M.mcap.clip(lower=1e5)), [0, 7.5, 8, 8.5, 9, 13], labels=["<$32M", "$32-100M", "$100-316M", "$316M-1B", ">$1B"])
def tab(by):
    g = M.groupby(by, observed=True).agg(n=("swan", "size"), swan=("swan", "sum"), peak25=("peak25", "sum"), dead=("dead", "mean"), alive=("alive", "mean"))
    g["swan_rate"] = g.swan / g.n
    g["peak25_rate"] = g.peak25 / g.n
    return {str(k): {kk: (round(float(vv), 4) if isinstance(vv, float) else int(vv)) for kk, vv in r.items()} for k, r in g.to_dict("index").items()}
out["base_rate_overall"] = {"n": int(len(M)), "swan": int(M.swan.sum()), "swan_rate": float(M.swan.mean()), "peak25_rate": float(M.peak25.mean()),
                            "possible_unpriced": int((M.cls == "POSSIBLE_SWAN_UNPRICED").sum())}
out["base_rate_by_drawdown"] = tab("dd_b")
out["base_rate_by_sector"] = tab("sector")
out["base_rate_by_mcap"] = tab("mc_b")
out["base_rate_by_dd_mcap"] = {f"{a}|{b}": v for (a, b), v in ((k, None) for k in [])}
g = M.groupby(["dd_b", "mc_b"], observed=True).agg(n=("swan", "size"), swan=("swan", "sum"), dead=("dead", "mean"))
out["base_rate_by_dd_mcap"] = {f"{a}|{b}": {"n": int(r.n), "swan": int(r.swan), "swan_rate": round(r.swan / r.n, 4), "dead": round(float(r.dead), 3)} for (a, b), r in g.iterrows() if r.n >= 30}
json.dump(out, open(DERIVED / "wave_rates.json", "w"), indent=1, default=str)
for k in ("survival", "episodes", "capture", "base_rate_overall", "base_rate_by_drawdown", "base_rate_by_sector", "base_rate_by_mcap", "base_rate_by_dd_mcap", "survival_by_drawdown_runway"):
    print(k, json.dumps(out[k], default=str)[:1500])
print(E[E.wave].sort_values("leader_median_peak", ascending=False).head(25).to_string())
