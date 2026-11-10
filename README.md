# parson — Operation Asymmetry Hunter v3 (White Swan edition)

Research system: universe screen → expected-value math → ML ranking → one buy set for Mon Nov 16, 2026.

- `asymmetry-hunter-state/STATE.md` — master state; start here. `PROMPT_v3.md` is the governing prompt.
- `ah/` — Python package (data clients, features, labels, cohort, model). `scripts/` — stage runners. `tests/` — leakage tests.
- `data/derived/` — compact derived tables (committed). `data/raw|pit|prices/` — rebuildable caches (gitignored).

Rebuild the data layer: `python3 scripts/r1_secmaster_frames.py && python3 scripts/r1_pull_facts.py && python3 scripts/r2_pull_prices.py data/tmp/syms_listed.csv listed`

This is research tooling for one person's $800 test. Nothing here places orders or touches any account.
