"""Section 6 arithmetic: Fermi decomposition (two numbers, never one), scenario EV at 5y, caps, breakeven,
required price / market cap paths, Kelly diagnostic, effective-N portfolio math. Pure functions; every
intermediate is returned so reports can show the arithmetic."""
import math

CALIBRATION = {"survival": 0.50, "wave": 0.125, "leads": 0.225, "captures": 0.15}   # Section 6.1 placeholders


def p4(f):
    return f["survival"] * f["wave"] * f["leads"] * f["captures"]


def fermi(filtered, base=None, lows=None, highs=None):
    base = base or CALIBRATION
    pb, pf = p4(base), p4(filtered)
    lifts = {k: filtered[k] / base[k] for k in base}
    r = {"p4_base": pb, "p4_filtered": pf, "lift": pf / pb, "factor_lifts": lifts,
         "one_in_base": 1 / pb, "one_in_filtered": 1 / pf}
    if lows and highs:
        r["p4_low"], r["p4_high"] = p4(lows), p4(highs)
    return r


def ev(probs, payoffs, cost=0.0, caps=(50.0, 25.0)):
    """probs/payoffs: dicts over Zero/Muddle/Re-rate/White Swan (payoffs = NET multiples at 5y).
    EV per $1 = sum(p * M) - 1 - cost."""
    s = sum(probs.values())
    if abs(s - 1.0) > 1e-9:
        raise ValueError(f"probabilities sum to {s}, not 1.00")
    base = sum(probs[k] * payoffs[k] for k in probs) - 1 - cost
    out = {"prob_sum": s, "ev_per_dollar": base, "terms": {k: probs[k] * payoffs[k] for k in probs}}
    for c in caps:
        pp = dict(payoffs)
        pp["White Swan"] = min(pp["White Swan"], c)
        out[f"ev_cap_{int(c)}x"] = sum(probs[k] * pp[k] for k in probs) - 1 - cost
    m = payoffs["White Swan"]
    out["breakeven_p_swan_alone"] = 1 / m if m > 0 else float("inf")
    rest = sum(probs[k] * payoffs[k] for k in probs if k != "White Swan")
    out["breakeven_p_swan_given_other_rows"] = max(0.0, (1 + cost - rest) / m) if m > 0 else float("inf")
    return out


def kelly(p_win, net_multiple):
    """Full Kelly for a binary win (net_multiple x stake) / total loss. b = M - 1."""
    b = net_multiple - 1
    return (p_win * b - (1 - p_win)) / b if b > 0 else -1.0


def required_paths(price, fd_shares_by_year, multiples=(25, 50, 190), year=5):
    """Required price and market cap for each multiple on the share count PROJECTED to the landing year."""
    sh = fd_shares_by_year[year]
    return {m: {"price": price * m, "market_cap": price * m * sh, "fd_shares": sh} for m in multiples}


def effective_n(weights_by_cluster):
    """Names riding one wave are fractional bets. N_eff = (sum w)^2 / sum(w^2) computed over CLUSTER weights."""
    w = list(weights_by_cluster.values())
    s = sum(w)
    return (s * s) / sum(x * x for x in w) if s > 0 else 0.0


def portfolio(p, n_eff):
    return {"p_at_least_one": 1 - (1 - p) ** n_eff, "expected_hits": n_eff * p, "expected_zeros": n_eff * (1 - p)}
