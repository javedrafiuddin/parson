"""Price-derived quantities from the PRICES table (current snapshot + point-in-time helpers)."""
import numpy as np
import pandas as pd
from . import store


def snapshot(asof="2026-11-10", c=None):
    """Per ticker: last close/date, 20d ADV$, split-adjusted 3-year high and drawdown (Section 5.1),
    history length, 52w stats. Uses closes strictly before/at `asof`."""
    c = c or store.connect()
    q = f"""
    WITH p AS (SELECT ticker, date, close, volume FROM prices WHERE date <= DATE '{asof}' AND close IS NOT NULL),
    l AS (SELECT ticker, max(date) last_date, count(*) n_days, min(date) first_date FROM p GROUP BY 1),
    r AS (SELECT p.*, row_number() OVER (PARTITION BY ticker ORDER BY date DESC) rn FROM p),
    a AS (SELECT ticker, avg(close * volume) adv20, median(close * volume) med_dv20, sum(CASE WHEN volume > 0 THEN 1 ELSE 0 END) traded20
          FROM r WHERE rn <= 20 GROUP BY 1),
    a60 AS (SELECT ticker, avg(close * volume) adv60 FROM r WHERE rn <= 60 GROUP BY 1),
    h AS (SELECT ticker, max(close) high_3y, arg_max(date, close) high_3y_date, min(close) low_3y FROM p
          WHERE date > DATE '{asof}' - INTERVAL 3 YEAR GROUP BY 1),
    h1 AS (SELECT ticker, max(close) high_1y, min(close) low_1y FROM p WHERE date > DATE '{asof}' - INTERVAL 1 YEAR GROUP BY 1),
    x AS (SELECT ticker, close last_close FROM r WHERE rn = 1),
    m6 AS (SELECT ticker, arg_max(close, date) c6 FROM p WHERE date <= DATE '{asof}' - INTERVAL 6 MONTH GROUP BY 1),
    m12 AS (SELECT ticker, arg_max(close, date) c12 FROM p WHERE date <= DATE '{asof}' - INTERVAL 12 MONTH GROUP BY 1)
    SELECT l.*, x.last_close, a.adv20, a.med_dv20, a.traded20, a60.adv60, h.high_3y, h.high_3y_date, h.low_3y, h1.high_1y, h1.low_1y,
           1 - x.last_close / h.high_3y AS drawdown_3y, x.last_close / m6.c6 - 1 AS ret_6m, x.last_close / m12.c12 - 1 AS ret_12m
    FROM l JOIN x USING (ticker) LEFT JOIN a USING (ticker) LEFT JOIN a60 USING (ticker) LEFT JOIN h USING (ticker)
    LEFT JOIN h1 USING (ticker) LEFT JOIN m6 USING (ticker) LEFT JOIN m12 USING (ticker)"""
    return c.execute(q).df()


def split_factor_after(c=None):
    """ticker, date -> product of (numerator/denominator) for splits strictly AFTER date.
    unadjusted_close = close * factor ; shares-as-filed on `date` are consistent with unadjusted_close."""
    c = c or store.connect()
    return c.execute("SELECT ticker, date, numerator, denominator FROM splits").df()
