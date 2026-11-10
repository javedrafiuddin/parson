"""Central configuration: paths, the single cost table (Sec 7.2), screen thresholds (Sec 5)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"          # raw API cache (gitignored, rebuildable)
PIT = DATA / "pit"          # large point-in-time parquet tables (gitignored, rebuildable)
PRICES = DATA / "prices"    # daily price parquet (gitignored, rebuildable)
DERIVED = DATA / "derived"  # compact derived tables (committed)
STATE = ROOT / "asymmetry-hunter-state"
for _p in (RAW, PIT, PRICES, DERIVED, STATE):
    _p.mkdir(parents=True, exist_ok=True)

# Declared, generic client name. No personal contact details are ever sent.
USER_AGENT = "asymmetry-hunter-research/1.0 (research client)"

RUN_ASOF = "2026-11-10"
STAKE_USD = 800

# ---- Section 7.2: THE SINGLE COST TABLE (screen, ML cost model and execution all read this) ----
COST = {
    "spread_cap_warrant_option": 0.15,   # eligibility: quoted spread <= 15% of mid
    "spread_cap_leaps": 0.10,
    "slippage_if_gt_5pct_adv": 0.05,
    "all_in_cost_void": 0.15,            # all-in cost > 15% of position voids the trade
    "cross_limit_of_mid": 0.10,          # a fill crossing > 10% of mid is cost-killed
    # assumed round-trip costs when historical spread data is missing (labelled ASSUMED)
    "assumed_rt_warrant": 0.20,
    "assumed_rt_otc_common": 0.10,
    "assumed_rt_listed_common": 0.02,
    "schwab_option_fee_per_contract": 0.65,
    "schwab_otc_fee": 6.95,
    "schwab_listed_equity_commission": 0.0,
}

# ---- Section 5 defaults ----
SCREEN = {
    "drawdown_min": 0.60,            # from split-adjusted 3-year high
    "ev_rev_max": 2.0,
    "mcap_small_max": 500e6,
    "rev_for_small_min": 20e6,
    "ttm_rev_min": 5e6,
    "runway_min_years": 1.0,
    "adv_min_common": 250_000,
    "adv_min_warrant_pref": 50_000,
    "float_pref_max_shares": 50e6,
    "atm_flag_pct_mcap": 0.25,
    "wave_window_default_years": 5,
    "wave_window_min_years": 2,
    "warrant_min_life_years": 3,
    "leaps_min_months": 18,
}

# ---- Section 8 cohort / label defaults (the sweep perturbs these) ----
COHORT = {
    "swan_peak_multiple": 25.0,
    "swan_terminal_net_multiple": 10.0,
    "forward_years": 5,
    "graveyard_drop": 0.95,
    "stub_value_frac": 0.10,
    "min_swan_positives_for_model": 30,
}
