"""R1 step 1: survivorship-bias-free CIK master from XBRL frames.
Every entity that reported dei:EntityCommonStockSharesOutstanding or dei:EntityPublicFloat in ANY
calendar quarter 2009Q2..2026Q3 is in the master - including entities that later died.
Output: data/derived/frames_cover.parquet (cik, entity, tag, period, end, val, accn, loc)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah import edgar
from ah.config import DERIVED

periods = [f"CY{y}Q{q}I" for y in range(2009, 2027) for q in (1, 2, 3, 4)
           if not (y == 2009 and q == 1) and not (y == 2026 and q == 4)]
jobs = [("dei", "EntityCommonStockSharesOutstanding", "shares", p) for p in periods] + \
       [("dei", "EntityPublicFloat", "USD", p) for p in periods]


def pull(j):
    tax, tag, unit, p = j
    d = edgar.frame(tax, tag, unit, p, cache_ttl=24 * 5 if p >= "CY2026" else None)
    if not d:
        return pd.DataFrame()
    df = pd.DataFrame(d["data"])
    df["tag"], df["period"] = tag, p
    return df


with ThreadPoolExecutor(6) as ex:
    parts = list(ex.map(pull, jobs))
df = pd.concat([p for p in parts if len(p)], ignore_index=True)
df = df.rename(columns={"entityName": "entity"})
df.to_parquet(DERIVED / "frames_cover.parquet", compression="zstd", index=False)
print("rows", len(df), "unique CIKs", df.cik.nunique())
print(df.groupby(["tag"]).cik.nunique())
print(df[df.tag == "EntityCommonStockSharesOutstanding"].groupby("period").cik.nunique().iloc[::8])
