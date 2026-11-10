"""R3 Stage 1 (code pass over the WHOLE R2 universe): Section 5.2 hard filters computable from filed data.
Each name gets exactly one outcome: PASS, FAIL(<first failing filter>), or NEEDS_FILING_CHECK(<what>).
Writes data/derived/stage1.parquet and appends the coverage ledger rows to data/derived/coverage_ledger_r3.csv.
Nothing here is 'verified' in the Rule V sense - PASS only earns a name filing-level verification."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ah import store, ctgov, rubric
from ah.config import DERIVED, SCREEN, RUN_ASOF, DATA

ASOF = pd.Timestamp(RUN_ASOF)
c = store.connect()
u = pd.read_parquet(DERIVED / "field_scan.parquet")
u = u[u.n_damage_tests >= 1].copy()
ent = c.execute("SELECT cik, sic, sic_desc, name AS sec_name, category, former_names FROM entities").df()
u = u.merge(ent, on="cik", how="left")
u["sic"] = pd.to_numeric(u.sic, errors="coerce")
led = []
def L(step, n_in, n_out, rule):
    led.append((step, n_in, n_out, n_in - n_out, rule)); print(f"[{step}] in={n_in} out={n_out} :: {rule}", flush=True)

# ---- filing-index flags (last 12 / 36 months) ----
y1 = (ASOF - pd.DateOffset(months=12)).strftime("%Y-%m-%d")
y3 = (ASOF - pd.DateOffset(months=36)).strftime("%Y-%m-%d")
fx = c.execute(f"""SELECT cik,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%4.02%' AND filed >= '{y1}' THEN filed END) nonreliance_12m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%4.01%' AND filed >= '{y1}' THEN filed END) auditor_change_12m,
   max(CASE WHEN form LIKE 'NT 10-%' AND filed >= '{y1}' THEN filed END) nt_12m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%3.01%' AND filed >= '{y1}' THEN filed END) delist_notice_12m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%1.03%' AND filed >= '{y3}' THEN filed END) bankruptcy_36m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%2.01%' AND filed >= '{y3}' THEN filed END) acq_complete_36m,
   max(CASE WHEN (form LIKE '424B%' OR form IN ('S-1','S-1/A','S-3','S-3/A','S-3ASR','F-1','F-3')) AND filed >= '{y1}' THEN filed END) offering_doc_12m,
   max(CASE WHEN form LIKE '424B5%' AND filed >= '{y1}' THEN filed END) last_424b5,
   count(CASE WHEN form LIKE '424B%' AND filed >= '{y1}' THEN 1 END) n_424b_12m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%3.02%' AND filed >= '{y1}' THEN filed END) unreg_sale_12m,
   max(CASE WHEN form IN ('S-3','S-3/A','S-3ASR') AND filed >= '{y3}' THEN filed END) shelf_36m,
   max(CASE WHEN form IN ('DEF 14A','PRE 14A','DEFR14A') AND filed >= '{y1}' THEN filed END) proxy_12m,
   max(CASE WHEN form LIKE '8-K%' AND items LIKE '%5.02%' AND filed >= '{y1}' THEN filed END) officer_change_12m
   FROM filings GROUP BY 1""").df()
u = u.merge(fx, on="cik", how="left")
n0 = len(u)

# ---- (1) real business ----
rev_ok = u.rev_ttm >= SCREEN["ttm_rev_min"]
bio = u.sic.isin([2833, 2834, 2835, 2836, 8731, 8734, 3841, 3845, 8071])
need_ct = u[(~rev_ok)].drop_duplicates("cik")[["cik", "sec_name"]]
print("clinical-trial lookups:", len(need_ct), flush=True)
def ct(row):
    try:
        return row[0], ctgov.summarize(ctgov.sponsor_trials(row[1]))
    except Exception as e:
        return row[0], {"n_p2p3": None}
with ThreadPoolExecutor(3) as ex:
    res = dict(ex.map(ct, list(need_ct.itertuples(index=False, name=None))))
u["ct_live"] = u.cik.map(lambda k: (res.get(k) or {}).get("n_live_or_completed"))
u["ct_active"] = u.cik.map(lambda k: (res.get(k) or {}).get("n_active"))
u["ct_p3"] = u.cik.map(lambda k: (res.get(k) or {}).get("n_p3"))
u["ct_conditions"] = u.cik.map(lambda k: (res.get(k) or {}).get("n_conditions"))
u["ct_example"] = u.cik.map(lambda k: (res.get(k) or {}).get("example_nct"))
lead_ok = (~rev_ok) & (u.ct_live.fillna(0) >= 1)
u["real_business"] = np.where(rev_ok, "revenue>=5M", np.where(lead_ok, "registered Phase2+ trial", "CHECK: pre-revenue, lead asset not found by code"))

# ---- (2) survival gate (Section 5.1 runway) ----
run_ok = (u.runway_years >= SCREEN["runway_min_years"]) | (u.cash_positive.fillna(False).astype(bool))
fin_after = (pd.to_datetime(u.offering_doc_12m) > pd.to_datetime(u.bs_end)) | (pd.to_datetime(u.unreg_sale_12m) > pd.to_datetime(u.bs_end))
u["survival_gate"] = np.where(run_ok, "PASS", np.where(u.runway_years.isna() & u.ocf_ttm.isna(), "CHECK: runway not computable from XBRL",
                              np.where(fin_after.fillna(False), "CHECK: runway<12m but financing filed after balance sheet", "FAIL: runway<12m, no financing filed since")))

# ---- (3) fraud red flags from the filing index ----
u["fraud_flag"] = np.where(u.nonreliance_12m.notna(), "FAIL: 8-K item 4.02 non-reliance (restatement) within 12m",
                   np.where(u.nt_12m.notna() & (u.runway_years < 1), "FAIL: late filing (NT) with <12m runway",
                   np.where(u.auditor_change_12m.notna(), "CHECK: auditor change (8-K 4.01) within 12m", "none found")))
u.loc[u.fin_status.isin(["E", "H", "J", "K", "Q", "G"]), "fraud_flag"] = "FAIL: exchange financial-status flag " + u.fin_status
# ---- (4) reverse-split risk (flag, not exclusion) ----
u["rs_risk"] = (u.last_close < 1.0) & (u.delist_notice_12m.notna() | u.fin_status.isin(["D"]))
# ---- (5) cancelled-equity trap routing ----
u["bk_or_despac"] = np.where(u.bankruptcy_36m.notna(), "post-bankruptcy(36m): Section 5.5 form required",
                     np.where(u.former_names.fillna("").str.contains("Acquisition|SPAC|Merger Corp|Capital Corp", case=False), "deSPAC lineage: Section 5.5 form required", ""))
# ---- SPAC shells (trust assets, SIC 6770): no operating business yet ----
u["spac_shell"] = (u.sic == 6770) & (u.rev_ttm.fillna(0) < 1e6)

def outcome(r):
    if r.spac_shell:
        return "FAIL: pre-merger SPAC shell (no operating business)"
    if r.fraud_flag.startswith("FAIL"):
        return r.fraud_flag
    if r.real_business.startswith("CHECK"):
        return "NEEDS_FILING_CHECK: lead asset"
    if r.survival_gate.startswith("FAIL"):
        return r.survival_gate
    if r.survival_gate.startswith("CHECK"):
        return "NEEDS_FILING_CHECK: survival"
    return "PASS"
u["stage1"] = [outcome(r) for r in u.itertuples()]
vc = u.stage1.value_counts()
print(vc.to_string())
L("S1", n0, int((u.stage1 == "PASS").sum() + u.stage1.str.startswith("NEEDS").sum()),
  "Stage 1 code pass (Section 5.2): " + "; ".join(f"{k} = {v}" for k, v in vc.items()))

# ---- rubric inputs + survival score (quantitative part) ----
u["dd"] = u[["drawdown_3y", "issuer_drawdown_3y"]].max(axis=1)
u["n_tests"] = u.n_damage_tests
u["debt_due_to_cash"] = u.debt_due_12m / u.cash_total.where(u.cash_total > 0)
u["gross_margin"] = u.gp_ttm / u.rev_ttm.where(u.rev_ttm > 0)
u.to_parquet(DERIVED / "stage1.parquet", index=False)
pd.DataFrame(led, columns=["step", "in", "out", "cut", "rule"]).to_csv(DERIVED / "coverage_ledger_r3.csv", index=False)
print("written", len(u))
