"""PRICES table build: full daily history (2000+) from Yahoo for a list of symbols.
Usage: r2_pull_prices.py <symbols.csv with columns symbol,ysym> <outdir-name>
Resumable (done list). Writes data/prices/<name>/part-*.parquet, splits-*.parquet, meta-*.parquet"""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah import yahoo
from ah.config import PRICES

src, name = sys.argv[1], sys.argv[2]
out = PRICES / name
out.mkdir(parents=True, exist_ok=True)
DONE = out / "_done.txt"
syms = pd.read_csv(src, keep_default_na=False, dtype=str)
done = set(DONE.read_text().split("\n")) if DONE.exists() else set()
todo = syms[~syms.symbol.isin(done)].reset_index(drop=True)
print(f"symbols {len(syms)} done {len(done)} todo {len(todo)}", flush=True)
fetched_at = pd.Timestamp.now("UTC")


def one(row):
    sym, ysym = row
    df, sp, meta = yahoo.history(ysym, start="2000-01-01")
    if df is None:
        return sym, ysym, None, None, {"err": str(meta)}
    df.insert(0, "ticker", sym)
    return sym, ysym, df, sp, meta


B, t0 = 250, time.time()
for b in range(0, len(todo), B):
    chunk = list(zip(todo.symbol[b:b + B], todo.ysym[b:b + B]))
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, chunk))
    px = [r[2] for r in res if r[2] is not None]
    tagid = f"{len(done) + b:06d}"
    if px:
        d = pd.concat(px, ignore_index=True)
        d["source"] = "yahoo_chart_v8"
        d["source_timestamp"] = fetched_at
        d.to_parquet(out / f"part-{tagid}.parquet", compression="zstd", index=False)
    sp = [(r[0], s[0], s[1], s[2]) for r in res if r[3] for s in r[3]]
    if sp:
        pd.DataFrame(sp, columns=["ticker", "date", "numerator", "denominator"]).to_parquet(out / f"splits-{tagid}.parquet", index=False)
    meta = [dict(ticker=r[0], ysym=r[1], **{k: str(v) if v is not None else None for k, v in r[4].items()}) for r in res]
    pd.DataFrame(meta).to_parquet(out / f"meta-{tagid}.parquet", index=False)
    with open(DONE, "a") as fh:
        fh.write("\n".join(r[0] for r in res) + "\n")
    el = time.time() - t0
    n = b + len(chunk)
    print(f"{n}/{len(todo)} {el:.0f}s eta {el / n * (len(todo) - n) / 60:.1f}min ok {len(px)}/{len(chunk)}", flush=True)
