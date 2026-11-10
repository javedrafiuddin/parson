"""R1 step 2: for every CIK in the survivorship-free master, pull
  (a) data.sec.gov submissions  -> entity master row + filing index rows (form, filed, ACCEPTED timestamp, items)
  (b) data.sec.gov companyfacts -> every reported value of the tags in ah.tags, WITH its accession + filed date
      (as-originally-filed versions preserved: one row per (tag,start,end,val) at its FIRST filing date).
Resumable: batches of 200 CIKs -> data/pit/{facts,filings,entities}/part-XXXXX.parquet ; done-list in data/pit/_done.txt"""
import sys, pathlib, time, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from ah import edgar, tags
from ah.http import get_json, HttpError
from ah.config import DERIVED, PIT

WANT = {tax: set(v) for tax, v in tags.ALL.items()}
for sub in ("facts", "filings", "entities"):
    (PIT / sub).mkdir(parents=True, exist_ok=True)
DONE = PIT / "_done.txt"


def one(cik):
    ent, fil, fac = None, [], []
    try:
        s = get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", ok404=True)
    except HttpError as e:
        s = None
    if s:
        ent = dict(cik=cik, name=s.get("name"), entity_type=s.get("entityType"), sic=s.get("sic"),
                   sic_desc=s.get("sicDescription"), category=s.get("category"),
                   tickers=",".join(s.get("tickers") or []), exchanges=",".join([x or "" for x in (s.get("exchanges") or [])]),
                   state_inc=s.get("stateOfIncorporation"), fye=s.get("fiscalYearEnd"),
                   former_names=json.dumps([(f.get("name"), (f.get("to") or "")[:10]) for f in s.get("formerNames", [])]),
                   n_older_pages=len(s["filings"].get("files", [])))
        r = s["filings"]["recent"]
        n = len(r.get("form", []))
        for i in range(n):
            fil.append((cik, r["accessionNumber"][i], r["form"][i], r["filingDate"][i], r["acceptanceDateTime"][i],
                        r["reportDate"][i], r["items"][i], r["primaryDocument"][i], r.get("primaryDocDescription", [""] * n)[i]))
    try:
        cf = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", ok404=True)
    except HttpError as e:
        cf = None
    if cf:
        for tax, want in WANT.items():
            for tag, body in (cf.get("facts", {}).get(tax, {}) or {}).items():
                if tag not in want:
                    continue
                for unit, rows in body.get("units", {}).items():
                    seen = {}
                    for x in sorted(rows, key=lambda z: z.get("filed", "")):
                        k = (x.get("start"), x.get("end"), x.get("val"))
                        if k in seen:
                            continue  # same value re-reported as a comparative: keep first filing only
                        seen[k] = 1
                        fac.append((cik, tax, tag, unit, x.get("start"), x.get("end"), x.get("val"), x.get("accn"),
                                    x.get("fy"), x.get("fp"), x.get("form"), x.get("filed"), x.get("frame")))
    return ent, fil, fac, (s is not None), (cf is not None)


def main():
    ciks = sorted(pd.read_parquet(DERIVED / "frames_cover.parquet", columns=["cik"]).cik.unique().tolist())
    done = set(int(x) for x in DONE.read_text().split()) if DONE.exists() else set()
    todo = [c for c in ciks if c not in done]
    print(f"master {len(ciks)} done {len(done)} todo {len(todo)}", flush=True)
    B = 200
    t0 = time.time()
    for b in range(0, len(todo), B):
        chunk = todo[b:b + B]
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(one, chunk))
        ents = [r[0] for r in res if r[0]]
        fil = [x for r in res for x in r[1]]
        fac = [x for r in res for x in r[2]]
        tagid = f"{chunk[0]:010d}"
        if ents:
            pd.DataFrame(ents).to_parquet(PIT / "entities" / f"part-{tagid}.parquet", index=False)
        if fil:
            pd.DataFrame(fil, columns=["cik", "accn", "form", "filed", "accepted", "report_date", "items", "primary_doc", "primary_desc"]
                         ).to_parquet(PIT / "filings" / f"part-{tagid}.parquet", compression="zstd", index=False)
        if fac:
            df = pd.DataFrame(fac, columns=["cik", "taxonomy", "tag", "unit", "start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"])
            df["val"] = pd.to_numeric(df["val"], errors="coerce")
            df.to_parquet(PIT / "facts" / f"part-{tagid}.parquet", compression="zstd", index=False)
        with open(DONE, "a") as fh:
            fh.write("\n".join(str(c) for c in chunk) + "\n")
        el = time.time() - t0
        print(f"{b + len(chunk)}/{len(todo)} ciks  {el:.0f}s  eta {el / (b + len(chunk)) * (len(todo) - b - len(chunk)) / 60:.1f} min  "
              f"facts {len(fac)} filings {len(fil)} nosub {sum(1 for r in res if not r[3])} nofacts {sum(1 for r in res if not r[4])}", flush=True)


if __name__ == "__main__":
    main()
