"""Yahoo chart API: daily OHLCV, split/dividend-adjusted close, split events. Covers CURRENTLY quoted
symbols only - most delisted tickers are purged by Yahoo (measured in cohort_report.md). Delayed quotes."""
import datetime as dt
import pandas as pd
from .http import get_json, HttpError

U = "https://query1.finance.yahoo.com/v8/finance/chart/{}"


def to_yahoo(symbol):
    """Exchange (ACT/CQS) symbol -> Yahoo symbol.  AAC.W->AAC-WT, AAC.U->AAC-UN, ABR$D->ABR-PD, BRK.A->BRK-A"""
    s = symbol.strip()
    if "$" in s:
        base, suf = s.split("$", 1)
        return f"{base}-P{suf.replace('.', '-')}" if suf else f"{base}-P"
    if "." in s:
        base, suf = s.split(".", 1)
        m = {"W": "WT", "WS": "WT", "U": "UN", "R": "RI"}
        return f"{base}-{m.get(suf, suf.replace('.', '-'))}"
    return s


def history(ysym, start="2000-01-01", end=None):
    """Returns (DataFrame[date, open, high, low, close, adjclose, volume], splits list, meta) or (None, None, err)."""
    p1 = int(dt.datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    p2 = int((dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).timestamp()) if end is None else \
        int(dt.datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    try:
        j = get_json(U.format(ysym), params={"period1": p1, "period2": p2, "interval": "1d", "events": "div,splits"},
                     ok404=True, retries=3)
    except HttpError as e:
        return None, None, f"http {e.status}"
    if not j or not j.get("chart", {}).get("result"):
        return None, None, ((j or {}).get("chart", {}).get("error") or {}).get("description", "no result")
    r = j["chart"]["result"][0]
    ts = r.get("timestamp")
    if not ts:
        return None, None, "no timestamps"
    q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    df = pd.DataFrame({"date": pd.to_datetime(ts, unit="s").normalize(), "open": q.get("open"), "high": q.get("high"),
                       "low": q.get("low"), "close": q.get("close"), "adjclose": adj if adj else q.get("close"),
                       "volume": q.get("volume")})
    df = df.dropna(subset=["close"])
    sp = [(pd.to_datetime(v["date"], unit="s").normalize(), v["numerator"], v["denominator"])
          for v in (r.get("events", {}).get("splits") or {}).values()]
    m = r.get("meta", {})
    meta = {"exch": m.get("fullExchangeName"), "type": m.get("instrumentType"), "name": m.get("longName") or m.get("shortName"),
            "last": m.get("regularMarketPrice"), "last_ts": m.get("regularMarketTime"), "first_trade": m.get("firstTradeDate")}
    return df, sp, meta
