"""Leakage and survivorship tests (Section 8.2 traps, 8.5 controls). Run: python3 -m pytest -q tests"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd, pytest
from ah import labels
from ah.config import PIT, DERIVED


def _px(n=3000, seed=0):
    r = np.random.default_rng(seed)
    d = pd.bdate_range("2012-01-02", periods=n)
    c = 10 * np.exp(np.cumsum(r.normal(0, 0.03, n)))
    return pd.DataFrame({"date": d, "close": c, "adjclose": c, "volume": 1e5})


def test_labels_use_only_forward_prices():
    """Changing prices at or before the entry session must not change any label except through entry itself;
    changing prices BEFORE the base date must change nothing."""
    px = _px()
    bd = [pd.Timestamp("2015-06-30")]
    a = labels.path_labels(px, bd)
    px2 = px.copy()
    px2.loc[px2.date < pd.Timestamp("2015-06-01"), ["close", "adjclose"]] *= 7.0
    b = labels.path_labels(px2, bd)
    pd.testing.assert_frame_equal(a, b)


def test_entry_is_next_session_not_base_day():
    px = _px()
    bd = pd.Timestamp("2015-06-30")
    a = labels.path_labels(px, [bd]).iloc[0]
    assert pd.Timestamp(a.entry_date) > bd


def test_unresolved_never_becomes_zero_or_win():
    px = _px(n=900)                      # < 5 years of forward data from the base
    a = labels.path_labels(px, [pd.Timestamp("2013-06-28")])
    assert not bool(a.resolved_5y.iloc[0]) and np.isnan(a.term_5y.iloc[0])
    cls = labels.classify(a)
    assert cls.iloc[0] in ("UNRESOLVED", "SWAN")     # SWAN only if the 25x peak already happened


def test_fwd_max_excludes_entry_day():
    a = np.array([1.0, 100.0, 2.0, 3.0])
    assert labels._fwd_max(a, 2)[1] == 3.0           # from index 1, forward window is [2, 3]


@pytest.mark.skipif(not (PIT / "series" / "ttm.parquet").exists(), reason="PIT series not built")
def test_pit_panel_never_sees_later_filings():
    """Every value in the as-of panel was filed strictly before the decision date."""
    import duckdb
    c = duckdb.connect()
    d = "2018-03-31"
    n = c.execute(f"""SELECT count(*) FROM (
        SELECT cik, tag, max(known) k FROM '{PIT}/series/instant.parquet' WHERE known < DATE '{d}' GROUP BY 1,2) WHERE k >= DATE '{d}'""").fetchone()[0]
    assert n == 0
    from ah import pit
    p = pit.asof_panel([d], pit.con(), ciks=[1800, 2488, 320193])
    assert (pd.to_datetime(p.bs_known) < pd.Timestamp(d)).all()
    assert (pd.to_datetime(p.bs_end) < pd.Timestamp(d)).all()


@pytest.mark.skipif(not (PIT / "series" / "instant.parquet").exists(), reason="PIT series not built")
def test_as_first_filed_not_restated():
    """The instant series keeps the FIRST filed value for a period: for any (cik, tag, end) there is one row and
    its 'known' date is the earliest filing date of that period in the raw facts."""
    import duckdb
    c = duckdb.connect()
    bad = c.execute(f"""
      WITH raw AS (SELECT cik, tag, CAST("end" AS DATE) e, min(CAST(filed AS DATE)) first_filed
                   FROM read_parquet('{PIT}/facts/*.parquet') WHERE start IS NULL AND tag='Assets' AND unit='USD' GROUP BY 1,2,3)
      SELECT count(*) FROM '{PIT}/series/instant.parquet' s JOIN raw USING (cik, tag, e) WHERE s.known <> raw.first_filed""").fetchone()[0]
    assert bad == 0


@pytest.mark.skipif(not (DERIVED / "cohort_bases.parquet").exists(), reason="cohort not built")
def test_cohort_contains_dead_names_and_keys_on_cik():
    b = pd.read_parquet(DERIVED / "cohort_bases.parquet")
    assert (b.subset == "S2_UNPRICED").sum() > 0, "population must include dead / unpriced CIKs"
    assert b.cik.notna().all() and not b.duplicated(["cik", "base_date"]).any()
    assert (pd.to_datetime(b.bs_known) < pd.to_datetime(b.base_date)).all()
