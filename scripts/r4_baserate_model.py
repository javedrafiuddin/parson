"""R4 degradation path (8.6): base-rate-table model for P(swan).
A pre-specified, UNWEIGHTED logistic on four categorical rubric variables only (drawdown bucket, size bucket,
sector group, runway bucket). No class weights -> probabilities sit at true population prevalence by construction.
Validated in the same purged walk-forward against climatology, the rubric and random selection.
Writes data/derived/baserate_validation.json, baserate_scores.parquet"""
import sys, pathlib, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from ah import cohort, model, rubric, store
from ah.config import DERIVED, RUN_ASOF
import importlib.util
spec = importlib.util.spec_from_file_location("r4m", str(pathlib.Path(__file__).parent / "r4_model.py"))

Q0 = pd.read_parquet(DERIVED / "cohort_bases.parquet")
HI = {"biopharma": "biopharma", "energy_mining": "energy_hw", "hardware_semis": "energy_hw"}


def strata(D, current=False):
    s1 = (D.subset == "S1_PRICED") if "subset" in D else pd.Series(True, index=D.index)
    dd = np.where(s1, D.drawdown_3y, D.float_dd) if not current else D.dd
    mc = D.mcap
    ry = D.runway_years.replace(np.inf, 99)
    cp = (D.ocf_ttm > 0)
    S = pd.DataFrame(index=D.index)
    S["dd_b"] = pd.cut(pd.Series(dd, index=D.index).fillna(0.0), [-10, 0.6, 0.8, 0.9, 1.01], labels=["dd<60", "dd60-80", "dd80-90", "dd>=90"]).astype(str)
    S["mc_b"] = pd.cut(np.log10(mc.clip(lower=1e5)).fillna(8.75), [0, 7.5, 8, 8.5, 9, 13], labels=["mc<32M", "mc32-100M", "mc100-316M", "mc316M-1B", "mc>1B"]).astype(str)
    S["sec_b"] = D.sic.map(model.sector_of).map(HI).fillna("other")
    S["run_b"] = np.where(cp, "cashpos", np.where(ry >= 2, "run>=2y", np.where(ry >= 0, "run<2y", "run_unknown")))
    return S


def design(S, cols=None):
    X = pd.get_dummies(S, drop_first=False).astype(float)
    if cols is not None:
        X = X.reindex(columns=cols, fill_value=0.0)
    return X


def fit(S, y):
    X = design(S)
    m = LogisticRegression(C=0.5, max_iter=2000)
    m.fit(X, y)
    return m, X.columns


def relabel(Q, thr=25.0, H=5, cost_mult=1.0, possible_as_swan=False):
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
    P = Q[Q.matured & Q.base_exact & (Q.cls != "UNRESOLVED")]
    if not possible_as_swan:
        P = P[P.cls != "POSSIBLE_SWAN_UNPRICED"]
    return P.copy()


def wf(P, H, test_years, month=6, k=50, min_pos=8):
    P = P.assign(byear=P.base_date.dt.year)
    S = strata(P)
    rows = []
    for ty in test_years:
        te = P[(P.byear == ty) & (P.base_date.dt.month == month)]
        if not len(te):
            continue
        t0 = te.base_date.min()
        tr = P[P.base_date + pd.Timedelta(days=int(365.25 * H) + 15) < t0]
        if tr.y_swan.sum() < min_pos:
            rows.append({"test_year": ty, "skipped": f"train positives {int(tr.y_swan.sum())} (< {min_pos}); test positives {int(te.y_swan.sum())}"})
            continue
        m, cols = fit(S.loc[tr.index], tr.y_swan)
        p = m.predict_proba(design(S.loc[te.index], cols))[:, 1]
        y = te.y_swan.to_numpy()
        clim = np.full(len(y), tr.y_swan.mean())
        rb = human_rubric(te).to_numpy()
        r = {"test_year": ty, "train_pos": int(tr.y_swan.sum()), "train_pos_ciks": int(tr[tr.y_swan == 1].cik.nunique()), "n_test": len(te), "test_pos": int(y.sum()),
             "brier_model": brier_score_loss(y, p), "brier_clim": brier_score_loss(y, clim),
             "logloss_model": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]), "logloss_clim": log_loss(y, np.clip(clim, 1e-6, 1 - 1e-6), labels=[0, 1]),
             "mean_p": float(p.mean()), "base_rate_test": float(y.mean())}
        for kk in (k, 2 * k):
            hm = model.precision_at(y, p + 1e-9 * np.random.default_rng(0).random(len(p)), kk)[1]
            hr = model.precision_at(y, rb, kk)[1]
            rnd = model.random_benchmark(y, kk)
            r.update({f"hits@{kk}_model": hm, f"hits@{kk}_rubric": hr, f"hits@{kk}_rand_mean": float(rnd.mean()), f"hits@{kk}_rand_p95": float(np.percentile(rnd, 95)),
                      f"pval@{kk}": float((rnd >= hm).mean())})
        rows.append(r)
    return pd.DataFrame(rows)


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


OUT = {}
P5 = relabel(Q0)
A = wf(P5, 5, [2018, 2019, 2020, 2021])
P3 = relabel(Q0, H=3)
B = wf(P3, 3, list(range(2016, 2024)))
show = ["test_year", "train_pos", "n_test", "test_pos", "brier_model", "brier_clim", "logloss_model", "logloss_clim", "hits@50_model", "hits@50_rubric", "hits@50_rand_mean", "hits@50_rand_p95", "pval@50", "hits@100_model", "hits@100_rubric", "hits@100_rand_mean", "pval@100", "skipped"]
pd.set_option("display.width", 260)
print("== FULLY PURGED 5y ==\n", A[[c for c in show if c in A]].round(4).to_string())
print("== PARTIALLY_PURGED 3y ==\n", B[[c for c in show if c in B]].round(4).to_string())


def verdict(R):
    f = R[R.get("brier_model").notna()] if "brier_model" in R else R.iloc[0:0]
    if not len(f):
        return {"folds": 0, "skipped": int(len(R))}
    return {"folds": int(len(f)), "skipped": int(len(R) - len(f)),
            "beats_climatology_brier": int((f.brier_model < f.brier_clim).sum()), "beats_climatology_logloss": int((f.logloss_model < f.logloss_clim).sum()),
            "beats_rubric_hits@50": int((f["hits@50_model"] > f["hits@50_rubric"]).sum()), "beats_random_p95_hits@50": int((f["hits@50_model"] > f["hits@50_rand_p95"]).sum()),
            "beats_rubric_hits@100": int((f["hits@100_model"] > f["hits@100_rubric"]).sum()), "beats_random_p95_hits@100": int((f["hits@100_model"] > f["hits@100_rand_p95"]).sum()),
            "total_hits@50": {"model": int(f["hits@50_model"].sum()), "rubric": int(f["hits@50_rubric"].sum()), "random_mean": round(float(f["hits@50_rand_mean"].sum()), 2)},
            "total_hits@100": {"model": int(f["hits@100_model"].sum()), "rubric": int(f["hits@100_rubric"].sum()), "random_mean": round(float(f["hits@100_rand_mean"].sum()), 2)}}
OUT["fully_purged_5y"] = {"folds": A.to_dict("records"), "verdict": verdict(A)}
OUT["partially_purged_3y"] = {"folds": B.to_dict("records"), "verdict": verdict(B)}
print(json.dumps({k: v["verdict"] for k, v in OUT.items()}, indent=1))

# ---- final table model on all matured quarterly bases; coefficients as odds multipliers ----
m, cols = fit(strata(P5), P5.y_swan)
OUT["final"] = {"n": int(len(P5)), "swan": int(P5.y_swan.sum()), "prevalence": float(P5.y_swan.mean()),
                "odds_multipliers": {c: round(float(np.exp(b)), 3) for c, b in zip(cols, m.coef_[0])}, "intercept": float(m.intercept_[0])}
print(json.dumps(OUT["final"], indent=1))

# ---- today's field ----
st = pd.read_parquet(DERIVED / "stage1.parquet")
k = st[st.stage1.str.startswith(("PASS", "NEEDS")) & st.sec_type.isin(["common", "adr", "otc_common"])].sort_values("adv20", ascending=False).drop_duplicates("cik").copy()
Sc = strata(k, current=True)
k["p_swan_table"] = m.predict_proba(design(Sc, cols))[:, 1]
k = pd.concat([k, Sc], axis=1)
cfgs = {"median": dict(), "thr20": dict(thr=20), "thr35": dict(thr=35), "win4y": dict(H=4), "win6y": dict(H=6), "cost0.5x": dict(cost_mult=0.5), "cost2x": dict(cost_mult=2),
        "cadence_MarSep_only": dict(), "cadence_JunDec_only": dict(), "unpriced_possibles_as_swans": dict(possible_as_swan=True)}
ranks, probs, meta = {}, {}, {}
for name, cf in cfgs.items():
    Pc = relabel(Q0, **cf)
    if name == "cadence_MarSep_only":
        Pc = Pc[Pc.base_date.dt.month.isin([3, 9])]
    if name == "cadence_JunDec_only":
        Pc = Pc[Pc.base_date.dt.month.isin([6, 12])]
    mc_, cc = fit(strata(Pc), Pc.y_swan)
    p = mc_.predict_proba(design(Sc, cc))[:, 1]
    probs[name] = p
    ranks[name] = pd.Series(p, index=k.index).rank(ascending=False, method="average")
    meta[name] = {"n": int(len(Pc)), "swan": int(Pc.y_swan.sum()), "prevalence": float(Pc.y_swan.mean())}
R = pd.DataFrame(ranks)
PR = pd.DataFrame(probs, index=k.index)
k["rank_table_median_cfg"] = R["median"]
k["rank_min"], k["rank_max"] = R.min(axis=1), R.max(axis=1)
k["p_swan_min"], k["p_swan_max"] = PR.min(axis=1), PR.max(axis=1)
n = len(k)
k["FRAGILE"] = (k.rank_max - k.rank_min) > 0.5 * n
OUT["sweep"] = meta
OUT["field"] = {"n": int(n), "fragile": int(k.FRAGILE.sum()), "p_swan_table_quantiles": k.p_swan_table.quantile([0.1, 0.5, 0.9, 0.99, 1.0]).round(5).to_dict()}
ms = pd.read_parquet(DERIVED / "model_scores.parquet")[["cik", "p_zero", "p_swan", "FRAGILE", "model_version"]].rename(columns={"p_swan": "p_swan_enet_RETIRED", "FRAGILE": "enet_fragile"})
k = k.merge(ms, on="cik", how="left")
k.to_parquet(DERIVED / "baserate_scores.parquet", index=False)
json.dump(OUT, open(DERIVED / "baserate_validation.json", "w"), indent=1, default=str)
print(json.dumps(OUT["field"]), json.dumps(meta)[:600])
print(k.sort_values("p_swan_table", ascending=False).head(12)[["symbol", "dd_b", "mc_b", "sec_b", "run_b", "p_swan_table", "p_swan_min", "p_swan_max", "p_zero", "rank_min", "rank_max", "FRAGILE"]].to_string())
