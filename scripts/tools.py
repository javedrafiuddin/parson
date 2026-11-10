#!/usr/bin/env python3
"""Small evidence tools for research/verification agents. All sources are public primary data.

  tools.py px SYM[,SYM...] [--from 2020-01-01] [--to 2026-11-09]   trough->peak multiple, dates, months, last close
  tools.py awards "Recipient name" [--years 5]                      federal contract/grant obligations (USAspending.gov)
  tools.py trials "Company name"                                   registered Phase 2/3 trials by lead sponsor (ClinicalTrials.gov)
  tools.py recent SYM [--months 12]                                 filing index from EDGAR: form, date, accession, 8-K items
  tools.py row SYM                                                  the screen's computed row for a symbol (prices + XBRL)
"""
import sys, pathlib, argparse, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pandas as pd, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("cmd"); ap.add_argument("arg")
ap.add_argument("--from", dest="frm", default="2019-01-01"); ap.add_argument("--to", default="2026-11-09")
ap.add_argument("--years", type=int, default=5); ap.add_argument("--months", type=int, default=12)
a = ap.parse_args()
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 200)

if a.cmd == "px":
    from ah import store
    c = store.connect()
    out = []
    for s in a.arg.split(","):
        d = c.execute("SELECT date, close FROM prices WHERE ticker = ? AND date BETWEEN ? AND ? AND close > 0 ORDER BY date", [s, a.frm, a.to]).df()
        if d.empty:
            out.append({"symbol": s, "note": "no price history in window"}); continue
        i = int(d.close.idxmin()); lo = d.iloc[i]
        after = d.iloc[i:]
        j = int(after.close.idxmax()); hi = d.loc[j]
        pk = d.loc[int(d.close.idxmax())]
        out.append({"symbol": s, "first": str(d.date.iloc[0])[:10], "trough": round(float(lo.close), 4), "trough_date": str(lo.date)[:10],
                    "peak_after_trough": round(float(hi.close), 4), "peak_date": str(hi.date)[:10], "trough_to_peak_x": round(float(hi.close / lo.close), 1),
                    "months": round((hi.date - lo.date).days / 30.4, 1), "window_high": round(float(pk.close), 4), "window_high_date": str(pk.date)[:10],
                    "last": round(float(d.close.iloc[-1]), 4), "last_vs_window_high": round(float(d.close.iloc[-1] / pk.close - 1), 3)})
    print(pd.DataFrame(out).to_string(index=False))
    print("(split-adjusted daily closes, Yahoo chart API; delayed)")
elif a.cmd == "awards":
    from ah.http import session
    import datetime as dt
    end = dt.date(2026, 11, 9); start = end.replace(year=end.year - a.years)
    body = {"filters": {"recipient_search_text": [a.arg], "time_period": [{"start_date": str(start), "end_date": str(end)}],
                        "award_type_codes": ["A", "B", "C", "D"]},
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Awarding Sub Agency", "Start Date", "End Date", "Description"],
            "sort": "Award Amount", "order": "desc", "limit": 15, "page": 1}
    r = session().post("https://api.usaspending.gov/api/v2/search/spending_by_award/", json=body, timeout=90)
    res = r.json().get("results", [])
    df = pd.DataFrame(res)
    if df.empty:
        print("no contract awards found for recipient text:", a.arg)
    else:
        df["Description"] = df["Description"].astype(str).str.slice(0, 60)
        print(df[["Award ID", "Recipient Name", "Award Amount", "Awarding Sub Agency", "Start Date", "End Date", "Description"]].to_string(index=False))
        print(f"top-15 contract awards {start}..{end}; sum of shown = ${df['Award Amount'].sum():,.0f}  (source: USAspending.gov spending_by_award; recipient text match - check the name)")
elif a.cmd == "trials":
    from ah import ctgov
    t = ctgov.sponsor_trials(a.arg)
    print(json.dumps(ctgov.summarize(t)))
    if t:
        print(pd.DataFrame(t)[["nct", "phase", "status", "primary_completion", "conditions", "title"]].assign(title=lambda d: d.title.str.slice(0, 60)).head(25).to_string(index=False))
elif a.cmd == "recent":
    from ah import store
    c = store.connect()
    cik = c.execute("SELECT cik FROM read_parquet('data/derived/field_scan.parquet') WHERE symbol = ?", [a.arg]).fetchone()
    if not cik:
        print("symbol not in field scan"); sys.exit(0)
    d = c.execute(f"SELECT form, filed, accn, items, primary_desc FROM filings WHERE cik = ? AND CAST(filed AS DATE) >= DATE '2026-11-10' - INTERVAL {a.months} MONTH AND form NOT IN ('4','3','5','144') ORDER BY filed DESC", [cik[0]]).df()
    print(f"CIK {cik[0]}  ({len(d)} filings, last {a.months} months; index pulled 2026-11-10)")
    print(d.head(120).to_string(index=False))
elif a.cmd == "row":
    st = pd.read_parquet("data/derived/stage1.parquet")
    r = st[st.symbol == a.arg]
    cols = ["symbol", "name", "cik", "sec_type", "exchange", "sic", "sic_desc", "last_close", "last_date", "adv20", "drawdown_3y", "high_3y", "high_3y_date", "mcap", "mcap_calc", "mcap_screener",
            "mcap_mismatch", "ev", "ev_rev", "rev_ttm", "rev_ttm_e", "cash_total", "debt_total", "debt_due_12m", "pref_liq", "ocf_ttm", "ocf_last2q", "runway_years", "runway_years_2q",
            "shares", "shares_e", "shares_src", "bs_end", "bs_known", "bs_accn", "n_damage_tests", "t_drawdown", "t_ev_rev", "t_small_rev", "stage1", "real_business", "survival_gate",
            "fraud_flag", "rs_risk", "bk_or_despac", "nonreliance_12m", "auditor_change_12m", "nt_12m", "delist_notice_12m", "offering_doc_12m", "last_424b5", "n_424b_12m",
            "unreg_sale_12m", "shelf_36m", "proxy_12m", "ct_live", "ct_active", "ct_p3", "ct_example"]
    print(r[[c for c in cols if c in r]].T.to_string() if len(r) else "symbol not in the R2 universe")
