#!/usr/bin/env python3
"""Compact verification sheet per symbol: filed XBRL values with period + accession, filing-index events, and
short regex-confirmed text items from the latest 10-Q / 10-K. Usage: r5_sheet.py SYM [SYM...]"""
import sys, re, pathlib, importlib.util, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pandas as pd, numpy as np
from ah import store, tags as T
spec = importlib.util.spec_from_file_location("filing", str(pathlib.Path(__file__).parent / "filing.py"))
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
c = store.connect()
st = pd.read_parquet("data/derived/stage1.parquet").drop_duplicates("symbol").set_index("symbol")
_pp = pathlib.Path("data/pit/series/instant.parquet")
INST = pd.read_parquet(_pp if _pp.exists() else "data/derived/pit_finalists_instant.parquet")
TTM = pd.read_parquet("data/pit/series/ttm.parquet" if _pp.exists() else "data/derived/pit_finalists_ttm.parquet")
M = lambda v: "n/a" if v is None or pd.isna(v) else f"{v/1e6:,.1f}"
TXT = [("going-concern", r"substantial doubt[^.]{0,160}", 1), ("ATM", r"(at[- ]the[- ]market|equity distribution agreement)[^.]{0,200}", 1),
       ("convert", r"conver(sion|tible)[^.]{0,60}(price|rate) of[^.]{0,120}", 2), ("antidilutive", r"anti-?dilutive[^.]{0,90}\.[^.]{0,230}", 1),
       ("warrants", r"warrants? (to purchase|outstanding)[^.]{0,170}", 1), ("backlog", r"(contracted )?backlog (of|was|totaled|as of)[^.]{0,170}", 1),
       ("covenant", r"(in compliance with|not in compliance|waiver|event of default)[^.]{0,150}covenant[^.]{0,80}|covenants?[^.]{0,60}(in compliance|waiver|breach)[^.]{0,80}", 1),
       ("listing", r"(minimum bid price|continued listing|reverse stock split)[^.]{0,170}", 1), ("buyback", r"(repurchase[d]?)[^.]{0,40}shares[^.]{0,150}", 1)]
for s in sys.argv[1:]:
    r = st.loc[s]; cik = int(r.cik)
    print(f"=== {s} {r['name'][:40]} | CIK {cik} | ${r.last_close:.3f} ({str(r.last_date)[:10]}) | 3y high ${r.high_3y:.2f} {str(r.high_3y_date)[:10]} | dd {r.drawdown_3y:.1%} | ADV ${r.adv20/1e6:.1f}M | mcap ${M(r.mcap)}M")
    i = INST[INST.cik == cik]; e = i[i.tag.isin(["Assets", "Liabilities", "StockholdersEquity"])].e.max()
    cur = i[i.e >= e - pd.Timedelta(days=10)].sort_values("known").drop_duplicates("tag", keep="last")
    acc = cur.accn.mode().iloc[0] if len(cur) else None
    print(f" BS {str(e)[:10]} acc {acc}: " + "; ".join(f"{t.replace('CashAndCashEquivalentsAtCarryingValue','Cash').replace('StockholdersEquity','Equity')}={M(v)}" for t, v in zip(cur.tag, cur.val)
          if t in set(T.CASH + T.DEBT + ["Assets", "Liabilities", "LiabilitiesCurrent", "AssetsCurrent", "StockholdersEquity", "PreferredStockValue", "TemporaryEquityCarryingAmountAttributableToParent", "Goodwill"]) and abs(v) > 0))
    sh = i[i.tag.isin(["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding", "CommonStockSharesAuthorized", "ClassOfWarrantOrRightOutstanding",
                       "ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingNumber", "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsNonvestedNumber"])]
    sh = sh.sort_values("e").drop_duplicates("tag", keep="last")
    print(" SHARES: " + "; ".join(f"{t.replace('ShareBasedCompensationArrangementByShareBasedPaymentAward','').replace('EntityCommonStockSharesOutstanding','Cover')}={v:,.0f}@{str(d)[:10]}" for t, v, d in zip(sh.tag, sh.val, sh.e)))
    t = TTM[TTM.cik == cik].sort_values("e")
    lt = t.drop_duplicates("tag", keep="last")
    lt = lt[lt.e >= lt.e.max() - pd.Timedelta(days=200)]
    keep = set(T.REVENUE) | {"NetCashProvidedByUsedInOperatingActivities", "NetIncomeLoss", "GrossProfit", "OperatingIncomeLoss", "InterestExpense", "NetCashProvidedByUsedInFinancingActivities", "PaymentsToAcquirePropertyPlantAndEquipment", "ResearchAndDevelopmentExpense"}
    print(" TTM: " + "; ".join(f"{g.replace('NetCashProvidedByUsedIn','CF_').replace('RevenueFromContractWithCustomerExcludingAssessedTax','Rev606')}={M(v)}({str(d)[:7]},{m})" for g, v, d, m in zip(lt.tag, lt.ttm, lt.e, lt.method) if g in keep))
    rv = t[t.tag.isin(T.REVENUE)]
    if len(rv):
        tag = rv.groupby("tag").e.max().idxmax(); h = rv[rv.tag == tag].drop_duplicates("e", keep="last").tail(9)
        print(f" REV TTM history [{tag[:30]}]: " + ", ".join(f"{str(d)[:7]}:{M(v)}" for d, v in zip(h.e, h.ttm)))
    oc = t[t.tag == "NetCashProvidedByUsedInOperatingActivities"].drop_duplicates("e", keep="last").tail(6)
    print(" OCF TTM history: " + ", ".join(f"{str(d)[:7]}:{M(v)}" for d, v in zip(oc.e, oc.ttm)))
    fx = c.execute("SELECT form, filed, items FROM filings WHERE cik = ? AND CAST(filed AS DATE) >= DATE '2025-11-10' AND form NOT IN ('4','3','5','144')", [cik]).df()
    it = pd.Series([x for v in fx[fx.form.str.startswith("8-K")]["items"].fillna("") for x in v.split(",") if x]).value_counts().to_dict()
    ev = fx[fx.form.str.contains("424B|S-3|S-1|NT 10|DEF 14A|PRE 14A|SC TO|DEFM|15-12|^25", regex=True)].sort_values("filed", ascending=False)
    print(f" 12m FILINGS: 8-K items {it}; other: " + ", ".join(f"{a} {b}" for a, b in zip(ev.form.head(8), ev.filed.head(8))))
    try:
        f, row, _ = F.get_text(s, "10-Q"); tx = f.read_text()
        print(f" TEXT [{row.form} filed {row.filed} acc {row.accession}]")
        for lab, pat, mx in TXT:
            k = 0
            for m in re.finditer(pat, tx, flags=re.I):
                print(f"  {lab}: {m.group(0)[:250]}"); k += 1
                if k >= mx: break
    except BaseException as ex:
        print(" TEXT not retrieved:", str(ex)[:60])
