"""Nasdaq Trader symbol directory + api.nasdaq.com (screener, quotes with bid/ask, history, option chains,
short interest, and the SEC-filing mirror that serves filing TEXT via app.quotemedia.com)."""
import io, re
import pandas as pd
from .http import get, get_json

API = "https://api.nasdaq.com/api"


def symbol_files():
    """Returns one frame: every non-test security on Nasdaq + NYSE/NYSE American/Arca/Cboe/IEX."""
    a = pd.read_csv(io.StringIO(get("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt").text), sep="|", keep_default_na=False, dtype=str)
    b = pd.read_csv(io.StringIO(get("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt").text), sep="|", keep_default_na=False, dtype=str)
    stamp_a, stamp_b = str(a.iloc[-1, 0]), str(b.iloc[-1, 0])
    a, b = a.iloc[:-1], b.iloc[:-1]
    a = pd.DataFrame({"symbol": a["Symbol"], "name": a["Security Name"], "exchange": "NASDAQ",
                      "etf": a["ETF"], "test": a["Test Issue"], "fin_status": a["Financial Status"],
                      "cqs": a["Symbol"], "src": "nasdaqtrader:nasdaqlisted.txt"})
    exmap = {"N": "NYSE", "A": "NYSE American", "P": "NYSE Arca", "Z": "Cboe BZX", "V": "IEX"}
    b = pd.DataFrame({"symbol": b["ACT Symbol"], "name": b["Security Name"], "exchange": b["Exchange"].map(exmap),
                      "etf": b["ETF"], "test": b["Test Issue"], "fin_status": "",
                      "cqs": b["CQS Symbol"], "src": "nasdaqtrader:otherlisted.txt"})
    df = pd.concat([a, b], ignore_index=True)
    df = df[df.test != "Y"].drop(columns="test")
    df.attrs["file_stamps"] = (stamp_a, stamp_b)
    return df


def classify(name, symbol=""):
    """Security type from the exchange's own security description (list-building mechanics, not a filter)."""
    n = (name or "").lower().strip()
    if re.search(r"[-–] ?units?$", n) or n.endswith(" units") or n.endswith(" unit"):
        return "unit"
    if re.search(r"\bunits?\b", n) and ("warrant" in n or "right" in n or "one " in n or "consisting" in n):
        return "unit"
    if "warrant" in n:
        return "warrant"
    if re.search(r"\brights?\b", n) and "ordinary" not in n.split("right")[0][-25:]:
        if re.search(r"\b(right|rights)\b(?!s? reserved)", n) and not re.search(r"common stock|ordinary shares?$", n):
            return "right"
    if re.search(r"\betn\b|exchange[- ]traded note|\betf\b|\bfund\b|portfolio|index-linked", n):
        return "fund_or_etn"
    if re.search(r"preferred|preference|depositary shares? (each )?representing .*(interest|1/)|% series|cumulative", n):
        return "convertible_or_preferred" if True else ""
    if re.search(r"\bnotes?\b|debentures?|\bbonds?\b|subordinated", n):
        return "note"
    if re.search(r"american depositary|\bads\b|\badr\b|depositary share", n):
        return "adr"
    if re.search(r"common stock|common shares?|ordinary shares?|class [a-c]\b|common units|capital stock|shares of beneficial|subordinate voting|limited partner|lp units|\bstock\b|\bshares\b", n):
        return "common"
    if re.search(r"\betns?\b|strats|tr ctf|\bpfd\b|trust for|pplus|certificates", n):
        return "note"
    return "common"   # bare company names in the directory are common stock


def screener():
    j = get_json(f"{API}/screener/stocks", params={"tableonly": "true", "limit": 25, "offset": 0, "download": "true"})
    df = pd.DataFrame(j["data"]["rows"])
    df["lastsale"] = pd.to_numeric(df["lastsale"].str.replace("$", "").str.replace(",", ""), errors="coerce")
    for c in ("volume", "marketCap"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _num(x):
    try:
        return float(str(x).replace("$", "").replace(",", ""))
    except Exception:
        return None


def quote(symbol, assetclass="stocks"):
    """Live/last quote with BID and ASK and their timestamp (used for spreads and lock prices)."""
    j = get_json(f"{API}/quote/{symbol}/info", params={"assetclass": assetclass})
    d = (j or {}).get("data") or {}
    out = {"symbol": symbol, "name": d.get("companyName"), "exchange": d.get("exchange")}
    for k in ("primaryData", "secondaryData"):
        p = d.get(k) or {}
        out[k] = {"last": _num(p.get("lastSalePrice")), "bid": _num(p.get("bidPrice")), "ask": _num(p.get("askPrice")),
                  "ts": p.get("lastTradeTimestamp"), "volume": _num(p.get("volume")), "realtime": p.get("isRealTime")}
    return out


def historical(symbol, start="2016-11-10", end="2026-11-10"):
    j = get_json(f"{API}/quote/{symbol}/historical",
                 params={"assetclass": "stocks", "fromdate": start, "todate": end, "limit": 9999})
    rows = (((j or {}).get("data") or {}).get("tradesTable") or {}).get("rows") or []
    df = pd.DataFrame(rows)
    if len(df):
        df["date"] = pd.to_datetime(df["date"])
        for c in ("close", "open", "high", "low", "volume"):
            df[c] = df[c].map(_num)
    return df


def option_chain(symbol, fromdate, todate, callput="call"):
    j = get_json(f"{API}/quote/{symbol}/option-chain",
                 params={"assetclass": "stocks", "limit": 2000, "fromdate": fromdate, "todate": todate,
                         "excode": "oprac", "callput": callput, "money": "all", "type": "all"})
    return (((j or {}).get("data") or {}).get("table") or {}).get("rows") or []


def short_interest(symbol):
    j = get_json(f"{API}/quote/{symbol}/short-interest", params={"assetClass": "stocks"})
    return ((((j or {}).get("data") or {}).get("shortInterestTable") or {}).get("rows")) or []


def sec_filings(symbol, limit=100, group=None):
    p = {"limit": limit, "sortColumn": "filed", "sortOrder": "desc", "IsQuoteMedia": "true"}
    if group:
        p["formGroup"] = group
    j = get_json(f"{API}/company/{symbol}/sec-filings", params=p)
    return (((j or {}).get("data") or {}).get("rows")) or []


def filing_text(html_link, maxlen=None):
    """Fetch a filing's full text (primary doc + exhibits) from the QuoteMedia mirror linked by Nasdaq."""
    h = get(html_link, timeout=120).text
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&#160;|&nbsp;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"\s+", " ", t)
    return t[:maxlen] if maxlen else t
