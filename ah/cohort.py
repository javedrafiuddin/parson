"""Section 8.2 cohort construction: buyable bases at quarter-ends for EVERY CIK in the survivorship-free master.

Subsets (kept separate in every count):
  S1_PRICED   - the issuer's common line is still quoted today -> daily path, exact Section 5.1 tests, path labels
  S2_UNPRICED - issuer has no quoted line today (died, acquired, went dark) -> EDGAR-only: public-float proxy for
                market value, terminal class from filing-index events
Identity is CIK + date. Features use only data filed strictly before the base date (pit.asof_panel).
"""
import numpy as np
import pandas as pd
from . import store, pit, labels
from .config import DERIVED, PRICES, SCREEN, COST, DATA

PERIODIC = "('10-K','10-KT','10-K405','10-Q','10-QT','10-KSB','10-QSB')"
MERGER_FORMS = "('DEFM14A','PREM14A','SC TO-T','SC TO-T/A','SC 14D9','SC 14D9/A','SC 13E3','SC 13E3/A','DEFM14C','PREM14C','SC TO-I')"


def quarter_ends(start="2012-06-30", end="2025-09-30"):
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(start, end, freq="QE")]


def cik_ticker_map(c):
    """Current CIK -> quoted lines (from the EDGAR entity master), restricted to lines we hold prices for."""
    ent = c.execute("SELECT cik, tickers, exchanges, sic, name FROM entities").df()
    have = set(c.execute("SELECT DISTINCT ticker FROM prices").df().ticker)
    meta = c.execute("SELECT ticker, ysym FROM price_meta").df().drop_duplicates("ticker")
    y2t = dict(zip(meta.ysym, meta.ticker))
    rows = []
    for r in ent.itertuples():
        for t in [x for x in (r.tickers or "").split(",") if x]:
            tk = y2t.get(t, t)
            if tk in have:
                rows.append((r.cik, tk))
    return pd.DataFrame(rows, columns=["cik", "ticker"]).drop_duplicates()


def terminal_events(c):
    """Per CIK, from the filing index only: last periodic filing, first bankruptcy 8-K (item 1.03),
    first deregistration/delisting form (15-*, 25*), merger evidence (tender/merger proxy forms, 8-K 2.01/5.01)."""
    q = f"""
    SELECT cik,
      max(CASE WHEN form IN {PERIODIC} THEN filed END) AS last_periodic,
      min(CASE WHEN form IN {PERIODIC} THEN filed END) AS first_periodic,
      min(CASE WHEN form LIKE '8-K%' AND items LIKE '%1.03%' THEN filed END) AS first_bk,
      max(CASE WHEN form LIKE '15-%' OR form LIKE '25%' THEN filed END) AS last_dereg,
      max(CASE WHEN form IN {MERGER_FORMS} THEN filed END) AS last_merger_form,
      max(CASE WHEN form LIKE '8-K%' AND (items LIKE '%2.01%' OR items LIKE '%5.01%') THEN filed END) AS last_coc_8k,
      max(CASE WHEN form LIKE '8-K%' AND items LIKE '%3.01%' THEN filed END) AS last_delist_notice,
      max(filed) AS last_any, count(*) AS n_filings
    FROM filings GROUP BY 1"""
    t = c.execute(q).df()
    for col in t.columns:
        if col.startswith(("last_", "first_")):
            t[col] = pd.to_datetime(t[col], errors="coerce")
    return t


def price_block(c, tmap, base_dates, rt_cost):
    """For every priced CIK and base date: unadjusted price, ADV20, 3y drawdown, momentum + forward labels.
    One primary common line per CIK = the line with the longest price history."""
    bd = pd.to_datetime(base_dates)
    n = c.execute("SELECT ticker, count(*) n, min(date) d0 FROM prices GROUP BY 1").df()
    tm = tmap.merge(n, on="ticker")
    # primary line: prefer plain symbols (no class/instrument suffix), then longest history
    tm["plain"] = ~tm.ticker.str.contains(r"[.$\-]") & ~((tm.ticker.str.len() >= 5) & tm.ticker.str.endswith(("W", "U", "R")))
    tm = tm.sort_values(["cik", "plain", "n"], ascending=[True, False, False]).drop_duplicates("cik")
    sp = c.execute("SELECT ticker, date, numerator, denominator FROM splits").df()
    sp["date"] = pd.to_datetime(sp.date)
    spg = {k: v.sort_values("date") for k, v in sp.groupby("ticker")}
    out = []
    tickers = tm.ticker.tolist()
    t2c = dict(zip(tm.ticker, tm.cik))
    for i in range(0, len(tickers), 400):
        chunk = tickers[i:i + 400]
        df = c.execute("SELECT ticker, date, close, adjclose, volume FROM prices WHERE ticker IN (SELECT unnest(?)) AND close > 0 ORDER BY ticker, date", [chunk]).df()
        df["date"] = pd.to_datetime(df.date)
        for tk, g in df.groupby("ticker", sort=False):
            g = g.reset_index(drop=True)
            lab = labels.path_labels(g, list(bd), rt_cost=rt_cost)
            if lab is None:
                continue
            d = g.date.to_numpy(); cl = g.close.to_numpy(float); dv = cl * g.volume.to_numpy(float)
            idx = np.searchsorted(d, lab.base_date.to_numpy(dtype="datetime64[ns]"), side="right") - 1
            cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(dv))])
            lo20 = np.maximum(idx - 19, 0)
            lab["adv20"] = (cs[idx + 1] - cs[lo20]) / (idx - lo20 + 1)
            hi3 = pd.Series(cl).rolling(756, min_periods=1).max().to_numpy()
            lab["close_bd"] = cl[idx]
            lab["drawdown_3y"] = 1 - cl[idx] / hi3[idx]
            lab["hist_days"] = idx + 1
            for nm, k in (("ret_6m", 126), ("ret_12m", 252)):
                j = idx - k
                lab[nm] = np.where(j >= 0, cl[idx] / cl[np.maximum(j, 0)] - 1, np.nan)
            lr = np.diff(np.log(cl), prepend=np.log(cl[0]))
            vol = pd.Series(lr).rolling(126, min_periods=40).std().to_numpy() * np.sqrt(252)
            lab["vol_6m"] = vol[idx]
            # unadjusted price at base date: adjusted close x product of ratios of splits AFTER the base date
            s = spg.get(tk)
            if s is not None and len(s):
                sd = s.date.to_numpy(); ratio = (s.numerator / s.denominator).to_numpy(float)
                after = np.array([np.prod(ratio[sd > b]) for b in lab.base_date.to_numpy(dtype="datetime64[ns]")])
            else:
                after = 1.0
            lab["unadj_close_bd"] = lab["close_bd"] * after
            lab["split_after"] = after
            lab["ticker"] = tk
            lab["cik"] = t2c[tk]
            out.append(lab)
    P = pd.concat(out, ignore_index=True)
    P["base_date"] = pd.to_datetime(P.base_date)
    return P, sp


def build(base_dates=None, rt_cost=None, verbose=True):
    c = store.connect()
    base_dates = base_dates or quarter_ends()
    rt = COST["assumed_rt_listed_common"] if rt_cost is None else rt_cost
    log = []
    say = lambda k, v: (log.append((k, v)), verbose and print(f"{k}: {v}", flush=True))

    # ---- 1. fundamentals known strictly before each base date, all CIKs ----
    parts = []
    pc = pit.con()
    for i in range(0, len(base_dates), 6):
        parts.append(pit.asof_panel(base_dates[i:i + 6], pc))
    F = pd.concat(parts, ignore_index=True)
    F["base_date"] = pd.to_datetime(F.date)
    say("cik-dates with any balance sheet known before the base date", len(F))

    # ---- 2. active periodic filer at the base date (10-K/10-Q filed in the prior 400 days) ----
    c.execute("CREATE OR REPLACE TEMP TABLE bdt AS SELECT CAST(d AS DATE) d FROM (SELECT unnest(?) d)", [list(base_dates)])
    act = c.execute(f"""SELECT DISTINCT f.cik, b.d AS base_date FROM bdt b JOIN filings f
                        ON f.form IN {PERIODIC} AND CAST(f.filed AS DATE) < b.d AND CAST(f.filed AS DATE) >= b.d - INTERVAL 400 DAY""").df()
    act["base_date"] = pd.to_datetime(act.base_date)
    F = F.merge(act.assign(active=True), on=["cik", "base_date"], how="inner")
    say("... of which active 10-K/10-Q filer at the base date", len(F))

    # ---- 3. price block for priced CIKs ----
    tmap = cik_ticker_map(c)
    P, sp = price_block(c, tmap, base_dates, rt)
    say("priced CIKs (a quoted line exists today)", P.cik.nunique())
    B = F.merge(P, on=["cik", "base_date"], how="left")
    B["subset"] = np.where(B.close_bd.notna(), "S1_PRICED", "S2_UNPRICED")
    # a CIK that is priced today but had no quote at that base date (pre-IPO shell, pre-listing) is not a base
    priced_ciks = set(P.cik.unique())
    pre = (B.subset == "S2_UNPRICED") & B.cik.isin(priced_ciks)
    say("dropped: priced CIK with no quote near that base date (pre-listing / halted)", int(pre.sum()))
    B = B[~pre].copy()

    # ---- 4. market value ----
    # S1: unadjusted close x shares as filed (made split-consistent for splits between the share date and the base date)
    spk = {k: v for k, v in sp.groupby("ticker")}
    def between(row):
        s = spk.get(row.ticker)
        if s is None or pd.isna(row.shares_e):
            return 1.0
        m = s[(s.date > row.shares_e) & (s.date <= row.base_date)]
        return float(np.prod(m.numerator / m.denominator)) if len(m) else 1.0
    s1 = B.subset == "S1_PRICED"
    hs = B.ticker.isin(spk.keys()) & s1
    B["sh_adj"] = 1.0
    B.loc[hs, "sh_adj"] = [between(r) for r in B.loc[hs, ["ticker", "shares_e", "base_date"]].itertuples()]
    B["mcap_px"] = B.unadj_close_bd * B.shares * B.sh_adj
    B["mcap_float"] = B.float_usd
    B["mcap"] = np.where(s1, B.mcap_px, B.mcap_float)
    B["mcap_src"] = np.where(s1, "PRICE_X_SHARES", "FLOAT_PROXY")
    for nm, m in (("", "mcap"), ("_fp", "mcap_float")):
        B["ev" + nm] = B[m] + B.debt_total.fillna(0) + B.pref_liq.fillna(0) - B.cash_total.fillna(0)
        B["ev_rev" + nm] = B["ev" + nm] / B.rev_ttm.where(B.rev_ttm > 0)

    # float history proxy for drawdown (all CIKs): float now vs max float filed in the prior 3 years
    fl = pd.read_parquet(pit.PIT / "series" / "instant.parquet")
    fl = fl[fl.tag == "EntityPublicFloat"][["cik", "e", "val", "known"]]
    fl["known"] = pd.to_datetime(fl.known); fl["e"] = pd.to_datetime(fl.e)
    fl = fl.sort_values(["cik", "known"])
    B = B.sort_values(["base_date", "cik"])
    mx = []
    for d, g in B.groupby("base_date"):
        w = fl[(fl.known < d) & (fl.e >= d - pd.Timedelta(days=3 * 365 + 650))]
        mx.append(g[["cik", "base_date"]].merge(w.groupby("cik").val.max().rename("float_max_3y"), on="cik", how="left"))
    B = B.merge(pd.concat(mx), on=["cik", "base_date"], how="left")
    B["float_dd"] = 1 - B.float_usd / B.float_max_3y
    B = B.reset_index(drop=True)
    s1 = B.subset == "S1_PRICED"

    # ---- 5. entry condition ----
    S = SCREEN
    B["t1_px"] = B.drawdown_3y >= S["drawdown_min"]
    B["t2_px"] = (B.ev_rev < S["ev_rev_max"]) & (B.rev_ttm > 0) & B.mcap_px.notna()
    B["t3_px"] = (B.mcap_px < S["mcap_small_max"]) & (B.rev_ttm > S["rev_for_small_min"])
    B["t1_fp"] = B.float_dd >= S["drawdown_min"]
    B["t2_fp"] = (B.ev_rev_fp < S["ev_rev_max"]) & (B.rev_ttm > 0) & B.mcap_float.notna()
    B["t3_fp"] = (B.mcap_float < S["mcap_small_max"]) & (B.rev_ttm > S["rev_for_small_min"])
    B["damaged_px"] = B.t1_px | B.t2_px | B.t3_px
    B["damaged_fp"] = B.t1_fp | B.t2_fp | B.t3_fp
    B["tradable_px"] = (B.adv20 >= S["adv_min_common"]) & (B.hist_days >= 60)
    # float level at which half of priced names clear the $250k ADV floor (calibrated on S1, applied to S2)
    cal = B[s1 & B.float_usd.notna() & B.adv20.notna()]
    if len(cal) > 1000:
        cal = cal.assign(lf=np.log10(cal.float_usd.clip(lower=1e5)))
        bins = np.arange(5.5, 9.6, 0.25)
        pr = cal.groupby(pd.cut(cal.lf, bins), observed=True).apply(lambda g: (g.adv20 >= S["adv_min_common"]).mean())
        above = pr[pr >= 0.5]
        float_min = 10 ** float(above.index[0].left) if len(above) else 5e7
    else:
        float_min = 5e7
    say("float proxy threshold where >=50% of priced names clear the $250k ADV floor (USD)", round(float_min))
    B["tradable_fp"] = B.float_usd >= float_min
    B["base_exact"] = np.where(s1, B.damaged_px & B.tradable_px, B.damaged_fp & B.tradable_fp)
    B["base_safe"] = B.damaged_fp & B.tradable_fp          # identical rule for both subsets
    B.attrs["float_min"] = float_min

    # ---- 6. S2 terminal class from the filing index ----
    T = terminal_events(c)
    B = B.merge(T, on="cik", how="left")
    H = pd.Timedelta(days=int(365.25 * 5))
    death = B.last_periodic + pd.Timedelta(days=200)          # no periodic report for 200+ days after the last one
    died_in = (death <= B.base_date + H) & (death <= pd.Timestamp("2026-11-01"))
    bk = B.first_bk.notna() & (B.first_bk > B.base_date - pd.Timedelta(days=30)) & (B.first_bk <= B.base_date + H)
    mg_dt = pd.concat([B.last_merger_form, B.last_coc_8k], axis=1).max(axis=1)
    mg = mg_dt.notna() & (mg_dt >= B.last_periodic - pd.Timedelta(days=400)) & died_in
    B["s2_event"] = np.where(~(B.subset == "S2_UNPRICED"), None,
                     np.where(bk, "BANKRUPTCY", np.where(died_in & mg, "MERGED_OR_ACQUIRED",
                     np.where(died_in, "DARK_OR_DEREGISTERED", "STILL_FILING_UNPRICED"))))
    B["death_date"] = death.where(died_in)
    return B, log


def postprocess(B, c, dates):
    """Shared by the historical cohort AND today's field so model inputs are built by one code path:
    prior-year values (same CIK, decision date one year earlier), filing-index flags known before the date,
    SIC, and the survivorship-free sector context."""
    from . import model
    ent = c.execute("SELECT cik, sic, name AS sec_name FROM entities").df()
    B = B.merge(ent, on="cik", how="left")
    prev = B[["cik", "base_date", "rev_ttm", "shares", "float_usd"]].copy()
    prev["base_date"] = prev.base_date + pd.DateOffset(years=1)
    prev = prev.rename(columns={"rev_ttm": "rev_ttm_prev", "shares": "shares_prev", "float_usd": "float_prev"})
    B = B.merge(prev.drop_duplicates(["cik", "base_date"]), on=["cik", "base_date"], how="left")
    c.execute("CREATE OR REPLACE TEMP TABLE bdt AS SELECT CAST(d AS DATE) d FROM (SELECT unnest(?) d)", [list(dates)])
    fx = c.execute("""SELECT f.cik, b.d AS base_date,
            max(CASE WHEN (f.form LIKE '424B%' OR f.form IN ('S-1','S-1/A','S-3','S-3/A','S-3ASR')) AND CAST(f.filed AS DATE) >= b.d - INTERVAL 90 DAY THEN 1 ELSE 0 END) offering_doc_90d,
            max(CASE WHEN f.form LIKE 'NT 10-%' THEN 1 ELSE 0 END) nt_12m_flag
         FROM bdt b JOIN filings f ON CAST(f.filed AS DATE) < b.d AND CAST(f.filed AS DATE) >= b.d - INTERVAL 365 DAY
         WHERE f.form LIKE '424B%' OR f.form IN ('S-1','S-1/A','S-3','S-3/A','S-3ASR') OR f.form LIKE 'NT 10-%'
         GROUP BY 1,2""").df()
    fx["base_date"] = pd.to_datetime(fx.base_date)
    B = B.merge(fx, on=["cik", "base_date"], how="left")
    B = B.reset_index(drop=True)
    return pd.concat([B, model.sector_context(B)], axis=1)


def classify_all(Q, asof="2026-11-09", H=5, swan_peak=25.0, swan_term=10.0):
    """One class column for both subsets. A base is MATURED when its H-year window has closed.
    S1: path labels. S2 (unpriced): BANKRUPTCY -> GRAVEYARD; DARK -> GRAVEYARD_BROAD; merged/acquired or still filing
    at window end -> MUDDLE, except float-implied value multiple >= 10x -> POSSIBLE_SWAN_UNPRICED (upper-bound bracket)."""
    Q = Q.copy()
    s1 = Q.subset == "S1_PRICED"
    Q["matured"] = Q.base_date + pd.Timedelta(days=int(365.25 * H) + 15) <= pd.Timestamp(asof)
    c1 = labels.classify(Q[s1], swan_peak=swan_peak, swan_term=swan_term, H=H)
    ev = Q.s2_event
    poss = Q.float_mult_max_5y >= 10
    c2 = np.where(ev == "BANKRUPTCY", "GRAVEYARD", np.where(ev == "DARK_OR_DEREGISTERED", "GRAVEYARD_BROAD",
         np.where(poss, "POSSIBLE_SWAN_UNPRICED", np.where(Q.matured, "MUDDLE", "UNRESOLVED"))))
    Q["cls"] = pd.Series(c2, index=Q.index)
    Q.loc[s1, "cls"] = c1
    return Q
