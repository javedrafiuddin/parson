"""Point-in-time fundamentals from the as-first-filed XBRL facts table.

Pipeline (all DuckDB SQL over data/pit/facts/*.parquet):
  1. first-filed version of every (cik, tag, start, end)            -> 'as originally filed'
  2. duration facts -> discrete fiscal quarters (direct 3-month facts, else YTD differences);
     each derived quarter carries known = max(filed of its components)
  3. TTM = sum of 4 consecutive discrete quarters (FY value as fallback); last-2-quarter sum for burn
  4. PIT-monotone series: ordered by 'known', keep only rows whose period end is the running maximum
  5. as-of join to decision dates with STRICT inequality known < decision_date  (usable next session after filing)
"""
import duckdb
import pandas as pd
from .config import PIT, DERIVED
from . import tags as T

DUR_USD = sorted(set(T.REVENUE + T.CASHFLOW + T.INCOME))
INST_USD = sorted(set(T.CASH + T.DEBT + T.BALANCE + ["PreferredStockLiquidationPreferenceValue", "PreferredStockValue",
                                                      "TemporaryEquityCarryingAmountAttributableToParent",
                                                      "WarrantsAndRightsOutstanding", "DerivativeLiabilities"])
                  - {"CashAndCashEquivalentsPeriodIncreaseDecrease"}) + ["EntityPublicFloat"]
INST_SH = ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding", "CommonStockSharesIssued",
           "CommonStockSharesAuthorized", "ClassOfWarrantOrRightOutstanding", "PreferredStockSharesOutstanding",
           "TemporaryEquitySharesOutstanding",
           "ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingNumber",
           "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsNonvestedNumber",
           "ShareBasedCompensationArrangementByShareBasedPaymentAwardNumberOfSharesAvailableForGrant"]
DUR_SH = ["WeightedAverageNumberOfSharesOutstandingBasic", "WeightedAverageNumberOfDilutedSharesOutstanding",
          "AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount", "StockIssuedDuringPeriodSharesNewIssues"]


def con():
    c = duckdb.connect()
    c.execute("PRAGMA threads=4; PRAGMA memory_limit='10GB'")
    c.execute(f"CREATE VIEW facts AS SELECT * FROM read_parquet('{PIT}/facts/*.parquet')")
    c.execute(f"CREATE VIEW filings AS SELECT * FROM read_parquet('{PIT}/filings/*.parquet')")
    c.execute(f"CREATE VIEW entities AS SELECT * FROM read_parquet('{PIT}/entities/*.parquet')")
    return c


def _inlist(xs):
    return ",".join("'" + x + "'" for x in xs)


def build(c=None, out=None):
    """Materialise the PIT-monotone instant and TTM series to data/pit/series/."""
    c = c or con()
    out = out or (PIT / "series")
    out.mkdir(parents=True, exist_ok=True)
    # ---- instants (USD + share counts): first-filed value per period, then PIT-monotone ----
    c.execute(f"""
    CREATE OR REPLACE TEMP TABLE inst0 AS
    SELECT cik, tag, CAST("end" AS DATE) e, val, CAST(filed AS DATE) known, accn, form
    FROM facts
    WHERE start IS NULL AND val IS NOT NULL AND (
          (unit='USD' AND tag IN ({_inlist(INST_USD)})) OR (unit='shares' AND tag IN ({_inlist(INST_SH)})))
    QUALIFY row_number() OVER (PARTITION BY cik, tag, "end" ORDER BY filed, val DESC) = 1""")
    c.execute(f"""
    COPY (
      WITH a AS (SELECT * FROM inst0 QUALIFY row_number() OVER (PARTITION BY cik, tag, known ORDER BY e DESC) = 1)
      SELECT * FROM a
      QUALIFY e >= max(e) OVER (PARTITION BY cik, tag ORDER BY known ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      ORDER BY cik, tag, known
    ) TO '{out}/instant.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    # ---- durations -> discrete quarters ----
    c.execute(f"""
    CREATE OR REPLACE TEMP TABLE dur0 AS
    SELECT cik, tag, CAST(start AS DATE) s, CAST("end" AS DATE) e, val, CAST(filed AS DATE) filed, accn,
           date_diff('day', CAST(start AS DATE), CAST("end" AS DATE)) + 1 AS d
    FROM facts
    WHERE start IS NOT NULL AND val IS NOT NULL AND (
          (unit='USD' AND tag IN ({_inlist(DUR_USD)})) OR (unit='shares' AND tag IN ({_inlist(DUR_SH)})))
    QUALIFY row_number() OVER (PARTITION BY cik, tag, start, "end" ORDER BY filed) = 1""")
    c.execute("""
    CREATE OR REPLACE TEMP TABLE q0 AS
    WITH c AS (SELECT *, CAST(round(d / 91.3) AS INT) k FROM dur0
               WHERE d BETWEEN 75 AND 385 AND abs(d - round(d / 91.3) * 91.3) < 17),
    x AS (SELECT *, lag(val) OVER w pv, lag(k) OVER w pk, lag(filed) OVER w pf
          FROM c WINDOW w AS (PARTITION BY cik, tag, s ORDER BY e))
    SELECT cik, tag, e,
           CASE WHEN k = 1 THEN val WHEN pk = k - 1 THEN val - pv END AS q,
           CASE WHEN k = 1 THEN filed ELSE greatest(filed, pf) END AS known,
           (k = 1) AS direct, accn
    FROM x WHERE k = 1 OR pk = k - 1""")
    c.execute("""
    CREATE OR REPLACE TEMP TABLE q1 AS
    SELECT * FROM q0 QUALIFY row_number() OVER (PARTITION BY cik, tag, e ORDER BY direct DESC, known) = 1""")
    # TTM: 4 consecutive quarters; FY fallback; last-2-quarter sum
    c.execute("""
    CREATE OR REPLACE TEMP TABLE ttm0 AS
    WITH w AS (
      SELECT cik, tag, e, q, known, accn,
             q + lag(q,1) OVER p + lag(q,2) OVER p + lag(q,3) OVER p AS ttm4,
             greatest(known, lag(known,1) OVER p, lag(known,2) OVER p, lag(known,3) OVER p) AS known4,
             date_diff('day', lag(e,3) OVER p, e) AS span4,
             q + lag(q,1) OVER p AS s2, greatest(known, lag(known,1) OVER p) AS known2,
             date_diff('day', lag(e,1) OVER p, e) AS span2
      FROM q1 WINDOW p AS (PARTITION BY cik, tag ORDER BY e))
    SELECT cik, tag, e, ttm4 AS ttm, known4 AS known, 'Q4SUM' AS method, accn,
           CASE WHEN span2 BETWEEN 80 AND 100 THEN s2 END AS last2q, q AS lastq
    FROM w WHERE span4 BETWEEN 255 AND 290 AND ttm4 IS NOT NULL
    UNION ALL
    SELECT cik, tag, e, val, filed, 'FY', accn, NULL, NULL FROM dur0 WHERE d BETWEEN 350 AND 385""")
    c.execute(f"""
    COPY (
      WITH a AS (SELECT * FROM ttm0 QUALIFY row_number() OVER (PARTITION BY cik, tag, e ORDER BY (method='Q4SUM') DESC, known) = 1),
           b AS (SELECT * FROM a QUALIFY row_number() OVER (PARTITION BY cik, tag, known ORDER BY e DESC) = 1)
      SELECT * FROM b
      QUALIFY e >= max(e) OVER (PARTITION BY cik, tag ORDER BY known ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      ORDER BY cik, tag, known
    ) TO '{out}/ttm.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    n1 = c.execute(f"SELECT count(*) FROM '{out}/instant.parquet'").fetchone()[0]
    n2 = c.execute(f"SELECT count(*) FROM '{out}/ttm.parquet'").fetchone()[0]
    return n1, n2


def _g(c, expr):  # greatest ignoring NULLs -> NULL if all NULL
    return f"nullif(greatest({','.join('coalesce(' + e + ',-1e30)' for e in expr)}), -1e30)"


def asof_panel(dates, c=None, ciks=None, stale_days=460):
    """One row per (cik, decision date) with fundamentals known STRICTLY BEFORE the decision date.
    Values older than `stale_days` (period end) are dropped as stale. Returns a pandas DataFrame."""
    c = c or con()
    s = PIT / "series"
    c.execute("CREATE OR REPLACE TEMP TABLE dd AS SELECT CAST(d AS DATE) d FROM (SELECT unnest(?) d)", [list(dates)])
    cikf = "" if ciks is None else f"WHERE cik IN ({','.join(str(int(x)) for x in ciks)})"
    # latest known row per (cik, tag) at each date, for instants and ttm
    c.execute(f"""
    CREATE OR REPLACE TEMP TABLE ai AS
    SELECT dd.d, i.cik, i.tag, arg_max(i.val, i.known) val, arg_max(i.e, i.known) e, max(i.known) known, arg_max(i.accn, i.known) accn
    FROM dd JOIN (SELECT * FROM '{s}/instant.parquet' {cikf}) i ON i.known < dd.d
    GROUP BY 1,2,3 HAVING date_diff('day', arg_max(i.e, i.known), dd.d) <= CASE WHEN i.tag='EntityPublicFloat' THEN 650 ELSE {stale_days} END""")
    c.execute(f"""
    CREATE OR REPLACE TEMP TABLE att AS
    SELECT dd.d, t.cik, t.tag, arg_max(t.ttm, t.known) ttm, arg_max(t.e, t.known) e, max(t.known) known,
           arg_max(t.last2q, t.known) last2q, arg_max(t.method, t.known) method
    FROM dd JOIN (SELECT * FROM '{s}/ttm.parquet' {cikf}) t ON t.known < dd.d
    GROUP BY 1,2,3 HAVING date_diff('day', arg_max(t.e, t.known), dd.d) <= {stale_days}""")
    # balance-sheet anchor date per (cik,d): latest end among Assets / cash tags
    c.execute("""CREATE OR REPLACE TEMP TABLE anchor AS
                 SELECT d, cik, max(e) bs_end, max(known) bs_known, arg_max(accn, e) bs_accn
                 FROM ai WHERE tag IN ('Assets','CashAndCashEquivalentsAtCarryingValue','Liabilities','StockholdersEquity',
                                       'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents','Cash') GROUP BY 1,2""")
    # pivot instants, keeping only values at (or within 10 days of) the anchor balance-sheet date
    piv_tags = [t for t in INST_USD if t != "EntityPublicFloat"]
    cols = ",".join(f"max(CASE WHEN tag='{t}' THEN val END) AS \"{t}\"" for t in piv_tags)
    c.execute(f"""CREATE OR REPLACE TEMP TABLE bi AS
                  SELECT ai.d, ai.cik, {cols} FROM ai JOIN anchor a USING (d, cik)
                  WHERE ai.tag IN ({_inlist(piv_tags)}) AND abs(date_diff('day', ai.e, a.bs_end)) <= 10 GROUP BY 1,2""")
    sh = ",".join(f"max(CASE WHEN tag='{t}' THEN val END) AS \"{t}\", max(CASE WHEN tag='{t}' THEN e END) AS \"{t}_e\"" for t in INST_SH + ["EntityPublicFloat"])
    c.execute(f"CREATE OR REPLACE TEMP TABLE si AS SELECT d, cik, {sh} FROM ai WHERE tag IN ({_inlist(INST_SH + ['EntityPublicFloat'])}) GROUP BY 1,2")

    def best(tags_, name, col="ttm"):  # among alternative tags choose the one with the latest period end
        return f"""SELECT d, cik, arg_max({col}, e) AS {name}, max(e) AS {name}_e, arg_max(method, e) AS {name}_m
                   FROM att WHERE tag IN ({_inlist(tags_)}) AND {col} IS NOT NULL GROUP BY 1,2"""
    c.execute(f"CREATE OR REPLACE TEMP TABLE r_rev AS {best(T.REVENUE, 'rev_ttm')}")
    c.execute(f"CREATE OR REPLACE TEMP TABLE r_ocf AS {best(['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'], 'ocf_ttm')}")
    c.execute(f"CREATE OR REPLACE TEMP TABLE r_ocf2 AS {best(['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'], 'ocf_last2q', 'last2q')}")
    one = lambda tag, name: f"(SELECT d, cik, ttm AS {name} FROM att WHERE tag='{tag}') USING (d, cik)"
    q = f"""
    SELECT a.d AS date, a.cik, a.bs_end, a.bs_known, a.bs_accn, bi.*, si.*,
           r_rev.rev_ttm, r_rev.rev_ttm_e, r_rev.rev_ttm_m, r_ocf.ocf_ttm, r_ocf.ocf_ttm_e, r_ocf2.ocf_last2q,
           fin.fin_ttm, ni.ni_ttm, gp.gp_ttm, rd.rd_ttm, oi.oi_ttm, iss.iss_ttm, iss2.iss2_ttm, wb.wavg_basic, wd.wavg_diluted, ad.antidil
    FROM anchor a
    LEFT JOIN bi USING (d, cik) LEFT JOIN si USING (d, cik)
    LEFT JOIN r_rev USING (d, cik) LEFT JOIN r_ocf USING (d, cik) LEFT JOIN r_ocf2 USING (d, cik)
    LEFT JOIN {one('NetCashProvidedByUsedInFinancingActivities','fin_ttm')} fin
    """
    # (simple single-tag joins)
    q = f"""
    WITH fin AS (SELECT d, cik, ttm fin_ttm FROM att WHERE tag='NetCashProvidedByUsedInFinancingActivities'),
         ni  AS (SELECT d, cik, arg_max(ttm, e) ni_ttm FROM att WHERE tag IN ('NetIncomeLoss','ProfitLoss') GROUP BY 1,2),
         gp  AS (SELECT d, cik, ttm gp_ttm FROM att WHERE tag='GrossProfit'),
         rd  AS (SELECT d, cik, ttm rd_ttm FROM att WHERE tag='ResearchAndDevelopmentExpense'),
         oi  AS (SELECT d, cik, ttm oi_ttm FROM att WHERE tag='OperatingIncomeLoss'),
         iss AS (SELECT d, cik, max(ttm) iss_ttm FROM att WHERE tag IN ('ProceedsFromIssuanceOfCommonStock','ProceedsFromIssuanceOrSaleOfEquity','ProceedsFromIssuanceOfPrivatePlacement') GROUP BY 1,2),
         cv  AS (SELECT d, cik, ttm cvt_ttm FROM att WHERE tag='ProceedsFromConvertibleNotesPayable'),
         wb  AS (SELECT d, cik, arg_max(ttm, e)/4.0 wavg_basic_ttm, arg_max(last2q, e)/2.0 wavg_basic_2q FROM att WHERE tag='WeightedAverageNumberOfSharesOutstandingBasic' GROUP BY 1,2),
         ad  AS (SELECT d, cik, arg_max(ttm, e)/4.0 antidil FROM att WHERE tag='AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount' GROUP BY 1,2)
    SELECT a.d AS date, a.cik, a.bs_end, a.bs_known, a.bs_accn, bi.* EXCLUDE (d, cik), si.* EXCLUDE (d, cik),
           r_rev.rev_ttm, r_rev.rev_ttm_e, r_rev.rev_ttm_m, r_ocf.ocf_ttm, r_ocf.ocf_ttm_e, r_ocf2.ocf_last2q,
           fin.fin_ttm, ni.ni_ttm, gp.gp_ttm, rd.rd_ttm, oi.oi_ttm, iss.iss_ttm, cv.cvt_ttm,
           wb.wavg_basic_ttm, wb.wavg_basic_2q, ad.antidil
    FROM anchor a
    LEFT JOIN bi USING (d, cik) LEFT JOIN si USING (d, cik)
    LEFT JOIN r_rev USING (d, cik) LEFT JOIN r_ocf USING (d, cik) LEFT JOIN r_ocf2 USING (d, cik)
    LEFT JOIN fin USING (d, cik) LEFT JOIN ni USING (d, cik) LEFT JOIN gp USING (d, cik) LEFT JOIN rd USING (d, cik)
    LEFT JOIN oi USING (d, cik) LEFT JOIN iss USING (d, cik) LEFT JOIN cv USING (d, cik)
    LEFT JOIN wb USING (d, cik) LEFT JOIN ad USING (d, cik)"""
    df = c.execute(q).df()
    return derive(df)


def derive(df):
    """Section 5.1 quantities from the raw as-of panel (pure pandas; NaN-aware)."""
    import numpy as np
    f = lambda *cols: df[[c for c in cols if c in df.columns]]
    mx = lambda *cols: f(*cols).max(axis=1, skipna=True)
    sm = lambda *cols: f(*cols).sum(axis=1, skipna=True, min_count=1)
    cash = mx("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash")
    sti = mx("ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesCurrent",
             "AvailableForSaleSecuritiesDebtSecuritiesCurrent")
    df["cash_total"] = pd.concat([cash.fillna(0) + sti.fillna(0), df.get("CashCashEquivalentsAndShortTermInvestments")], axis=1).max(axis=1, skipna=True)
    df.loc[cash.isna() & sti.isna() & df.get("CashCashEquivalentsAndShortTermInvestments").isna(), "cash_total"] = np.nan
    a = df.get("DebtLongtermAndShorttermCombinedAmount")
    b = sm("LongTermDebt", "ShortTermBorrowings")
    c_ = sm("LongTermDebtNoncurrent", "LongTermDebtCurrent", "ShortTermBorrowings")
    c2 = sm("LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsCurrent")
    conv = pd.concat([df.get("ConvertibleNotesPayable"), sm("ConvertibleNotesPayableCurrent", "ConvertibleNotesPayableNoncurrent"),
                      df.get("ConvertibleDebt"), sm("ConvertibleDebtCurrent", "ConvertibleDebtNoncurrent")], axis=1).max(axis=1, skipna=True)
    notes = pd.concat([df.get("NotesPayable"), sm("NotesPayableCurrent", "LongTermNotesPayable")], axis=1).max(axis=1, skipna=True)
    d_ = pd.concat([conv, notes, df.get("LineOfCredit"), df.get("SeniorNotes"), df.get("SecuredDebt")], axis=1).sum(axis=1, skipna=True, min_count=1)
    df["debt_total"] = pd.concat([a, b, c_, c2, d_, df.get("DebtInstrumentCarryingAmount")], axis=1).max(axis=1, skipna=True).fillna(0.0)
    df["conv_debt"] = conv.fillna(0.0)
    due = pd.concat([df.get("DebtCurrent"), sm("LongTermDebtCurrent", "ShortTermBorrowings"),
                     sm("ConvertibleNotesPayableCurrent", "NotesPayableCurrent", "ConvertibleDebtCurrent"),
                     df.get("LongTermDebtAndCapitalLeaseObligationsCurrent"),
                     df.get("LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths")], axis=1).max(axis=1, skipna=True)
    df["debt_due_12m"] = due.fillna(0.0)
    df["pref_liq"] = pd.concat([df.get("PreferredStockLiquidationPreferenceValue"), df.get("TemporaryEquityCarryingAmountAttributableToParent"),
                                df.get("PreferredStockValue")], axis=1).max(axis=1, skipna=True).fillna(0.0)
    # burn: TTM operating cash flow (negative = burn); runway per Section 5.1
    burn = -df["ocf_ttm"]
    df["burn_ttm"] = burn.where(burn > 0)
    df["cash_positive"] = df["ocf_ttm"] > 0
    df["runway_years"] = ((df["cash_total"] - df["debt_due_12m"]) / df["burn_ttm"]).where(df["burn_ttm"] > 0)
    df.loc[df["cash_positive"], "runway_years"] = np.inf
    burn2 = -df["ocf_last2q"] * 2.0
    df["runway_years_2q"] = ((df["cash_total"] - df["debt_due_12m"]) / burn2).where(burn2 > 0)
    # shares: cover count if recent, else balance-sheet count, else weighted average
    cov, cov_e = df.get("EntityCommonStockSharesOutstanding"), pd.to_datetime(df.get("EntityCommonStockSharesOutstanding_e"))
    d = pd.to_datetime(df["date"])
    fresh = (d - cov_e).dt.days <= 250
    df["shares"] = cov.where(fresh & (cov > 0))
    df["shares_e"] = cov_e.where(fresh & (cov > 0))
    alt = df.get("CommonStockSharesOutstanding")
    alt_e = pd.to_datetime(df.get("CommonStockSharesOutstanding_e"))
    use_alt = df["shares"].isna() & (alt > 0) & ((d - alt_e).dt.days <= 250)
    df.loc[use_alt, "shares"] = alt[use_alt]
    df.loc[use_alt, "shares_e"] = alt_e[use_alt]
    use_w = df["shares"].isna() & (df["wavg_basic_2q"] > 0)
    df.loc[use_w, "shares"] = df["wavg_basic_2q"][use_w]
    df.loc[use_w, "shares_e"] = pd.to_datetime(df["ocf_ttm_e"])[use_w]
    df["shares_src"] = np.where(fresh & (cov > 0), "cover", np.where(use_alt, "balance_sheet", np.where(use_w, "wavg", None)))
    df["float_usd"] = df.get("EntityPublicFloat")
    df["float_e"] = pd.to_datetime(df.get("EntityPublicFloat_e"))
    return df
