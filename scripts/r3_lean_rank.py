"""R3 lean pass (budget-scaled): read the 407 tier-1 evidence packs IN CODE for red-flag language, then order the
names by a transparent rubric so that filing-level verification is spent on a short list.
Writes data/derived/tier1_lean.parquet. Nothing here is 'verified'; flags are regex hits to be confirmed by reading."""
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah.config import DERIVED, DATA, STATE
from ah import rubric

B = pd.read_csv(STATE / "batches" / "tier1_batches.csv", keep_default_na=False)
st = pd.read_parquet(DERIVED / "stage1.parquet").drop_duplicates("symbol").set_index("symbol")
sc = pd.read_parquet(DERIVED / "baserate_scores.parquet").drop_duplicates("symbol").set_index("symbol")
rows = []
for s in B.symbol:
    p = DATA / "packs" / f"{s.replace('/', '_')}.md"
    t = p.read_text() if p.exists() else ""
    body = t.split("## Snippets", 1)[1] if "## Snippets" in t else ""
    gc = [m for m in re.finditer(r"\*\*going concern\*\*[^\n]*", body)]
    gc_real = [m.group(0) for m in gc if re.search(r"substantial doubt (about|regarding|as to|exists)|raise[s]? substantial doubt", m.group(0), re.I)
               and not re.search(r"(no|not|alleviat\w+|mitigat\w+|does not raise) substantial doubt|substantial doubt (was|has been) alleviated", m.group(0), re.I)]
    r = st.loc[s]
    rows.append({"symbol": s, "pack": bool(t), "no_10q": "## 10-Q: NOT RETRIEVED" in t, "no_10k": "## 10-K: NOT RETRIEVED" in t,
                 "gc_hits": len(gc), "gc_flag": len(gc_real) > 0, "toxic_flag": "**variable-price / toxic terms**" in body,
                 "atm_flag": "**ATM / equity distribution**" in body, "listing_flag": bool(re.search(r"\*\*listing deficiency / reverse split\*\*[^\n]*(minimum bid|deficien|notice from)", body, re.I)),
                 "conv_flag": "**convertible notes**" in body, "pref_flag": "**preferred stock**" in body})
L = pd.DataFrame(rows).set_index("symbol")
D = B.set_index("symbol").join(L).join(st[["name", "sic_desc", "last_close", "adv20", "mcap_mismatch", "rev_ttm", "rev_ttm_e", "cash_total", "debt_total", "debt_due_12m", "ocf_ttm", "runway_years",
                                           "cash_positive", "gp_ttm", "shares", "n_damage_tests", "real_business", "survival_gate", "rs_risk", "bk_or_despac", "ct_live", "ct_p3", "ct_conditions", "nt_12m", "auditor_change_12m"]])
D = D.join(sc[["dd_b", "mc_b", "sec_b", "run_b", "p_swan_min", "p_swan_max"]])
D["ry"] = D.runway_years.replace(np.inf, 99)
D["mcap"] = pd.to_numeric(D.mcap_musd, errors="coerce") * 1e6
D["net_cash"] = D.cash_total.fillna(0) - D.debt_total.fillna(0)
D["net_cash_to_mcap"] = D.net_cash / D.mcap
D["gm"] = D.gp_ttm / D.rev_ttm.where(D.rev_ttm > 0)
# 25x arithmetic: required market cap, and how it compares with the name's own 3-year-high cap (constant-share approximation)
D["cap_25x_busd"] = D.mcap * 25 / 1e9
D["x_of_own_peak_cap_at_25x"] = 25 * (1 - D.dd.astype(float))
# transparent ordering rubric (0-100): survival 40, real business 25, size/plausibility 20, clean structure 15
surv = np.select([D.cash_positive.fillna(False).astype(bool), D.ry >= 3, D.ry >= 2, D.ry >= 1.5, D.ry >= 1], [36, 40, 34, 22, 12], 0) - np.where(D.gc_flag, 15, 0)
biz = np.select([D.rev_ttm >= 100e6, D.rev_ttm >= 20e6, D.rev_ttm >= 5e6], [22, 18, 12], 0) + np.where(D.gm.fillna(0) > 0.3, 3, 0) \
    + np.where((D.rev_ttm.fillna(0) < 5e6) & (D.ct_live.fillna(0) >= 1), 10 + np.minimum(D.ct_conditions.fillna(0), 3) * 2, 0)
size = np.select([D.mcap < 30e6, D.mcap <= 320e6, D.mcap <= 1e9, D.mcap <= 3e9], [4, 20, 14, 8], 2)
clean = 15 - np.where(D.toxic_flag, 8, 0) - np.where(D.listing_flag | D.rs_risk.fillna(False).astype(bool), 4, 0) - np.where(D.mcap_mismatch.fillna(False).astype(bool), 3, 0)
D["o_surv"], D["o_biz"], D["o_size"], D["o_clean"] = surv, biz, size, clean
D["order_score"] = surv + biz + size + clean
D.reset_index().to_parquet(DERIVED / "tier1_lean.parquet", index=False)
print("names", len(D), "| packs", int(D.pack.sum()), "| 10-Q missing", int(D.no_10q.sum()), "| going-concern language", int(D.gc_flag.sum()),
      "| toxic-term hits", int(D.toxic_flag.sum()), "| ATM hits", int(D.atm_flag.sum()), "| listing-deficiency hits", int(D.listing_flag.sum()))
print("gate counts: rev>=5M", int((D.rev_ttm >= 5e6).sum()), "| runway>=2y or cash+", int(((D.ry >= 2)).sum()), "| both", int(((D.ry >= 2) & (D.rev_ttm >= 5e6)).sum()),
      "| both & cap 30M-3B & no going-concern", int(((D.ry >= 2) & (D.rev_ttm >= 5e6) & D.mcap.between(3e7, 3e9) & ~D.gc_flag).sum()))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 26)
T = D.sort_values("order_score", ascending=False).head(70).copy()
T["nm"] = T.name.str.slice(0, 24); T["mc"] = (T.mcap / 1e6).round(0); T["rev"] = (T.rev_ttm / 1e6).round(0); T["nc/mc"] = T.net_cash_to_mcap.round(2); T["ry"] = T.ry.round(1); T["pz"] = pd.to_numeric(T.p_zero, errors="coerce").round(2)
T["fl"] = np.where(T.gc_flag, "G", "") + np.where(T.toxic_flag, "T", "") + np.where(T.atm_flag, "A", "") + np.where(T.listing_flag, "L", "") + np.where(T.conv_flag, "C", "")
print(T[["nm", "topic", "dd", "mc", "rev", "ry", "nc/mc", "pz", "fl", "order_score"]].to_string())
