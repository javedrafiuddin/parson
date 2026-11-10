"""Evidence packs for verification batches: per name, the screen's computed row + filing index + regex snippets cut
from the latest 10-Q and 10-K text (QuoteMedia mirror). A pack is a READING AID that points to filings by accession;
the verifying agent confirms from the snippet / filing, and marks anything it cannot confirm.
Usage: r3_packs.py <symbols.csv>   -> data/packs/<SYMBOL>.md"""
import sys, pathlib, re, importlib.util, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, numpy as np
from ah import store
from ah.config import DERIVED, DATA

spec = importlib.util.spec_from_file_location("filing", str(pathlib.Path(__file__).parent / "filing.py"))
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
PACK = DATA / "packs"
syms = pd.read_csv(sys.argv[1], keep_default_na=False, dtype=str).symbol.tolist()
st = pd.read_parquet(DERIVED / "stage1.parquet").drop_duplicates("symbol").set_index("symbol")
sc = pd.read_parquet(DERIVED / "baserate_scores.parquet").drop_duplicates("symbol").set_index("symbol")
th = pd.read_parquet(DERIVED / "themes.parquet").drop_duplicates("symbol").set_index("symbol")
c = store.connect()
FIL = c.execute("""SELECT cik, form, filed, accn, items FROM filings WHERE CAST(filed AS DATE) >= DATE '2025-11-01'
                   AND (form IN ('10-K','10-K/A','10-Q','10-Q/A','8-K','8-K/A','S-1','S-1/A','S-3','S-3/A','S-3ASR','DEF 14A','PRE 14A','NT 10-K','NT 10-Q','EFFECT','S-8','SC TO-T','SC 14D9','DEFM14A','PREM14A','25','15-12G','15-12B')
                        OR form LIKE '424B%')""").df()
FILG = {k: g.sort_values("filed", ascending=False) for k, g in FIL.groupby("cik")}

PAT_Q = [("cover shares outstanding", r"(shares of (the registrant'?s? )?(class [a-z] )?(common stock|ordinary shares)[^.]{0,90}outstanding|outstanding (as of|at) [A-Z][a-z]+ \d{1,2}, 20\d\d)", 2),
         ("going concern", r"(substantial doubt|going concern)", 3),
         ("potentially dilutive securities", r"(anti-?dilutive|potentially dilutive (securities|shares)|excluded from the (computation|calculation) of diluted)", 2),
         ("liquidity", r"(liquidity and capital resources|we (believe|expect) (that )?our (existing )?cash)", 2),
         ("ATM / equity distribution", r"(at[- ]the[- ]market|equity distribution agreement|sales agreement with)", 3),
         ("shelf", r"(shelf registration|registration statement on form s-3)", 1),
         ("convertible notes", r"(convertible (senior |promissory )?notes?|conversion (price|rate))", 3),
         ("variable-price / toxic terms", r"(variable conversion|% of the (lowest|volume[- ]weighted)|discount to the (vwap|market price)|equity line|standby equity purchase|committed equity)", 3),
         ("warrants", r"warrants? (to purchase|outstanding|exercisable)[^.]{0,160}", 3),
         ("subsequent events", r"subsequent events?", 2),
         ("listing deficiency / reverse split", r"(minimum bid price|listing (rule|standards?|requirement)|notice from (nasdaq|the nyse)|reverse stock split)", 3),
         ("debt maturities / covenants", r"(matur(es|ity) (on|in|date)|covenant (waiver|breach|default)|event of default|forbearance)", 2)]
PAT_K = [("business overview", r"item\s*1\.?\s*business", 1),
         ("customers / concentration", r"(customers? (accounted|represented) for|one customer|largest customers?)", 2),
         ("backlog / contracts", r"(backlog|remaining performance obligations?|contract(s)? (with|award(ed)?) (the )?(u\.s\.|department|doe|dod|nasa|air force|army|navy))", 3),
         ("going concern", r"(substantial doubt|going concern)", 2),
         ("options / RSUs outstanding", r"(options? outstanding|restricted stock units? outstanding|unvested (rsus|restricted))", 2),
         ("earnout / contingent shares", r"(earn[- ]?out shares?|contingent (consideration )?shares|sponsor shares? subject to)", 2),
         ("authorized shares", r"authorized[^.]{0,60}shares of common stock", 1),
         ("warrant terms", r"(warrants?[^.]{0,120}(expire|expiration|redeem|redemption)|\$18\.00|\$11\.50)", 3),
         ("preferred stock", r"(series [a-z0-9\-]+ (convertible )?preferred|liquidation preference)", 2),
         ("material weakness / restatement", r"(material weakness|restat(ed|ement))", 2),
         ("competition / position", r"(we (believe|are) (we are )?(the|a) (only|first|leading|largest)|market leader)", 2)]


def snips(text, pats, ctx=200):
    out = []
    for label, pat, mx in pats:
        k = 0
        for m in re.finditer(pat, text, flags=re.I):
            s, e = max(0, m.start() - ctx), min(len(text), m.end() + (900 if label == "business overview" else (520 if label == "potentially dilutive securities" else ctx)))
            if label == "business overview" and k == 0 and m.start() < 0.12 * len(text) and len(text) > 50000:
                continue_ = True   # skip the table-of-contents hit; take the next
                k_toc = getattr(snips, "_toc", 0)
            out.append(f"- **{label}** @{m.start()}: …{text[s:e].strip()}…")
            k += 1
            if k >= mx:
                break
    return out


def fnum(v, money=True):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "n/a" if not (isinstance(v, float) and np.isinf(v)) else "cash-positive"
    return f"${v/1e6:,.1f}M" if money else f"{v:,.0f}"


def one(sym):
    f = PACK / f"{sym.replace('/', '_')}.md"
    if f.exists() and f.stat().st_size > 1500:
        return sym, "cached"
    if sym not in st.index:
        return sym, "not in stage1"
    r = st.loc[sym]
    L = [f"# {sym} — {r['name']}", "",
         f"CIK {int(r.cik)} · {r.exchange} · SIC {r.get('sic')} {r.get('sic_desc')} · Stage 1 (code): **{r.stage1}**",
         f"Price: close ${r.last_close:.4f} on {str(r.last_date)[:10]} (Yahoo, delayed) · 3y high ${r.high_3y:.2f} on {str(r.high_3y_date)[:10]} · drawdown {r.drawdown_3y:.1%} · 20d ADV ${r.adv20/1e6:.2f}M",
         f"Market cap {fnum(r.mcap)} (screener {fnum(r.mcap_screener)}; price x filed shares {fnum(r.mcap_calc)}; mismatch flag {bool(r.mcap_mismatch)})", "",
         "## Screen row computed from XBRL (as first filed) — CONFIRM against the filing",
         f"- Balance sheet period {str(r.bs_end)[:10]}, filed {str(r.bs_known)[:10]}, accession {r.bs_accn}",
         f"- Cash + ST investments {fnum(r.cash_total)} · total debt {fnum(r.debt_total)} · debt due <12m {fnum(r.debt_due_12m)} · preferred/temp equity {fnum(r.pref_liq)}",
         f"- Revenue TTM {fnum(r.rev_ttm)} (through {str(r.rev_ttm_e)[:10]}) · operating cash flow TTM {fnum(r.ocf_ttm)} · last 2 quarters {fnum(r.ocf_last2q)}",
         f"- Runway (5.1 formula) {('cash-positive' if r.cash_positive else (f'{r.runway_years:.2f} years' if pd.notna(r.runway_years) else 'n/a'))} · on last-2-quarter burn {(f'{r.runway_years_2q:.2f} years' if pd.notna(r.runway_years_2q) else 'n/a')}",
         f"- Shares {fnum(r.shares, False)} ({r.shares_src}, as of {str(r.shares_e)[:10]}) · EV/revenue {r.ev_rev if pd.notna(r.ev_rev) else 'n/a'} · damage tests passed {int(r.n_damage_tests)}",
         f"- Filing-index flags: non-reliance 8-K {r.nonreliance_12m}; auditor change 8-K {r.auditor_change_12m}; NT filing {r.nt_12m}; delisting-notice 8-K (3.01) {r.delist_notice_12m}; latest 424B5 {r.last_424b5}; 424B count 12m {r.n_424b_12m}; unregistered sale 8-K (3.02) {r.unreg_sale_12m}; S-3 (36m) {r.shelf_36m}; lineage flag: {r.bk_or_despac or 'none'}",
         f"- Clinical trials (lead sponsor match): live/completed P2-P3 {r.ct_live}, active {r.ct_active}, P3 {r.ct_p3}, e.g. {r.ct_example}"]
    if sym in sc.index:
        s = sc.loc[sym]
        L.append(f"- Cohort strata: {s.dd_b}, {s.mc_b}, {s.sec_b}, {s.run_b} → base-rate P(swan 5y) {s.p_swan_table:.2%} (sweep {s.p_swan_min:.2%}–{s.p_swan_max:.2%}); model P(zero 5y) {s.p_zero:.1%}")
    if sym in th.index:
        t = th.loc[sym]
        L += ["", f"## Vendor description (LEAD ONLY, not evidence) — emergent cluster {int(t.topic)}: {t.topic_terms}; fallen-leader flag {bool(t.fallen_leader)}", str(t.description)[:900]]
    g = FILG.get(int(r.cik))
    if g is not None:
        L += ["", "## EDGAR filing index, last 12 months (form · filed · accession · 8-K items)"]
        L += [f"- {x.form} · {x.filed} · {x.accn} · {x.items}" for x in g.head(45).itertuples()]
    for form, pats in (("10-Q", PAT_Q), ("10-K", PAT_K)):
        try:
            ff, row, cik = F.get_text(sym, form)
            t = ff.read_text()
            L += ["", f"## Snippets — {row.form} filed {row.filed}, accession {row.accession} ({len(t):,} chars; full text: `{ff}`)"]
            L += snips(t, pats) or ["- (no pattern hits)"]
        except BaseException as e:
            L += ["", f"## {form}: NOT RETRIEVED ({str(e)[:80]})"]
    f.write_text("\n".join(L))
    return sym, "ok"


t0 = time.time()
with ThreadPoolExecutor(5) as ex:
    res = list(ex.map(one, syms))
print(pd.Series([r[1] for r in res]).value_counts().to_dict(), round(time.time() - t0), "s")
