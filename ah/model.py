"""Section 8.4-8.6: survivorship-safe feature builder, purged walk-forward validation, elastic-net champion,
shallow GBM challenger, calibration with true-prevalence correction, sensitivity sweep.

SURVIVORSHIP-SAFE means: every feature is built from EDGAR filings only (XBRL values + filing index), by the
same code path for names that are alive today and names that died. No price-derived feature enters the model,
because price history exists only for survivors and its presence would leak the outcome."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import brier_score_loss, log_loss

SECTORS = {
    "biopharma": [(2833, 2836), (8731, 8734)], "medtech": [(3841, 3851), (8000, 8099)],
    "software_it": [(7370, 7379)], "hardware_semis": [(3570, 3579), (3660, 3699), (3810, 3829)],
    "energy_mining": [(1000, 1499), (2900, 2999), (4900, 4991)], "financial": [(6000, 6799)],
    "consumer": [(2000, 2399), (5000, 5999), (7000, 7299), (7800, 7999)],
    "industrial_transport": [(1500, 1799), (2400, 2832), (3000, 3569), (3580, 3659), (3700, 3799), (4000, 4899)],
}


def sector_of(sic):
    try:
        s = int(sic)
    except Exception:
        return "other"
    for k, rs in SECTORS.items():
        if any(a <= s <= b for a, b in rs):
            return k
    return "other"


NUM = ["log_mcap", "ev_rev", "mcap_to_cash", "float_dd", "runway", "debt_due_to_cash", "current_ratio", "log_rev",
       "rev_growth", "gross_margin", "rd_to_rev", "ni_margin", "share_growth_1y", "overhang", "auth_headroom",
       "issuance_rate", "liab_to_assets", "sic2_float_growth", "sic2_frac_up20", "sic2_rev_growth", "sic2_log_n"]
FLAG = ["cash_positive", "has_rev", "reverse_split_12m", "neg_equity", "offering_doc_90d", "nt_12m", "has_conv_debt"]


def features(B):
    """B: bases (historical or current) carrying the pit.asof_panel columns + float proxy + prior-year joins."""
    X = pd.DataFrame(index=B.index)
    mc = B.mcap_float.where(B.mcap_float > 0)
    X["log_mcap"] = np.log10(mc)
    X["ev_rev"] = B.ev_rev_fp.clip(-5, 60)
    X["mcap_to_cash"] = (mc / B.cash_total.where(B.cash_total > 0)).clip(0, 200)
    X["float_dd"] = B.float_dd.clip(-3, 1)
    X["runway"] = B.runway_years.replace(np.inf, np.nan).clip(0, 10)
    X["cash_positive"] = (B.ocf_ttm > 0).astype(float)
    X.loc[X.cash_positive == 1, "runway"] = 10.0
    X["debt_due_to_cash"] = (B.debt_due_12m / B.cash_total.where(B.cash_total > 0)).clip(0, 20)
    X["current_ratio"] = (B.AssetsCurrent / B.LiabilitiesCurrent.where(B.LiabilitiesCurrent > 0)).clip(0, 25)
    X["has_rev"] = (B.rev_ttm > 1e5).astype(float)
    X["log_rev"] = np.log10(B.rev_ttm.clip(lower=1e4)).where(B.rev_ttm > 0)
    X["rev_growth"] = (B.rev_ttm / B.rev_ttm_prev.where(B.rev_ttm_prev > 1e5) - 1).clip(-1, 5)
    X["gross_margin"] = (B.gp_ttm / B.rev_ttm.where(B.rev_ttm > 1e5)).clip(-3, 1)
    X["rd_to_rev"] = (B.rd_ttm / B.rev_ttm.where(B.rev_ttm > 1e5)).clip(0, 10)
    X["ni_margin"] = (B.ni_ttm / B.rev_ttm.where(B.rev_ttm > 1e5)).clip(-20, 2)
    sr = B.shares / B.shares_prev.where(B.shares_prev > 0)
    X["reverse_split_12m"] = (sr < 0.6).astype(float)
    X["share_growth_1y"] = (sr - 1).where(sr >= 0.6).clip(-0.4, 10)
    X["overhang"] = (B.antidil / B.shares.where(B.shares > 0)).clip(0, 5)
    X["auth_headroom"] = (1 - B.shares / B.CommonStockSharesAuthorized.where(B.CommonStockSharesAuthorized > 0)).clip(-1, 1)
    X["issuance_rate"] = (B.iss_ttm / mc).clip(0, 5)
    X["neg_equity"] = (B.StockholdersEquity < 0).astype(float)
    X["liab_to_assets"] = (B.Liabilities / B.Assets.where(B.Assets > 0)).clip(0, 5)
    X["offering_doc_90d"] = B.offering_doc_90d.fillna(0).astype(float)
    X["nt_12m"] = B.nt_12m_flag.fillna(0).astype(float)
    X["has_conv_debt"] = (B.conv_debt > 0).astype(float)
    for k in ("sic2_float_growth", "sic2_frac_up20", "sic2_rev_growth", "sic2_log_n"):
        X[k] = B[k] if k in B else np.nan
    sec = B.sic.map(sector_of)
    for k in list(SECTORS) :
        X["sec_" + k] = (sec == k).astype(float)
    return X


def sector_context(B):
    """Wave-context features built ONLY from filings (survivorship-free): per (base_date, SIC-2) aggregate
    public-float growth, share of peers whose float rose > 20% y/y, aggregate revenue growth, peer count.
    Uses every active filer at the base date, dead or alive. All inputs were filed before the base date."""
    d = B[["cik", "base_date", "sic", "float_usd", "float_prev", "rev_ttm", "rev_ttm_prev"]].copy()
    d["sic2"] = (pd.to_numeric(d.sic, errors="coerce") // 100)
    ok = d.float_usd.notna() & d.float_prev.notna() & (d.float_prev > 0)
    g = d[ok].groupby(["base_date", "sic2"])
    a = pd.DataFrame({"sic2_float_growth": (g.float_usd.sum() / g.float_prev.sum() - 1).clip(-1, 5),
                      "sic2_frac_up20": g.apply(lambda x: ((x.float_usd / x.float_prev) > 1.2).mean()),
                      "sic2_log_n": np.log10(g.size())})
    okr = d.rev_ttm.notna() & d.rev_ttm_prev.notna() & (d.rev_ttm_prev > 0)
    gr = d[okr].groupby(["base_date", "sic2"])
    a["sic2_rev_growth"] = (gr.rev_ttm.sum() / gr.rev_ttm_prev.sum() - 1).clip(-1, 5)
    d = d.merge(a.reset_index(), on=["base_date", "sic2"], how="left")
    return d[["sic2_float_growth", "sic2_frac_up20", "sic2_rev_growth", "sic2_log_n"]].set_index(B.index)


class Prep:
    """Median imputation + missing indicators fitted on TRAIN only."""
    def fit(self, X):
        self.med = X.median(numeric_only=True)
        self.miss = [c for c in NUM if c in X and X[c].isna().mean() > 0.02]
        return self

    def transform(self, X):
        Z = X.copy()
        for c in self.miss:
            Z["miss_" + c] = Z[c].isna().astype(float)
        return Z.fillna(self.med).fillna(0.0)


def case_control(X, y, max_neg=12000, seed=0):
    """Keep every positive and a seeded random sample of negatives (8.2 ii allows case-control FITTING; every
    probability is re-anchored to the true prevalence afterwards by prior_correct)."""
    y = np.asarray(y)
    neg = np.flatnonzero(y == 0)
    if len(neg) <= max_neg:
        return X, y
    r = np.random.default_rng(seed)
    keep = np.sort(np.concatenate([np.flatnonzero(y == 1), r.choice(neg, size=max_neg, replace=False)]))
    return X.iloc[keep], y[keep]


def fit_enet(X, y, w=None, C=0.05, l1_ratio=0.5, seed=0):
    X, y = case_control(X, y, seed=seed)
    w = None
    m = make_pipeline(StandardScaler(), LogisticRegression(solver="saga", C=C, l1_ratio=l1_ratio,
                                                           class_weight="balanced", max_iter=3000, tol=2e-3, random_state=seed))
    m.fit(X, y, logisticregression__sample_weight=w)
    return m


def fit_gbm(X, y, w=None, seed=0):
    import lightgbm as lgb
    X, y = case_control(X, y, seed=seed)
    y = pd.Series(y)
    w = None
    pos = max(y.sum(), 1)
    m = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.02, max_depth=2, num_leaves=4, min_child_samples=40,
                           min_child_weight=5.0, subsample=0.7, subsample_freq=1, colsample_bytree=0.7, reg_lambda=10.0,
                           scale_pos_weight=(len(y) - pos) / pos, random_state=seed, verbose=-1)
    m.fit(X, y, sample_weight=w)
    return m


def prior_correct(p_bal, prevalence, train_share=0.5):
    """Model fitted with balanced class weights sees an effective 50% prevalence. Shift the logit back to the
    TRUE population prevalence (8.2 ii). A probability quoted off the resampled distribution is forbidden."""
    p = np.clip(p_bal, 1e-9, 1 - 1e-9)
    lo = np.log(p / (1 - p)) - np.log(train_share / (1 - train_share)) + np.log(prevalence / (1 - prevalence))
    return 1 / (1 + np.exp(-lo))


def precision_at(y, score, k):
    idx = np.argsort(-np.asarray(score))[:k]
    return float(np.asarray(y)[idx].mean()), int(np.asarray(y)[idx].sum())


def random_benchmark(y, k, draws=1000, seed=0):
    r = np.random.default_rng(seed)
    y = np.asarray(y)
    hits = np.array([y[r.choice(len(y), size=min(k, len(y)), replace=False)].sum() for _ in range(draws)])
    return hits


def walk_forward(D, X, ycol, rubric_col="rubric", horizon_years=5, test_years=None, model="enet", ks=(25, 50, 100),
                 train_pool=None, X_pool=None, min_train_pos=8):
    """Expanding-window purged walk-forward. Train = bases whose label window closed before the test year's first
    base date (purge), test = bases of one calendar year. Because training never uses bases after the test block,
    the post-test embargo is satisfied by construction. Returns per-fold metrics + out-of-fold predictions."""
    D = D.copy()
    D["byear"] = pd.to_datetime(D.base_date).dt.year
    years = sorted(D.byear.unique())
    y0 = years[0] if train_pool is None else int(pd.to_datetime(train_pool.base_date).dt.year.min())
    test_years = test_years or [y for y in years if y - horizon_years - 1 >= y0]
    rows, oof = [], []
    for ty in test_years:
        t0 = pd.to_datetime(D.loc[D.byear == ty, "base_date"]).min()
        TP, XP = (D, X) if train_pool is None else (train_pool, X_pool)
        tr = TP[pd.to_datetime(TP.base_date) + pd.Timedelta(days=int(365.25 * horizon_years) + 15) < t0]
        tr = tr.assign(byear=pd.to_datetime(tr.base_date).dt.year)
        te = D[D.byear == ty]
        if tr[ycol].sum() < min_train_pos or len(te) < 50:
            rows.append({"test_year": ty, "skipped": f"train positives {int(tr[ycol].sum())} (< {min_train_pos}), test n {len(te)}, test positives {int(te[ycol].sum())}"})
            continue
        pr = Prep().fit(XP.loc[tr.index])
        Xtr, Xte = pr.transform(XP.loc[tr.index]), pr.transform(X.loc[te.index])
        Xte = Xte.reindex(columns=Xtr.columns, fill_value=0.0)
        m = fit_enet(Xtr, tr[ycol].astype(int)) if model == "enet" else fit_gbm(Xtr, tr[ycol].astype(int))
        pbal = m.predict_proba(Xte)[:, 1]
        prev = tr[ycol].mean()                                    # climatology known at training time
        p = prior_correct(pbal, prev) if model == "enet" else np.clip(pbal * 0 + pbal, 1e-9, 1 - 1e-9)
        if model != "enet":                                       # GBM used scale_pos_weight -> same correction
            p = prior_correct(pbal, prev)
        y = te[ycol].astype(int).to_numpy()
        clim = np.full(len(y), prev)
        r = {"test_year": ty, "train_years": f"{tr.byear.min()}-{tr.byear.max()}", "n_train": len(tr), "train_pos": int(tr[ycol].sum()),
             "train_pos_ciks": int(tr[tr[ycol] == 1].cik.nunique()),
             "n_test": len(te), "test_pos": int(y.sum()), "test_base_rate": float(y.mean()),
             "brier_model": brier_score_loss(y, p), "brier_clim": brier_score_loss(y, clim),
             "logloss_model": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]),
             "logloss_clim": log_loss(y, np.clip(clim, 1e-6, 1 - 1e-6), labels=[0, 1])}
        for k in ks:
            k_ = min(k, len(te))
            r[f"p@{k}_model"], r[f"hits@{k}_model"] = precision_at(y, p, k_)
            if rubric_col in te:
                r[f"p@{k}_rubric"], r[f"hits@{k}_rubric"] = precision_at(y, te[rubric_col].to_numpy(), k_)
            rb = random_benchmark(y, k_)
            r[f"hits@{k}_rand_mean"], r[f"hits@{k}_rand_p95"] = float(rb.mean()), float(np.percentile(rb, 95))
            r[f"pval@{k}_vs_random"] = float((rb >= r[f"hits@{k}_model"]).mean())
        rows.append(r)
        oof.append(pd.DataFrame({"idx": te.index, "p": p, "y": y, "test_year": ty}))
    return pd.DataFrame(rows), (pd.concat(oof, ignore_index=True) if oof else pd.DataFrame())


def calibration_table(oof, bins=10):
    if oof.empty:
        return pd.DataFrame()
    q = pd.qcut(oof.p.rank(method="first"), bins, labels=False)
    return oof.groupby(q).agg(n=("y", "size"), predicted=("p", "mean"), realized=("y", "mean")).reset_index(names="decile")
