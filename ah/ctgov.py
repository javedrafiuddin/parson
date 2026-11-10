"""ClinicalTrials.gov v2 API: registered Phase 2/3 programs by lead sponsor (the 'verifiable lead asset' test, Sec 5.2)."""
import re
from .http import get_json

API = "https://clinicaltrials.gov/api/v2/studies"
_DROP = r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|llc|holdings?|group|sa|nv|ag|the|/de/?|/nv/?|/ca/?|/md/?|/new/?)\b\.?"


def norm(name):
    n = re.sub(r"[/\\].*$", "", (name or "").lower())
    n = re.sub(r"[.,]", " ", n)
    n = re.sub(_DROP, " ", n)
    return re.sub(r"\s+", " ", n).strip()


def sponsor_trials(company_name, max_pages=3):
    """Returns list of dicts for interventional Phase 2 / Phase 3 trials whose LEAD sponsor matches the company."""
    key = norm(company_name)
    if len(key) < 3:
        return []
    out, tok = [], None
    for _ in range(max_pages):
        p = {"query.lead": key, "filter.advanced": "AREA[Phase](PHASE2 OR PHASE3) AND AREA[StudyType]INTERVENTIONAL",
             "fields": "NCTId,BriefTitle,Phase,OverallStatus,LeadSponsorName,PrimaryCompletionDate,StartDate,Condition,StudyFirstSubmitDate",
             "pageSize": 100}
        if tok:
            p["pageToken"] = tok
        try:
            j = get_json(API, params=p)
        except Exception:
            break
        for s in j.get("studies", []):
            ps = s.get("protocolSection", {})
            lead = ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")
            ln = norm(lead)
            if not (ln == key or ln.startswith(key + " ") or key.startswith(ln + " ") or ln.startswith(key)):
                continue
            st = ps.get("statusModule", {})
            out.append({"nct": ps.get("identificationModule", {}).get("nctId"),
                        "title": ps.get("identificationModule", {}).get("briefTitle"),
                        "phase": ",".join(ps.get("designModule", {}).get("phases", [])),
                        "status": st.get("overallStatus"), "lead": lead,
                        "primary_completion": (st.get("primaryCompletionDateStruct") or {}).get("date"),
                        "start": (st.get("startDateStruct") or {}).get("date"),
                        "first_submitted": st.get("studyFirstSubmitDate"),
                        "conditions": ";".join(ps.get("conditionsModule", {}).get("conditions", [])[:3])})
        tok = j.get("nextPageToken")
        if not tok:
            break
    return out


def summarize(trials):
    live = {"RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION", "NOT_YET_RECRUITING", "COMPLETED"}
    t = [x for x in trials if x["status"] in live]
    return {"n_p2p3": len(trials), "n_live_or_completed": len(t),
            "n_p3": sum("PHASE3" in x["phase"] for x in t),
            "n_active": sum(x["status"] in live - {"COMPLETED"} for x in t),
            "n_conditions": len({x["conditions"] for x in t}),
            "example_nct": t[0]["nct"] if t else None}
