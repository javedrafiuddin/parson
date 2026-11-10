"""Section 8.3 labels from the PRICES table (S1_PRICED subset): forward excursions and terminal multiples.
Labels read prices and nothing else. Entry = next session after the base date, at an assumed ask
(close * (1 + half round-trip cost)); exit at an assumed bid. Cost class per ah.config.COST (labelled ASSUMED)."""
import numpy as np
import pandas as pd

SESS = {1: 252, 3: 756, 4: 1008, 5: 1260, 6: 1512}


def _fwd_max(a, n):
    """max of a[i+1 : i+1+n] for each i (NaN if no forward data)."""
    s = pd.Series(a[::-1])
    r = s.rolling(n, min_periods=1).max().to_numpy()[::-1]     # r[i] = max(a[i : i+n])
    out = np.full(len(a), np.nan)
    out[:-1] = r[1:]
    return out


def _fwd_min(a, n):
    s = pd.Series(a[::-1])
    r = s.rolling(n, min_periods=1).min().to_numpy()[::-1]
    out = np.full(len(a), np.nan)
    out[:-1] = r[1:]
    return out


def path_labels(px, base_dates, rt_cost=0.02, horizons=(1, 3, 5), extra=(4, 6)):
    """px: one ticker's frame sorted by date with columns date, close, adjclose, volume.
    Returns one row per base date at which the ticker had a quote within 7 days at/before the base date."""
    d = px["date"].to_numpy()
    cl = px["close"].to_numpy(float)
    adj = px["adjclose"].to_numpy(float)
    vol = px["volume"].to_numpy(float)
    n = len(d)
    if n < 2:
        return None
    half = rt_cost / 2.0
    rows = []
    idx = np.searchsorted(d, np.array(base_dates, dtype="datetime64[ns]"), side="right") - 1   # last session <= base date
    fm = {h: _fwd_max(cl, SESS[h]) for h in set(horizons) | set(extra)}
    fmin5 = _fwd_min(cl, SESS[5])
    for bd, i in zip(base_dates, idx):
        if i < 0 or i + 1 >= n:
            continue
        if (np.datetime64(bd) - d[i]) > np.timedelta64(7, "D"):
            continue                       # no quote near the base date -> not tradable there
        j = i + 1                          # entry session = next session after the base date
        if (d[j] - np.datetime64(bd)) > np.timedelta64(10, "D"):
            continue                       # next quote is far away -> untradable at the base (logged upstream)
        entry = cl[j] * (1 + half)
        if not np.isfinite(entry) or entry <= 0:
            continue
        r = {"base_date": bd, "entry_date": d[j], "entry_close": cl[j], "entry_ask": entry, "entry_vol": vol[j]}
        last_i = n - 1
        for h in set(horizons) | set(extra):
            k = j + SESS[h]
            r[f"mfe_{h}y"] = fm[h][j] / entry if np.isfinite(fm[h][j]) else np.nan
            if k <= last_i:
                # terminal: exit at assumed bid; total-return path via adjclose ratio applied to entry close
                r[f"term_{h}y"] = (adj[k] / adj[j]) * (1 - half) / (1 + half)
                r[f"resolved_{h}y"] = True
            else:
                r[f"term_{h}y"] = np.nan
                r[f"resolved_{h}y"] = False
        r["min_5y"] = fmin5[j] / entry if np.isfinite(fmin5[j]) else np.nan
        r["last_date"] = d[last_i]
        r["last_over_entry"] = (adj[last_i] / adj[j]) * (1 - half) / (1 + half)
        rows.append(r)
    return pd.DataFrame(rows) if rows else None


def classify(df, swan_peak=25.0, swan_term=10.0, H=5, grave_drop=0.95):
    """SWAN / GRAVEYARD / MUDDLE / UNRESOLVED for the priced subset.
    A window that has not matured (resolved_H False) is UNRESOLVED unless the swan peak was ALREADY reached
    (a peak that has happened cannot un-happen) - shortened windows never become zeros or muddles silently."""
    mfe, term, res = df[f"mfe_{H}y"], df[f"term_{H}y"], df[f"resolved_{H}y"]
    swan = (mfe >= swan_peak) | (term >= swan_term)
    grave = res & (term <= (1 - grave_drop))
    out = np.where(swan, "SWAN", np.where(~res, "UNRESOLVED", np.where(grave, "GRAVEYARD", "MUDDLE")))
    return pd.Series(out, index=df.index)
