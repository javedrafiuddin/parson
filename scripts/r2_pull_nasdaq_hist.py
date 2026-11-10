"""Daily history from api.nasdaq.com for instruments whose Yahoo history is thin (Nasdaq-listed warrants).
Usage: r2_pull_nasdaq_hist.py <symbols.csv with column symbol> <outdir-name>"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah import nasdaq
from ah.config import PRICES

src, name = sys.argv[1], sys.argv[2]
out = PRICES / name
out.mkdir(parents=True, exist_ok=True)
syms = pd.read_csv(src, keep_default_na=False, dtype=str).symbol.tolist()
ts = pd.Timestamp.now("UTC")


def one(s):
    try:
        d = nasdaq.historical(s, start="2016-11-10", end="2026-11-10")
    except Exception as e:
        return None
    if d is None or d.empty:
        return None
    d = d.rename(columns={"date": "date"})
    d["ticker"] = s
    d["adjclose"] = d["close"]
    d["volume"] = d["volume"].fillna(0.0)
    return d[["ticker", "date", "open", "high", "low", "close", "adjclose", "volume"]]


with ThreadPoolExecutor(4) as ex:
    parts = [p for p in ex.map(one, syms) if p is not None]
df = pd.concat(parts, ignore_index=True)
df["source"] = "nasdaq_historical"
df["source_timestamp"] = ts
df.to_parquet(out / "part-000000.parquet", compression="zstd", index=False)
pd.DataFrame({"ticker": [p.ticker.iloc[0] for p in parts], "ysym": [p.ticker.iloc[0] for p in parts]}).to_parquet(out / "meta-000000.parquet", index=False)
print("symbols", len(syms), "with history", len(parts), "rows", len(df))
