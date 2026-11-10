#!/usr/bin/env python3
"""Filing reader for verification batches. Filing TEXT comes from the QuoteMedia mirror linked by Nasdaq's
filings API (www.sec.gov is not reachable here); accession numbers come from data.sec.gov submissions.

  filing.py list  SYMBOL [--forms 10-K,10-Q,8-K] [--n 40]      list filings: idx, form, filed, period, accession
  filing.py text  SYMBOL IDX|FORM                              cache full text; print path + length
  filing.py grep  SYMBOL IDX|FORM 'regex' [--ctx 250] [--max 12]   print matching snippets
  filing.py facts SYMBOL                                        latest XBRL point-in-time fundamentals (Section 5.1 inputs)
IDX is the index printed by `list`; FORM (e.g. 10-Q) means the most recent filing of that form."""
import sys, re, json, pathlib, argparse, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pandas as pd
from ah import nasdaq, edgar
from ah.http import get_json
from ah.config import RAW

CACHE = RAW / "filing_text"
CACHE.mkdir(parents=True, exist_ok=True)


def cik_for(symbol):
    hits = edgar.typeahead(symbol)
    for cik, ent, tk in hits:
        if tk and symbol.upper().replace(".", "-") in [t.strip().upper() for t in tk.split(",")]:
            return int(cik)
    return int(hits[0][0]) if hits else None


def _rows_cached(symbol):
    """Filing list cached for 12 hours per symbol (keeps parallel verification batches off the Nasdaq API)."""
    import time, json as _j
    f = CACHE / f"_list_{symbol.replace('/', '_')}.json"
    if f.exists() and time.time() - f.stat().st_mtime < 12 * 3600:
        return _j.loads(f.read_text())
    rows = nasdaq.sec_filings(symbol, limit=100)
    f.write_text(_j.dumps(rows))
    return rows


def _subs_cached(cik):
    import time, json as _j
    f = CACHE / f"_subs_{cik}.json"
    if f.exists() and time.time() - f.stat().st_mtime < 12 * 3600:
        return _j.loads(f.read_text())
    s = get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    r = s["filings"]["recent"]
    out = {"form": r["form"][:400], "filingDate": r["filingDate"][:400], "accessionNumber": r["accessionNumber"][:400], "items": r["items"][:400]}
    f.write_text(_j.dumps(out))
    return out


def _cik_cached(symbol):
    f = CACHE / f"_cik_{symbol.replace('/', '_')}.txt"
    if f.exists():
        return int(f.read_text())
    try:
        st = pd.read_parquet(pathlib.Path(__file__).resolve().parent.parent / "data" / "derived" / "field_scan.parquet", columns=["symbol", "cik"])
        m = st[st.symbol == symbol]
        cik = int(m.cik.iloc[0]) if len(m) else cik_for(symbol)
    except Exception:
        cik = cik_for(symbol)
    if cik:
        f.write_text(str(cik))
    return cik


def listing(symbol, forms=None, n=60):
    rows = _rows_cached(symbol)
    df = pd.DataFrame([{"form": r["formType"], "filed": pd.to_datetime(r["filed"]).strftime("%Y-%m-%d"),
                        "period": r.get("period"), "link": r["view"]["htmlLink"]} for r in rows])
    if df.empty:
        return df
    df = df.sort_values("filed", ascending=False).reset_index(drop=True)
    if forms:
        fs = set(forms.split(","))
        df = df[df.form.isin(fs) | df.form.str.replace("/A", "").isin(fs)]
    df = df[~df.form.isin(["3", "4", "5", "144", "SC 13G", "SC 13G/A", "SCHEDULE 13G", "SCHEDULE 13G/A"])] if not forms else df
    df = df.head(n).reset_index(drop=True)
    cik = _cik_cached(symbol)
    df["accession"] = None
    if cik:
        r = _subs_cached(cik)
        m = {}
        for a, f, d in zip(r["accessionNumber"], r["form"], r["filingDate"]):
            m.setdefault((f, d), []).append(a)
        df["accession"] = [",".join(m.get((f, d), [])) or None for f, d in zip(df.form, df.filed)]
        df.attrs["cik"] = cik
    return df


def get_text(symbol, sel, forms=None):
    df = listing(symbol, forms=None if sel.isdigit() else sel, n=100)
    if df.empty:
        raise SystemExit(f"no filings listed for {symbol}")
    row = df.iloc[int(sel)] if sel.isdigit() else df.iloc[0]
    key = hashlib.sha1(row.link.encode()).hexdigest()[:16]
    f = CACHE / f"{symbol}_{row.form.replace('/', '-').replace(' ', '')}_{row.filed}_{key}.txt"
    if not f.exists():
        f.write_text(nasdaq.filing_text(row.link))
    return f, row, df.attrs.get("cik")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd"); ap.add_argument("symbol"); ap.add_argument("sel", nargs="?"); ap.add_argument("pattern", nargs="?")
    ap.add_argument("--forms"); ap.add_argument("--n", type=int, default=40); ap.add_argument("--ctx", type=int, default=250)
    ap.add_argument("--max", type=int, default=12)
    a = ap.parse_args()
    if a.cmd == "list":
        df = listing(a.symbol, a.forms, a.n)
        print(f"CIK {df.attrs.get('cik')}")
        print(df.drop(columns="link").to_string())
    elif a.cmd == "text":
        f, row, cik = get_text(a.symbol, a.sel)
        print(f"{row.form} filed {row.filed} period {row.period} accession {row.accession} CIK {cik}\n{f}\n{f.stat().st_size} chars")
    elif a.cmd == "grep":
        f, row, cik = get_text(a.symbol, a.sel)
        t = f.read_text()
        print(f"## {a.symbol} {row.form} filed {row.filed} accession {row.accession} CIK {cik} ({len(t)} chars)")
        k = 0
        for m in re.finditer(a.pattern, t, flags=re.I):
            s, e = max(0, m.start() - a.ctx), min(len(t), m.end() + a.ctx)
            print(f"--- @{m.start()}: ...{t[s:e]}...")
            k += 1
            if k >= a.max:
                break
        print(f"({k} match(es) shown)")
    elif a.cmd == "facts":
        from ah import pit
        cik = _cik_cached(a.symbol)
        p = pit.asof_panel([pd.Timestamp.now().strftime("%Y-%m-%d")], pit.con(), ciks=[cik])
        cols = ["cik", "bs_end", "bs_known", "bs_accn", "cash_total", "debt_total", "debt_due_12m", "pref_liq", "rev_ttm", "rev_ttm_e",
                "ocf_ttm", "ocf_last2q", "runway_years", "runway_years_2q", "shares", "shares_e", "shares_src", "float_usd", "antidil",
                "CommonStockSharesAuthorized", "ClassOfWarrantOrRightOutstanding"]
        print(p[[c for c in cols if c in p.columns]].T.to_string())
