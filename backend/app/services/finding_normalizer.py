SEV_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
CONF_ORDER = {"high": 3, "medium": 2, "low": 1}

def validate_and_dedupe(findings: list[dict], files: dict[str, str]) -> list[dict]:
    """Validate line refs/paths against real source; dedupe overlaps; clamp enum values."""
    out, seen = [], set()
    for f in findings:
        if f.get("severity") not in SEV_ORDER: f["severity"] = "low"
        if f.get("confidence") not in CONF_ORDER: f["confidence"] = "low"
        if f.get("category") not in ("correctness","security","reliability","performance","maintainability","testing"):
            f["category"] = "maintainability"
        path = f.get("file_path") or (next(iter(files)) if files else "")
        f["file_path"] = path
        content = files.get(path, "")
        nlines = len(content.splitlines()) if content else 0
        line_ok = isinstance(f.get("start_line"), int) and 1 <= f["start_line"] <= max(nlines, 1)
        if not line_ok and f.get("source") == "llm":
            f["verification_status"] = "line-unverified"
            if not isinstance(f.get("start_line"), int): f["start_line"] = None
            elif nlines: f["start_line"] = None
        if line_ok and content and not f.get("evidence"):
            f["evidence"] = content.splitlines()[f["start_line"]-1].strip()[:500]
        if isinstance(f.get("start_line"), int) and isinstance(f.get("end_line"), int) and f["end_line"] < f["start_line"]:
            f["end_line"] = f["start_line"]
        key = (path, f.get("start_line"), (f.get("title","")[:60].lower()), f.get("rule_id",""))
        # cross-source dedupe: same file+line+similar title start
        sig = (path, f.get("start_line"))
        if key in seen: continue
        seen.add(key)
        f.setdefault("suggested_tests", []); f.setdefault("suggested_patch", "")
        f.setdefault("verification_status", "unverified" if f.get("source") == "llm" else "tool-confirmed")
        out.append(f)
    out.sort(key=lambda x: (-SEV_ORDER.get(x["severity"],0), -CONF_ORDER.get(x["confidence"],0), x.get("start_line") or 0))
    return out

def summarize(findings: list[dict], files: dict) -> dict:
    by_sev, by_cat, by_src = {}, {}, {}
    for f in findings:
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
        by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
        by_src[f["source"]] = by_src.get(f["source"], 0) + 1
    return {"total_findings": len(findings), "files_analyzed": len(files),
            "by_severity": by_sev, "by_category": by_cat, "by_source": by_src,
            "note": "Static findings are tool-confirmed; LLM findings are hypotheses requiring human verification."}
