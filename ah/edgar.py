"""SEC EDGAR access via data.sec.gov (submissions, XBRL companyfacts, frames) and efts full-text search.
Note: www.sec.gov (Archives) refuses this environment; filing TEXT is read via ah.nasdaq.filing_text()."""
from .http import get_json, cached_json, HttpError

D = "https://data.sec.gov"
FTS = "https://efts.sec.gov/LATEST/search-index"


def cik10(cik):
    return f"{int(cik):010d}"


def submissions(cik, cache=True):
    url = f"{D}/submissions/CIK{cik10(cik)}.json"
    return cached_json(url, ns="submissions") if cache else get_json(url)


def companyfacts(cik):
    try:
        return get_json(f"{D}/api/xbrl/companyfacts/CIK{cik10(cik)}.json", ok404=True)
    except HttpError as e:
        if e.status == 404:
            return None
        raise


def frame(taxonomy, tag, unit, period, cache_ttl=None):
    """period e.g. 'CY2019Q2I' (instant) or 'CY2019Q2' / 'CY2019' (duration)."""
    url = f"{D}/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json"
    try:
        return cached_json(url, ns="frames", ttl_hours=cache_ttl, ok404=True)
    except HttpError as e:
        if e.status == 404:
            return None
        raise


def fts(q, forms=None, start=None, end=None, ciks=None, frm=0):
    """EDGAR full-text search (2001+). Returns hit metadata (accession, exhibit type/description, items)."""
    p = {"q": q, "from": frm}
    if forms:
        p["forms"] = forms
    if start and end:
        p.update({"dateRange": "custom", "startdt": start, "enddt": end})
    if ciks:
        p["ciks"] = ciks
    return get_json(FTS, params=p)


def typeahead(keys):
    j = get_json(FTS, params={"keysTyped": keys})
    return [(h["_id"], h["_source"].get("entity"), h["_source"].get("tickers")) for h in j["hits"]["hits"]]
