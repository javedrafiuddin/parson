"""Live quote + summary (bid, ask, last, volume, average volume) from api.nasdaq.com for a list of symbols.
Used for instruments whose Yahoo history is thin (warrants) and for bid/ask spreads at any stage.
Usage: r2_pull_quotes.py <sec_type or 'file:path.csv'> <out-name>   -> data/derived/quotes_<out-name>.parquet"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah import nasdaq
from ah.http import get_json
from ah.config import DERIVED

sel, name = sys.argv[1], sys.argv[2]
f = pd.read_csv(DERIVED / "field_listed_all.csv", keep_default_na=False, dtype=str)
if sel.startswith("file:"):
    want = pd.read_csv(sel[5:], keep_default_na=False, dtype=str).symbol.tolist()
    f = f[f.symbol.isin(want)]
else:
    f = f[f.sec_type.isin(sel.split(","))]
ts = pd.Timestamp.now("UTC")


def one(row):
    sym, cqs = row
    q = cqs if cqs else sym                      # NYSE-family instruments quote under the CQS symbol (e.g. AMPX.WS)
    out = {"symbol": sym, "quote_symbol": q, "fetched_utc": ts}
    try:
        i = nasdaq.quote(q)
        p, s = i["primaryData"], i["secondaryData"]
        out.update(name=i["name"], last=p["last"], bid=p["bid"], ask=p["ask"], quote_ts=p["ts"], volume=p["volume"],
                   realtime=p["realtime"], close_last=(s or {}).get("last"), close_ts=(s or {}).get("ts"))
    except Exception as e:
        out["err"] = str(e)[:80]
    try:
        j = get_json(f"https://api.nasdaq.com/api/quote/{q}/summary", params={"assetclass": "stocks"})
        sd = ((j or {}).get("data") or {}).get("summaryData") or {}
        g = lambda k: nasdaq._num((sd.get(k) or {}).get("value"))
        out.update(avg_volume=g("AverageVolume"), prev_close=g("PreviousClose"), mcap_summary=g("MarketCap"),
                   hi_lo_52w=(sd.get("FiftTwoWeekHighLow") or {}).get("value"))
    except Exception as e:
        out["err2"] = str(e)[:80]
    return out


with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(one, list(zip(f.symbol, f.cqs))))
df = pd.DataFrame(rows)
df.to_parquet(DERIVED / f"quotes_{name}.parquet", index=False)
px = df["last"].fillna(df.get("prev_close"))
df["adv_usd"] = df.avg_volume * px
print(len(df), "quoted:", int(df["last"].notna().sum()), "with avg volume:", int(df.avg_volume.notna().sum()),
      "ADV>=50k:", int((df.adv_usd >= 5e4).sum()), "ADV>=250k:", int((df.adv_usd >= 2.5e5).sum()))
