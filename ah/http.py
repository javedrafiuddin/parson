"""Rate-limited, retrying HTTP client. One token bucket per host. Polite by construction:
SEC fair-access is 10 req/s; we stay well under it. Never spoofs a browser."""
import threading, time, json, hashlib, gzip
from urllib.parse import urlparse
import requests
from .config import USER_AGENT, RAW

_RATE = {  # max requests / second per host
    "data.sec.gov": 8.0, "efts.sec.gov": 4.0, "www.sec.gov": 1.0,
    "query1.finance.yahoo.com": 4.0, "query2.finance.yahoo.com": 4.0,
    "api.nasdaq.com": 4.0, "www.nasdaqtrader.com": 1.0, "app.quotemedia.com": 2.0,
    "cdn.finra.org": 3.0, "clinicaltrials.gov": 3.0, "api.usaspending.gov": 2.0,
}
_locks, _next = {}, {}
_glock = threading.Lock()
_tls = threading.local()


def _throttle(host):
    rate = _RATE.get(host, 2.0)
    with _glock:
        lk = _locks.setdefault(host, threading.Lock())
    with lk:
        now = time.monotonic()
        t = max(now, _next.get(host, 0.0))
        _next[host] = t + 1.0 / rate
    d = t - time.monotonic()
    if d > 0:
        time.sleep(d)


def session():
    s = getattr(_tls, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
        _tls.s = s
    return s


class HttpError(Exception):
    def __init__(self, status, url):
        super().__init__(f"HTTP {status} {url}")
        self.status = status


def get(url, params=None, timeout=60, retries=4, ok404=False):
    """GET with throttle + backoff on 429/5xx. 403 is a policy answer: raised, never retried around."""
    host = urlparse(url).netloc
    last = None
    for i in range(retries + 1):
        _throttle(host)
        try:
            r = session().get(url, params=params, timeout=timeout)
        except requests.RequestException as e:
            last = e
            time.sleep(1.5 * (2 ** i))
            continue
        if r.status_code == 200:
            return r
        if r.status_code == 404 and ok404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            last = HttpError(r.status_code, url)
            time.sleep(2.0 * (2 ** i))
            continue
        raise HttpError(r.status_code, url)
    raise last if last else HttpError(0, url)


def get_json(url, params=None, **kw):
    r = get(url, params=params, **kw)
    return None if r is None else r.json()


def cached_json(url, params=None, ns="misc", ttl_hours=None, **kw):
    """Disk cache under data/raw/<ns>/ keyed by URL hash. ttl_hours=None -> cache forever."""
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
    d = RAW / ns
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{key}.json.gz"
    if f.exists() and (ttl_hours is None or (time.time() - f.stat().st_mtime) < ttl_hours * 3600):
        with gzip.open(f, "rt") as fh:
            return json.load(fh)
    j = get_json(url, params=params, **kw)
    with gzip.open(f, "wt") as fh:
        json.dump(j, fh)
    return j
