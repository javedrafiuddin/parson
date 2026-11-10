"""Company descriptions (Nasdaq company-profile endpoint) for Stage-1 survivors. Vendor text: used ONLY as a lead
for emergent theme clustering (Section 4 'fallen leaders, discovered not assumed'), never as evidence."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah.http import get_json
from ah.config import DERIVED

st = pd.read_parquet(DERIVED / "stage1.parquet")
k = st[st.stage1.str.startswith(("PASS", "NEEDS")) & st.sec_type.isin(["common", "adr", "otc_common"])]
k = k.sort_values("adv20", ascending=False).drop_duplicates("cik")
out_f = DERIVED / "profiles.parquet"
done = pd.read_parquet(out_f) if out_f.exists() else pd.DataFrame(columns=["symbol"])
todo = k[~k.symbol.isin(done.symbol)]
print("todo", len(todo), flush=True)


def one(row):
    sym, cik = row
    try:
        j = get_json(f"https://api.nasdaq.com/api/company/{sym}/company-profile", retries=2)
        d = (j or {}).get("data") or {}
        g = lambda key: (d.get(key) or {}).get("value")
        return {"symbol": sym, "cik": cik, "description": g("CompanyDescription"), "sector": g("Sector"), "industry": g("Industry"),
                "region": g("Region"), "employees": g("Employees")}
    except Exception as e:
        return {"symbol": sym, "cik": cik, "description": None, "err": str(e)[:60]}


rows = []
items = list(zip(todo.symbol, todo.cik))
with ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(one, items)):
        rows.append(r)
        if (i + 1) % 200 == 0:
            pd.concat([done, pd.DataFrame(rows)], ignore_index=True).to_parquet(out_f, index=False)
            print(i + 1, flush=True)
df = pd.concat([done, pd.DataFrame(rows)], ignore_index=True)
df.to_parquet(out_f, index=False)
print("profiles", len(df), "with description", int(df.description.notna().sum()))
