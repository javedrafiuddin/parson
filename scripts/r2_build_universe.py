"""R2: universe build with the coverage ledger (Section 4). Run after the PIT + price pulls complete.
Phase A (this script, arg 'map'): F0-F3 + OTC discovery -> writes data/tmp/syms_otc.csv for the OTC price pull.
Phase B (arg 'scan'): F4, F5, D1 damage scan -> universe.csv + ledger rows + data/derived/field_scan.parquet"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah import nasdaq, yahoo, store, pit, px
from ah.config import DERIVED, STATE, SCREEN, RUN_ASOF, DATA

phase = sys.argv[1]
ASOF = RUN_ASOF
c = store.connect()
ledger = []


def led(step, n_in, n_out, rule):
    ledger.append((step, n_in, n_out, n_in - n_out if n_in is not None else None, rule))
    print(f"[{step}] in={n_in} out={n_out} :: {rule}", flush=True)


# ---------- F0/F1: field + instrument scope ----------
f = pd.read_csv(DERIVED / "field_listed_all.csv", keep_default_na=False, dtype=str)
f["sec_type"] = [nasdaq.classify(n, s) for n, s in zip(f.name, f.symbol)]
f.loc[f.etf == "Y", "sec_type"] = "etf"
n0 = len(f)
scope = {"common", "adr", "warrant", "convertible_or_preferred"}
cut1 = f[~f.sec_type.isin(scope)].sec_type.value_counts().to_dict()
f1 = f[f.sec_type.isin(scope)].copy()

# ---------- F2: CIK mapping through the EDGAR entity master (identity = CIK, never ticker alone) ----------
ent = c.execute("SELECT cik, name AS sec_name, entity_type, sic, sic_desc, category, tickers, exchanges, state_inc, former_names FROM entities").df()
rows = []
for r in ent.itertuples():
    tk = [t for t in (r.tickers or "").split(",") if t]
    ex = (r.exchanges or "").split(",")
    for i, t in enumerate(tk):
        rows.append((t, r.cik, ex[i] if i < len(ex) else ""))
tmap = pd.DataFrame(rows, columns=["sec_ticker", "cik", "sec_exchange"]).drop_duplicates("sec_ticker")
f1 = f1.merge(tmap, left_on="ysym", right_on="sec_ticker", how="left")
# fallback: instrument symbols not individually listed by the SEC -> issuer via base symbol
def base(sym, st):
    if "-" in sym:
        return sym.split("-")[0]
    if st == "warrant" and len(sym) >= 5 and sym.endswith(("W", "WW")):
        return sym.rstrip("W") if not sym.endswith("WW") else sym[:-2]
    if st == "convertible_or_preferred" and len(sym) >= 5:
        return sym[:-1]
    return None
miss = f1.cik.isna()
f1.loc[miss, "base_sym"] = [base(s, t) for s, t in zip(f1.ysym[miss], f1.sec_type[miss])]
bm = tmap.set_index("sec_ticker").cik
f1.loc[miss, "cik"] = f1.loc[miss, "base_sym"].map(bm)
f1["cik_via"] = np.where(miss & f1.cik.notna(), "base_symbol", np.where(f1.cik.notna(), "sec_ticker", None))
f2 = f1[f1.cik.notna()].copy()
f2["cik"] = f2.cik.astype(int)

# ---------- OTC discovery: SEC registrants with an OTC ticker (not exchange-listed) ----------
listed_ciks = set(f2.cik)
otc = tmap[(tmap.sec_exchange == "OTC") & (~tmap.cik.isin(listed_ciks))].copy()
otc = otc[~otc.sec_ticker.str.contains("-")]            # common lines only (first ticker per CIK)
otc = otc.drop_duplicates("cik")
otc_df = pd.DataFrame({"symbol": otc.sec_ticker, "name": otc.cik.map(ent.set_index("cik").sec_name), "exchange": "OTC",
                       "etf": "N", "fin_status": "", "cqs": otc.sec_ticker, "src": "edgar:submissions.exchanges=OTC",
                       "sec_type": "otc_common", "ysym": otc.sec_ticker, "sec_ticker": otc.sec_ticker, "cik": otc.cik.astype(int),
                       "sec_exchange": "OTC", "cik_via": "sec_ticker"})
n_field = n0 + len(otc_df)
led("F0", None, n_field, f"field enumerated: {n0} listed securities (Nasdaq Trader directory) + {len(otc_df)} OTC tickers of SEC registrants (EDGAR submissions, exchanges=OTC)")
led("F1", n_field, len(f1) + len(otc_df), f"instrument scope = common/ADR/warrant/convertible-or-preferred/OTC common; cut by type: {json.dumps(cut1)}")
led("F2", len(f1) + len(otc_df), len(f2) + len(otc_df), "maps to an EDGAR CIK that has filed XBRL periodic reports (submissions.tickers; base-symbol fallback for instrument lines)")
u = pd.concat([f2, otc_df], ignore_index=True)

# ---------- F3: filing floor (10-K AND 10-Q within trailing 12 months) ----------
fl = c.execute(f"""SELECT cik,
        max(CASE WHEN form IN ('10-K','10-KT','10-K405') THEN filed END) last_10k,
        max(CASE WHEN form IN ('10-Q','10-QT') THEN filed END) last_10q,
        max(CASE WHEN form IN ('20-F','40-F') THEN filed END) last_fpi,
        max(filed) last_any
     FROM filings GROUP BY 1""").df()
u = u.merge(fl, on="cik", how="left")
cutoff = (pd.Timestamp(ASOF) - pd.DateOffset(months=12)).strftime("%Y-%m-%d")
ok3 = (u.last_10k.fillna("") >= cutoff) & (u.last_10q.fillna("") >= cutoff)
fpi = (~ok3) & (u.last_fpi.fillna("") >= cutoff)
u3 = u[ok3].copy()
led("F3", len(u), len(u3), f"filing floor: 10-K and 10-Q both filed since {cutoff}; of the {int((~ok3).sum())} cut, {int(fpi.sum())} are 20-F/40-F-only foreign issuers, the rest are delinquent/new/non-reporting")
u[~ok3][["symbol", "sec_type", "cik", "last_10k", "last_10q", "last_fpi"]].to_csv(DATA / "tmp" / "cut_F3.csv", index=False)

if phase == "map":
    u3[u3.sec_type == "otc_common"][["symbol", "ysym"]].to_csv(DATA / "tmp" / "syms_otc.csv", index=False)
    u3.to_parquet(DATA / "tmp" / "u3.parquet", index=False)
    pd.DataFrame(ledger, columns=["step", "in", "out", "cut", "rule"]).to_csv(DATA / "tmp" / "ledger_A.csv", index=False)
    print("OTC symbols needing prices:", int((u3.sec_type == "otc_common").sum()))
    sys.exit(0)

# ---------- F4/F5: price + liquidity floors ----------
snap = px.snapshot(ASOF, c)
u4 = u3.merge(snap, left_on="symbol", right_on="ticker", how="left")
recent = (pd.Timestamp(ASOF) - pd.to_datetime(u4.last_date)).dt.days <= 14
ok4 = u4.last_close.notna() & (u4.n_days >= 60) & recent
led("F4", len(u4), int(ok4.sum()), "price floor: >= 60 sessions of history and a quote within the last 10 sessions (Yahoo chart API, delayed)")
u4[~ok4][["symbol", "sec_type", "cik", "last_date", "n_days"]].to_csv(DATA / "tmp" / "cut_F4.csv", index=False)
u4 = u4[ok4].copy()
thr = np.where(u4.sec_type.isin(["warrant", "convertible_or_preferred"]), SCREEN["adv_min_warrant_pref"], SCREEN["adv_min_common"])
ok5 = u4.adv20 >= thr
led("F5", len(u4), int(ok5.sum()), "liquidity floor: 20-day average dollar volume >= $250k (common/ADR/OTC) or >= $50k (warrants, preferreds)")
u4[~ok5][["symbol", "sec_type", "cik", "adv20"]].to_csv(DATA / "tmp" / "cut_F5.csv", index=False)
u5 = u4[ok5].copy()

# ---------- D1: cheap damage scan (Section 5.2 priced-for-failure; any one of three) ----------
fund = pit.asof_panel([ASOF], pit.con(), ciks=u5.cik.unique().tolist())
keep = ["cik", "bs_end", "bs_known", "bs_accn", "cash_total", "debt_total", "debt_due_12m", "pref_liq", "rev_ttm", "rev_ttm_e", "rev_ttm_m",
        "ocf_ttm", "ocf_last2q", "burn_ttm", "runway_years", "runway_years_2q", "cash_positive", "shares", "shares_e", "shares_src",
        "float_usd", "ni_ttm", "gp_ttm", "rd_ttm", "iss_ttm", "fin_ttm", "Assets", "Liabilities", "StockholdersEquity", "AssetsHeldInTrustNoncurrent", "AssetsHeldInTrust"]
u5 = u5.merge(fund[[k for k in keep if k in fund.columns]], on="cik", how="left")
# issuer-level market cap: common line price x shares (as filed, split-consistent). Screener cap as cross-check.
scr = nasdaq.screener()[["symbol", "marketCap", "sector", "industry", "country", "ipoyear"]].rename(columns={"marketCap": "mcap_screener"})
u5 = u5.merge(scr, on="symbol", how="left")
sp = c.execute("SELECT ticker, date, numerator, denominator FROM splits").df()
sp["date"] = pd.to_datetime(sp.date)
def adj_shares(row):
    s = sp[(sp.ticker == row.symbol) & (sp.date > row.shares_e)] if pd.notna(row.shares_e) else sp.iloc[0:0]
    k = float(np.prod(s.numerator / s.denominator)) if len(s) else 1.0
    return row.shares * k if pd.notna(row.shares) else np.nan
u5["shares_adj"] = [adj_shares(r) for r in u5.itertuples()]
is_common = u5.sec_type.isin(["common", "adr", "otc_common"])
u5["mcap_calc"] = np.where(is_common, u5.last_close * u5.shares_adj, np.nan)
# issuer cap for instrument lines = cap of the issuer's most liquid common line
iss_cap = u5[is_common].sort_values("adv20", ascending=False).drop_duplicates("cik").set_index("cik")
u5["mcap"] = np.where(is_common, u5.mcap_calc.fillna(u5.mcap_screener), u5.cik.map(iss_cap.mcap_calc.fillna(iss_cap.mcap_screener)))
u5["issuer_drawdown_3y"] = np.where(is_common, u5.drawdown_3y, u5.cik.map(iss_cap.drawdown_3y))
u5["ev"] = u5.mcap + u5.debt_total.fillna(0) + u5.pref_liq.fillna(0) - u5.cash_total.fillna(0)
u5["ev_rev"] = u5.ev / u5.rev_ttm.where(u5.rev_ttm > 0)
t1 = (u5.drawdown_3y >= SCREEN["drawdown_min"]) | (u5.issuer_drawdown_3y >= SCREEN["drawdown_min"])
t2 = (u5.ev_rev < SCREEN["ev_rev_max"]) & u5.rev_ttm.notna() & u5.mcap.notna()
t3 = (u5.mcap < SCREEN["mcap_small_max"]) & (u5.rev_ttm > SCREEN["rev_for_small_min"])
u5["t_drawdown"], u5["t_ev_rev"], u5["t_small_rev"] = t1, t2, t3
u5["n_damage_tests"] = t1.astype(int) + t2.astype(int) + t3.astype(int)
d1 = u5[u5.n_damage_tests >= 1].copy()
led("D1", len(u5), len(d1), f"cheap damage scan, any of: drawdown>=60% from 3y high ({int(t1.sum())}), EV<2.0x TTM revenue ({int(t2.sum())}), mcap<$500M with TTM revenue>$20M ({int(t3.sum())}); two or more tests: {int((u5.n_damage_tests >= 2).sum())}")
u5.to_parquet(DERIVED / "field_scan.parquet", index=False)

# ---------- write universe.csv + ledger ----------
ac = {"common": "US-listed common stock", "adr": "US-listed ADR/ADS (10-K/10-Q filer)", "warrant": "Listed warrant",
      "convertible_or_preferred": "Tradable convertible/preferred", "otc_common": "OTC with current SEC filings"}
out = pd.DataFrame({
    "ticker": d1.symbol, "asset_class": d1.sec_type.map(ac), "source": d1.src, "cik": d1.cik, "name": d1.name, "exchange": d1.exchange,
    "sic": d1.sic if "sic" in d1 else None, "last_close": d1.last_close.round(4), "price_asof": pd.to_datetime(d1.last_date).dt.strftime("%Y-%m-%d"),
    "price_source": "yahoo_chart_v8 (delayed close)", "adv20_usd": d1.adv20.round(0), "drawdown_3y": d1.drawdown_3y.round(4),
    "mcap_usd": d1.mcap.round(0), "ev_rev": d1.ev_rev.round(3), "rev_ttm_usd": d1.rev_ttm, "runway_years": d1.runway_years.round(2),
    "t_drawdown": d1.t_drawdown, "t_ev_rev": d1.t_ev_rev, "t_small_rev": d1.t_small_rev, "n_damage_tests": d1.n_damage_tests,
    "latest_bs_accn": d1.bs_accn, "latest_bs_period": d1.bs_end, "latest_bs_filed": d1.bs_known})
out.sort_values(["asset_class", "ticker"]).to_csv(STATE / "universe.csv", index=False)
L = pd.concat([pd.read_csv(DATA / "tmp" / "ledger_A.csv") if False else pd.DataFrame(ledger, columns=["step", "in", "out", "cut", "rule"])])
L.to_csv(DERIVED / "coverage_ledger_r2.csv", index=False)
print(out.asset_class.value_counts())
print("universe rows", len(out), "distinct issuers", out.cik.nunique())
