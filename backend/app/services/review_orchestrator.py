import asyncio
from app.core.config import get_settings
from app.services.ast_analyzer import analyze_python_ast
from app.services.static_analyzer import run_static_tools
from app.services.llm_review import review_with_llm
from app.services.finding_normalizer import validate_and_dedupe, summarize

SUPPORTED_EXT = {".py": "python"}

def detect_language(path: str, declared: str) -> tuple[str, bool]:
    for ext, lang in SUPPORTED_EXT.items():
        if path.lower().endswith(ext): return lang, True
    return declared or "unknown", False

async def run_review(files_in: list[dict], include_llm: bool = True, diff_text: str = "") -> dict:
    """files_in: [{path, content}]. Returns {findings, files, summary, warnings, status, llm_summary}"""
    s = get_settings()
    warnings, all_findings, files_map = [], [], {}
    if len(files_in) > s.max_files: raise ValueError(f"Too many files (max {s.max_files})")
    total = 0
    for f in files_in:
        content = f["content"]
        if len(content.encode()) > s.max_file_bytes: raise ValueError(f"File {f['path']} exceeds {s.max_file_bytes} bytes")
        if "\x00" in content: raise ValueError(f"File {f['path']} looks binary and was rejected")
        total += len(content.encode())
        lang, supported = detect_language(f["path"], "python")
        if not supported:
            warnings.append(f"{f['path']}: unsupported language — only Python analysis is available; file stored but not analyzed.")
            files_map[f["path"]] = content; continue
        files_map[f["path"]] = content
        ast_findings, syntax_err = analyze_python_ast(content, f["path"])
        for x in ast_findings: x["file_path"] = f["path"]
        all_findings += ast_findings
        if not syntax_err:
            static_findings, w = await asyncio.to_thread(run_static_tools, content, f["path"])
            for x in static_findings: x["file_path"] = f["path"]
            all_findings += static_findings; warnings += [f"{f['path']}: {x}" for x in w]
        else:
            warnings.append(f"{f['path']}: syntax error — Ruff/Bandit skipped for this file.")
    if total > s.max_source_bytes: raise ValueError(f"Total source exceeds {s.max_source_bytes} bytes")
    llm_summary = ""
    status = "completed"
    if include_llm:
        llm_out, llm_warn = await review_with_llm([{"path": p, "content": c} for p, c in files_map.items()], diff_text)
        if llm_warn: warnings.append(llm_warn); status = "partial"
        if llm_out:
            llm_summary = llm_out.get("summary", "")
            for x in llm_out.get("findings", []):
                x["source"] = "llm"; x["rule_id"] = "LLM"
                x["verification_status"] = "unverified"
                all_findings.append(x)
    findings = validate_and_dedupe(all_findings, files_map)
    summary = summarize(findings, files_map)
    if llm_summary: summary["llm_summary"] = llm_summary
    return {"findings": findings, "files": files_map, "summary": summary, "warnings": warnings, "status": status}
