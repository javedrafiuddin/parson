#!/usr/bin/env python3
"""Tight evidence brief for a few symbols from cached filing text: each item <= W chars, with form/date/accession."""
import sys, re, pathlib, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
spec = importlib.util.spec_from_file_location("filing", str(pathlib.Path(__file__).parent / "filing.py"))
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
W = 330
ITEMS_Q = [("shares", r"[\d,]{9,}\s+shares of[^.]{0,80}outstanding|outstanding[^.]{0,60}[\d,]{9,}\s+shares", 1),
           ("going-concern", r"substantial doubt[^.]{0,200}", 1), ("liquidity", r"(we believe|management believes)[^.]{0,60}(cash|liquidity)[^.]{0,220}", 1),
           ("backlog", r"backlog[^.]{0,230}", 1), ("dilutive", r"(anti-?dilutive)[^.]{0,120}\.[^.]{0,260}", 1),
           ("debt", r"(term loan|senior (secured )?notes|convertible (senior )?notes|credit facility)[^.]{0,160}(due|matur)[^.]{0,90}", 2),
           ("ATM", r"(at[- ]the[- ]market|equity distribution)[^.]{0,230}", 1)]
ITEMS_K = [("business", r"(?<=\. )(we are|the company is|[A-Z][A-Za-z&\.\- ]{2,40} is) (a|an|the) [^.]{40,330}\.", 2),
           ("customers", r"(one|two|three|our (largest|top))[^.]{0,40}customers?[^.]{0,220}", 1), ("position", r"(market leader|leading (global )?(provider|supplier|manufacturer)|largest)[^.]{0,220}", 1)]
for s in sys.argv[1:]:
    print(f"=== {s}")
    for form, items in (("10-Q", ITEMS_Q), ("10-K", ITEMS_K)):
        try:
            f, row, cik = F.get_text(s, form)
            t = f.read_text()
        except BaseException as e:
            print(f" [{form}] not retrieved: {str(e)[:60]}"); continue
        print(f" [{row.form} filed {row.filed} acc {row.accession}]")
        body = t[int(0.04 * len(t)):] if form == "10-K" else t
        for lab, pat, mx in items:
            k = 0
            for m in re.finditer(pat, body if lab != "shares" else t, flags=re.I):
                print(f"  {lab}: {m.group(0)[:W]}")
                k += 1
                if k >= mx:
                    break
