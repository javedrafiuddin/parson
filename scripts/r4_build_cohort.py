"""Section 8.2 cohort build, full run. Quarter-end bases 2012Q2..2025Q3, every CIK in the survivorship-free master.
Outputs: data/derived/cohort_bases.parquet (all qualifying bases with features inputs + labels + classes)
         data/derived/cohort_counts.json   (counts at every step, for cohort_report.md)"""
import sys, pathlib, json, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from ah import cohort, labels, store, pit, model
from ah.config import DERIVED, COST, COHORT

t0 = time.time()
dates = cohort.quarter_ends("2012-06-30", "2025-09-30")
B, log = cohort.build(dates)
counts = {"log": [(k, (int(v) if isinstance(v, (int, np.integer)) else float(v))) for k, v in log]}
c = store.connect()
B = cohort.postprocess(B, c, dates)
counts["active_filer_cik_dates"] = int(len(B))
counts["by_subset_all"] = B.subset.value_counts().to_dict()
Q = B[B.base_exact | B.base_safe].copy()
counts["qualifying_bases_exact"] = B.groupby("subset").base_exact.sum().astype(int).to_dict()
counts["qualifying_bases_safe"] = B.groupby("subset").base_safe.sum().astype(int).to_dict()

# ---- classes ----
s1 = Q.subset == "S1_PRICED"
# S2: float-implied value multiple over the next 5 years (upper-bound screen for unpriced swans)
fl = pd.read_parquet(pit.PIT / "series" / "instant.parquet")
fl = fl[fl.tag == "EntityPublicFloat"][["cik", "e", "val"]]
fl["e"] = pd.to_datetime(fl.e)
s2 = Q[~s1][["cik", "base_date", "float_usd", "float_e"]].merge(fl, on="cik", how="left")
s2 = s2[(s2.e > s2.float_e) & (s2.e <= s2.base_date + pd.Timedelta(days=int(365.25 * 5)))]
fm = (s2.assign(m=s2.val / s2.float_usd).groupby(["cik", "base_date"]).m.max().rename("float_mult_max_5y")).reset_index()
Q = Q.merge(fm, on=["cik", "base_date"], how="left")
Q = cohort.classify_all(Q)
Q["byear"] = Q.base_date.dt.year
Q.to_parquet(DERIVED / "cohort_bases.parquet", compression="zstd", index=False)

def tab(d, by):
    return {str(k): v for k, v in d.groupby(by).size().items()}
E = Q[Q.base_exact]
counts["exact_class_by_subset"] = {s: g.cls.value_counts().to_dict() for s, g in E.groupby("subset")}
counts["exact_class_by_year_S1"] = {int(y): g.cls.value_counts().to_dict() for y, g in E[E.subset == "S1_PRICED"].groupby("byear")}
counts["distinct_cik_by_class_exact"] = E.groupby("cls").cik.nunique().to_dict()
m = E[(E.subset == "S1_PRICED")]
counts["swan_25x_peak_name_dates"] = int((m.mfe_5y >= 25).sum())
counts["swan_10x_terminal_name_dates"] = int((m.term_5y >= 10).sum())
counts["swan_distinct_ciks"] = int(m[m.cls == "SWAN"].cik.nunique())
counts["elapsed_s"] = round(time.time() - t0, 1)
json.dump(counts, open(DERIVED / "cohort_counts.json", "w"), indent=1, default=str)
print(json.dumps(counts, indent=1, default=str)[:6000])
