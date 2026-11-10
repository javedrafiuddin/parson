"""The human rubric AS CODE (Sections 5-6 scoring) + dilution trajectory (5.3).
The rubric is transparent arithmetic on filed numbers so it can be (a) applied to today's field and
(b) replayed on the historical cohort as the benchmark the model must beat (8.5). The model never sees it."""
import numpy as np
import pandas as pd


def rubric_score(df):
    """Expects columns: n_tests (0-3), dd (drawdown 0-1), rev_ttm, rev_growth, gross_margin, runway_years,
    cash_positive, debt_due_to_cash, share_growth_1y, reverse_split_12m, overhang (dilutive / shares). 0-100."""
    g = lambda c, d=np.nan: df[c] if c in df else pd.Series(d, index=df.index)
    n = g("n_tests", 0).fillna(0)
    damage = np.select([n >= 3, n == 2, n == 1], [22, 18, 10], 0) + np.where(g("dd").fillna(0) >= 0.80, 3, 0)
    rev = g("rev_ttm").fillna(0)
    biz = np.select([rev >= 100e6, rev >= 20e6, rev >= 5e6], [15, 12, 8], 0) \
        + np.where(g("rev_growth").fillna(0) > 0.20, 3, 0) + np.where(g("gross_margin").fillna(0) > 0.30, 2, 0)
    ry = g("runway_years")
    cp = g("cash_positive", False).fillna(False).astype(bool)
    surv = np.select([cp, ry >= 3, ry >= 2, ry >= 1.5, ry >= 1.0], [30, 28, 24, 16, 10], 0) \
        + np.where(g("debt_due_to_cash").fillna(0) < 0.25, 5, 0)
    sg = g("share_growth_1y").fillna(0.30)
    dil = np.select([sg < 0.10, sg < 0.30, sg < 0.75], [10, 6, 3], 0) \
        + np.where(g("reverse_split_12m", False).fillna(False).astype(bool), 0, 5) \
        + np.where(g("overhang").fillna(0.15) < 0.15, 5, 0)
    out = pd.DataFrame({"r_damage": damage, "r_business": biz, "r_survival": surv, "r_dilution": dil}, index=df.index)
    out["rubric"] = out.sum(axis=1)
    return out


def dilution_trajectory(shares0, price0, cash, debt_due_12m, burn_ttm, years=(1, 3, 5), paths=(1.0, 3.0, 10.0),
                        sbc_rate=0.03, raise_discount=0.10, buffer_years=1.0, overhang_shares=0.0, overhang_strike=None):
    """Section 5.3: projected share count at years 1/3/5 under the company's own burn, funded by equity once the
    cash buffer falls to `buffer_years`, at three price paths (flat, 3x, 10x reached geometrically by year 5).
    Issuance gets cheaper per dollar as price rises. Existing warrants/converts are added once in the money.
    Returns {path_multiple: {year: shares}} and the dilution factors."""
    burn = float(burn_ttm) if burn_ttm and burn_ttm > 0 else 0.0
    free_cash = max(float(cash or 0) - float(debt_due_12m or 0), 0.0)
    out = {}
    for m in paths:
        sh, cashbal, res = float(shares0), free_cash, {}
        for y in range(1, max(years) + 1):
            p_mid = price0 * (m ** ((y - 0.5) / 5.0))
            need = 0.0
            if burn > 0:
                cashbal -= burn
                target = burn * buffer_years
                if cashbal < target:
                    need = target - cashbal
                    cashbal = target
            sh += need / (p_mid * (1 - raise_discount)) if p_mid > 0 else 0.0
            sh *= (1 + sbc_rate)
            if overhang_shares and (overhang_strike is None or price0 * (m ** (y / 5.0)) >= overhang_strike):
                sh += overhang_shares
                overhang_shares = 0.0
            if y in years:
                res[y] = sh
        out[m] = res
    return out
