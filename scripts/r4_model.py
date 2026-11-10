"""R4: pre-flight class count -> purged walk-forward validation (model vs rubric vs random) -> final fit ->
score today's field -> sensitivity sweep (rank ranges, FRAGILE flags). Writes:
  data/derived/model_validation.json, model_scores.parquet, model_sweep.parquet"""
import sys, pathlib, json, hashlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from ah import cohort, labels, store, model, rubric
from ah.config import DERIVED, COHORT, RUN_ASOF

t0 = time.time()
OUT = {}
Q0 = pd.read_parquet(DERIVED / "cohort_bases.parquet")


def human_rubric(D):
    s1 = D.subset == "S1_PRICED"
    r = pd.DataFrame(index=D.index)
    r["n_tests"] = np.where(s1, D.t1_px.fillna(False).astype(int) + D.t2_px.fillna(False).astype(int) + D.t3_px.fillna(False).astype(int),
                            D.t1_fp.fillna(False).astype(int) + D.t2_fp.fillna(False).astype(int) + D.t3_fp.fillna(False).astype(int))
    r["dd"] = np.where(s1, D.drawdown_3y, D.float_dd)
    r["rev_ttm"] = D.rev_ttm
    r["rev_growth"] = D.rev_ttm / D.rev_ttm_prev.where(D.rev_ttm_prev > 1e5) - 1
    r["gross_margin"] = D.gp_ttm / D.rev_ttm.where(D.rev_ttm > 1e5)
    r["runway_years"] = D.runway_years.replace(np.inf, np.nan)
    r["cash_positive"] = D.ocf_ttm > 0
    r["debt_due_to_cash"] = D.debt_due_12m / D.cash_total.where(D.cash_total > 0)
    sr = D.shares / D.shares_prev.where(D.shares_prev > 0)
    r["reverse_split_12m"] = sr < 0.6
    r["share_growth_1y"] = (sr - 1).where(sr >= 0.6)
    r["overhang"] = D.antidil / D.shares.where(D.shares > 0)
    return rubric.rubric_score(r)["rubric"]


def relabel(Q, thr=25.0, H=5, cost_mult=1.0, possible_as_swan=False):
    """Re-derive classes under a perturbed configuration. Cost perturbation rescales the assumed half-spread."""
    Q = Q.copy()
    h0, h1 = 0.01, 0.01 * cost_mult
    for k in (1, 3, 4, 5, 6):
        Q[f"mfe_{k}y"] = Q[f"mfe_{k}y"] * (1 + h0) / (1 + h1)
        Q[f"term_{k}y"] = Q[f"term_{k}y"] * ((1 - h1) / (1 + h1)) / ((1 - h0) / (1 + h0))
    Q = cohort.classify_all(Q, H=H, swan_peak=thr)
    Q["y_swan"] = (Q.cls == "SWAN").astype(int)
    if possible_as_swan:
        Q.loc[Q.cls == "POSSIBLE_SWAN_UNPRICED", "y_swan"] = 1
    Q["y_zero"] = Q.cls.isin(["GRAVEYARD", "GRAVEYARD_BROAD"]).astype(int)
    return Q


def population(Q, month=6, possible_as_swan=False):
    M = Q[Q.matured & Q.base_exact & (Q.cls != "UNRESOLVED")]
    if month is not None:
        M = M[M.base_date.dt.month == month]
    if not possible_as_swan:
        M = M[M.cls != "POSSIBLE_SWAN_UNPRICED"]          # label unknown -> excluded, counted, reported
    return M.copy()


# ================= pre-flight class count (8.6) =================
Q = relabel(Q0)
allm = Q[Q.matured & Q.base_exact]
pf = {"matured_exact_name_dates": int(len(allm)), "by_subset": allm.subset.value_counts().to_dict(),
      "class_counts_name_dates": allm.groupby("subset").cls.value_counts().unstack(fill_value=0).to_dict("index"),
      "swan_25x_peak_name_dates": int((allm.mfe_5y >= 25).sum()), "swan_25x_peak_distinct_ciks": int(allm[allm.mfe_5y >= 25].cik.nunique()),
      "terminal_10x_name_dates": int((allm.term_5y >= 10).sum()), "terminal_10x_distinct_ciks": int(allm[allm.term_5y >= 10].cik.nunique()),
      "swan_union_name_dates": int((allm.cls == "SWAN").sum()), "swan_union_distinct_ciks": int(allm[allm.cls == "SWAN"].cik.nunique()),
      "graveyard_name_dates": int(allm.cls.isin(["GRAVEYARD", "GRAVEYARD_BROAD"]).sum()),
      "graveyard_distinct_ciks": int(allm[allm.cls.isin(["GRAVEYARD", "GRAVEYARD_BROAD"])].cik.nunique()),
      "possible_swan_unpriced_name_dates": int((allm.cls == "POSSIBLE_SWAN_UNPRICED").sum()),
      "possible_swan_unpriced_distinct_ciks": int(allm[allm.cls == "POSSIBLE_SWAN_UNPRICED"].cik.nunique()),
      "swan_ciks_by_base_year": allm[allm.cls == "SWAN"].groupby(allm.base_date.dt.year).cik.nunique().to_dict(),
      "swan_ciks_by_sic2_top": allm[allm.cls == "SWAN"].assign(s2=lambda d: pd.to_numeric(d.sic, errors="coerce") // 100).groupby("s2").cik.nunique().sort_values(ascending=False).head(12).to_dict()}
n = len(allm)
pf["true_base_rate_swan_lower"] = pf["swan_union_name_dates"] / n
pf["true_base_rate_swan_upper"] = (pf["swan_union_name_dates"] + pf["possible_swan_unpriced_name_dates"]) / n
pf["true_base_rate_25x_peak_lower"] = pf["swan_25x_peak_name_dates"] / n
pf["true_base_rate_graveyard"] = pf["graveyard_name_dates"] / n
pf["model_permitted"] = pf["swan_union_distinct_ciks"] >= COHORT["min_swan_positives_for_model"]
OUT["preflight"] = pf
print(json.dumps(pf, indent=1, default=str), flush=True)

# ================= validation (8.5): purged walk-forward, model vs rubric vs random =================
M = population(Q)
M["rubric"] = human_rubric(M)
X = model.features(M)
OUT["population_annual"] = {"n": int(len(M)), "swan": int(M.y_swan.sum()), "zero": int(M.y_zero.sum()),
                            "swan_ciks": int(M[M.y_swan == 1].cik.nunique()), "prevalence_swan": float(M.y_swan.mean()),
                            "prevalence_zero": float(M.y_zero.mean()), "by_year": M.groupby(M.base_date.dt.year).agg(n=("y_swan", "size"), swan=("y_swan", "sum"), zero=("y_zero", "sum")).to_dict("index")}
val = {}
P = population(Q, month=None)                 # training pool: every quarterly base (purged per fold)
P["rubric"] = human_rubric(P)
XP = model.features(P)
SHOW = ["test_year", "train_years", "train_pos", "train_pos_ciks", "n_test", "test_pos", "brier_model", "brier_clim", "logloss_model", "logloss_clim",
        "hits@50_model", "hits@50_rubric", "hits@50_rand_mean", "hits@50_rand_p95", "pval@50_vs_random", "skipped"]
def run(tag, Mtest, Xtest, pool, Xpool, target, H, mname):
    res, oof = model.walk_forward(Mtest, Xtest, target, model=mname, ks=(25, 50, 100), horizon_years=H, train_pool=pool, X_pool=Xpool)
    val[tag] = {"folds": res.to_dict("records"), "calibration": model.calibration_table(oof).to_dict("records") if len(oof) else []}
    print(f"\n== {tag} ==\n", res[[c for c in SHOW if c in res]].round(4).to_string(), flush=True)
# (A) FULLY PURGED, 5-year labels, 5-year purge
for target in ("y_swan", "y_zero"):
    for mname in ("enet", "gbm"):
        run(f"{target}_{mname}", M, X, P, XP, target, 5, mname)
# (B) PARTIALLY_PURGED proxy for the swan class: 3-year label horizon with a full 3-year purge.
#     The 5-year swan label cannot be validated at full purge inside a 2012-2026 window (see fold table A).
Q3 = relabel(Q0, H=3)
P3 = population(Q3, month=None); P3["rubric"] = human_rubric(P3); XP3 = model.features(P3)
M3 = P3[P3.base_date.dt.month == 6].copy(); X3 = XP3.loc[M3.index]
OUT["population_3y_annual"] = {"n": int(len(M3)), "swan3": int(M3.y_swan.sum()), "swan3_ciks": int(M3[M3.y_swan == 1].cik.nunique()),
                               "pool_n": int(len(P3)), "pool_swan3": int(P3.y_swan.sum()), "pool_swan3_ciks": int(P3[P3.y_swan == 1].cik.nunique())}
for mname in ("enet", "gbm"):
    run(f"PARTIALLY_PURGED_3y_swan_{mname}", M3, X3, P3, XP3, "y_swan", 3, mname)
OUT["validation"] = val


def verdict(v):
    f = [x for x in v["folds"] if x.get("brier_model") is not None and x.get("brier_model") == x.get("brier_model")]
    if not f:
        return {"folds": 0}
    return {"folds": len(f),
            "beats_rubric_p@50": int(sum(x["hits@50_model"] > x.get("hits@50_rubric", 0) for x in f)),
            "beats_random_p95_@50": int(sum(x["hits@50_model"] > x["hits@50_rand_p95"] for x in f)),
            "beats_climatology_brier": int(sum(x["brier_model"] < x["brier_clim"] for x in f)),
            "beats_climatology_logloss": int(sum(x["logloss_model"] < x["logloss_clim"] for x in f)),
            "rubric_beats_random_p95_@50": int(sum(x.get("hits@50_rubric", 0) > x["hits@50_rand_p95"] for x in f)),
            "total_hits@50_model": int(sum(x["hits@50_model"] for x in f)), "total_hits@50_rubric": int(sum(x.get("hits@50_rubric", 0) for x in f)),
            "total_hits@50_random_mean": float(sum(x["hits@50_rand_mean"] for x in f)),
            "folds_skipped_for_lack_of_training_positives": int(len(v["folds"]) - len(f))}
OUT["verdicts"] = {k: verdict(v) for k, v in val.items()}
print(json.dumps(OUT["verdicts"], indent=1), flush=True)

# ================= today's field, built by the same code path =================
asof = RUN_ASOF
prev = (pd.Timestamp(asof) - pd.DateOffset(years=1)).strftime("%Y-%m-%d")
Bc, _ = cohort.build([prev, asof], verbose=False)
Bc = cohort.postprocess(Bc, store.connect(), [prev, asof])
C = Bc[Bc.base_date == pd.Timestamp(asof)].copy()
st = pd.read_parquet(DERIVED / "stage1.parquet")
keep = st[st.stage1.str.startswith(("PASS", "NEEDS"))]
C = C[C.cik.isin(keep.cik)].drop_duplicates("cik").reset_index(drop=True)
Xc = model.features(C)
OUT["current_field"] = {"issuers_scored": int(len(C)), "stage1_survivor_issuers": int(keep.cik.nunique()),
                        "float_missing": int(C.float_usd.isna().sum())}


def fit_final(M, X, target, kind):
    pr = model.Prep().fit(X)
    Z = pr.transform(X)
    m = model.fit_enet(Z, M[target].astype(int)) if kind == "enet" else model.fit_gbm(Z, M[target].astype(int))
    return pr, m, float(M[target].mean())


def score(pr, m, prev_rate, Xn):
    Z = pr.transform(Xn)
    Z = Z.reindex(columns=pr.transform(Xn.iloc[:0]).columns, fill_value=0.0)
    return model.prior_correct(m.predict_proba(Z)[:, 1], prev_rate)


champ = {}
for target in ("y_swan", "y_zero"):
    ve, vg = OUT["verdicts"].get(f"{target}_enet", {}), OUT["verdicts"].get(f"{target}_gbm", {})
    # challenger promoted only if it beats the champion on purged OOS precision-at-top AND Brier
    promote = bool(vg.get("folds") and ve.get("folds") and vg["total_hits@50_model"] > ve["total_hits@50_model"]
                   and vg["beats_climatology_brier"] >= ve["beats_climatology_brier"])
    champ[target] = "gbm" if promote else "enet"
OUT["champion"] = champ
S = C[["cik", "ticker", "sec_name", "sic", "float_usd", "float_dd", "runway_years"]].copy()
models = {}
for target in ("y_swan", "y_zero"):
    pr, m, pv = fit_final(M, X, target, champ[target])
    models[target] = (pr, m, pv)
    S["p_" + target[2:]] = score(pr, m, pv, Xc)
    if champ[target] == "enet":
        lr = m.named_steps["logisticregression"]
        cols = pr.transform(X.iloc[:0]).columns
        co = pd.Series(lr.coef_[0], index=cols).sort_values(key=abs, ascending=False)
        OUT[f"coef_{target}"] = co[co != 0].round(4).head(25).to_dict()
S["rank_swan"] = S.p_swan.rank(ascending=False, method="min").astype(int)
vh = hashlib.sha1((json.dumps(sorted(X.columns.tolist())) + json.dumps(champ) + str(len(M)) + str(int(M.y_swan.sum()))).encode()).hexdigest()[:12]
OUT["model_version"] = f"ah-v3-{vh}"

# ================= sensitivity sweep (8.5): rank ranges =================
cfgs = {"median(25x,5y,1x cost,Jun)": dict(thr=25, H=5, cost_mult=1, month=6),
        "thr20": dict(thr=20, H=5, cost_mult=1, month=6), "thr35": dict(thr=35, H=5, cost_mult=1, month=6),
        "win4y": dict(thr=25, H=4, cost_mult=1, month=6), "win6y": dict(thr=25, H=6, cost_mult=1, month=6),
        "cost0.5x": dict(thr=25, H=5, cost_mult=0.5, month=6), "cost2x": dict(thr=25, H=5, cost_mult=2, month=6),
        "cadence_Mar": dict(thr=25, H=5, cost_mult=1, month=3), "cadence_Sep": dict(thr=25, H=5, cost_mult=1, month=9),
        "unpriced_possibles_as_swans": dict(thr=25, H=5, cost_mult=1, month=6, possible_as_swan=True)}
sw = pd.DataFrame({"cik": S.cik})
sw_meta = {}
for name, cf in cfgs.items():
    Qc = relabel(Q0, thr=cf["thr"], H=cf["H"], cost_mult=cf["cost_mult"], possible_as_swan=cf.get("possible_as_swan", False))
    Mc = population(Qc, month=cf["month"], possible_as_swan=cf.get("possible_as_swan", False))
    Xm = model.features(Mc)
    pr, m, pv = fit_final(Mc, Xm, "y_swan", champ["y_swan"])
    p = score(pr, m, pv, Xc)
    sw[name] = pd.Series(p).rank(ascending=False, method="min").astype(int).values
    sw["p|" + name] = p
    sw_meta[name] = {"n": int(len(Mc)), "swan": int(Mc.y_swan.sum()), "prevalence": pv}
rk = sw[list(cfgs)]
S["rank_min"], S["rank_max"], S["rank_median"] = rk.min(axis=1).values, rk.max(axis=1).values, rk.median(axis=1).values
nfield = len(S)
top = (rk <= max(1, int(0.10 * nfield)))
S["top_decile_share"] = top.mean(axis=1).values
S["FRAGILE"] = ((S.rank_max - S.rank_min) > 0.5 * nfield) | ((S.rank_median <= 0.10 * nfield) & (S.top_decile_share < 0.5))
S["p_swan_min"], S["p_swan_max"] = sw[[c for c in sw if c.startswith("p|")]].min(axis=1).values, sw[[c for c in sw if c.startswith("p|")]].max(axis=1).values
OUT["sweep"] = sw_meta
S["model_version"] = OUT["model_version"]
S.to_parquet(DERIVED / "model_scores.parquet", index=False)
sw.to_parquet(DERIVED / "model_sweep.parquet", index=False)
OUT["elapsed_s"] = round(time.time() - t0, 1)
json.dump(OUT, open(DERIVED / "model_validation.json", "w"), indent=1, default=str)
print("\nchampion", champ, OUT["model_version"], "field", nfield, "FRAGILE", int(S.FRAGILE.sum()))
print(S.sort_values("rank_median").head(25)[["ticker", "sec_name", "p_swan", "p_zero", "rank_swan", "rank_min", "rank_max", "FRAGILE"]].to_string())
