"""Wave atlas (Section 5.6 'comparable prior waves', measured not asserted): for three cycle windows, every quoted
ticker's trough -> subsequent peak multiple (daily closes, split-adjusted) and months trough-to-crest; aggregated by
SIC-3 industry. Survivors only (dead tickers are unpriced) - stated wherever used.
Writes data/derived/wave_atlas.parquet and wave_atlas_summary.json"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah import store, cohort
from ah.config import DERIVED

c = store.connect()
WIN = {"W1_2015-2018": ("2015-06-01", "2018-12-31"), "W2_2019-2021": ("2019-06-01", "2021-12-31"), "W3_2022-2026": ("2022-06-01", "2026-11-09")}
tm = cohort.cik_ticker_map(c)
ent = c.execute("SELECT cik, sic, name FROM entities").df()
rows = []
for w, (a, b) in WIN.items():
    d = c.execute(f"""
      WITH p AS (SELECT ticker, date, close, close*volume dv FROM prices WHERE date BETWEEN DATE '{a}' AND DATE '{b}' AND close > 0),
      t AS (SELECT ticker, arg_min(date, close) td, min(close) tc, count(*) n, median(dv) mdv FROM p GROUP BY 1 HAVING count(*) >= 250)
      SELECT t.ticker, t.td, t.tc, t.n, t.mdv, max(p.close) pc, arg_max(p.date, p.close) pd
      FROM t JOIN p ON p.ticker = t.ticker AND p.date >= t.td GROUP BY 1,2,3,4,5""").df()
    d["window"] = w
    rows.append(d)
A = pd.concat(rows, ignore_index=True)
A["mult"] = A.pc / A.tc
A["months"] = (pd.to_datetime(A.pd) - pd.to_datetime(A.td)).dt.days / 30.4
A = A.merge(tm, on="ticker", how="inner").merge(ent, on="cik", how="left")
A = A.sort_values("mult", ascending=False).drop_duplicates(["window", "cik"])
A = A[(A.mdv >= 50_000) & (A.tc >= 0.10)]            # tradable: median daily $ volume >= $50k and trough not sub-dime
A["sic3"] = pd.to_numeric(A.sic, errors="coerce") // 10
A.to_parquet(DERIVED / "wave_atlas.parquet", index=False)
out = {}
for w, g in A.groupby("window"):
    sw = g[g.mult >= 25]
    ind = []
    for k, h in g.groupby("sic3"):
        if len(h) < 8:
            continue
        top = h.sort_values("mult", ascending=False).head(max(3, int(np.ceil(0.2 * len(h)))))
        ind.append({"sic3": int(k), "n": int(len(h)), "leader_median_x": round(float(top.mult.median()), 1), "leader_months_median": round(float(top.months.median()), 1),
                    "n_25x": int((h.mult >= 25).sum()), "leaders": ", ".join(top.ticker.head(6))})
    I = pd.DataFrame(ind).sort_values("leader_median_x", ascending=False)
    out[w] = {"n_names": int(len(g)), "n_25x": int(len(sw)), "share_25x": round(len(sw) / len(g), 4), "median_months_trough_to_crest_25x": round(float(sw.months.median()), 1) if len(sw) else None,
              "n_100x": int((g.mult >= 100).sum()), "industries_with_leader_basket_ge_10x": int((I.leader_median_x >= 10).sum()), "n_industries": int(len(I)),
              "top_industries": I.head(12).to_dict("records"),
              "top_names": sw.head(40)[["ticker", "name", "mult", "months", "td", "pd"]].assign(mult=lambda x: x.mult.round(1), months=lambda x: x.months.round(1), td=lambda x: x.td.astype(str).str[:10], pd=lambda x: x.pd.astype(str).str[:10]).to_dict("records")}
json.dump(out, open(DERIVED / "wave_atlas_summary.json", "w"), indent=1, default=str)
for w, v in out.items():
    print(w, {k: v[k] for k in ("n_names", "n_25x", "share_25x", "n_100x", "median_months_trough_to_crest_25x", "industries_with_leader_basket_ge_10x", "n_industries")})
    print(pd.DataFrame(v["top_industries"]).head(8).to_string(index=False))
    print("  25x names:", ", ".join(f"{x['ticker']}({x['mult']:.0f}x/{x['months']:.0f}m)" for x in v["top_names"][:30]))
