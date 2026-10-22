"""Ruff + Bandit via safe subprocess (no shell, isolated temp dir, timeouts)."""
import json, subprocess, tempfile, os, sys, shutil

RUFF_SEV = {"E9": "high", "F": "medium", "B": "medium", "S": "high", "E": "low", "W": "low", "C4": "low", "SIM": "low", "UP": "low", "N": "low"}
BANDIT_SEV = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
BANDIT_CONF = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}

def _run(cmd, cwd, timeout=30):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)  # never shell=True
        return p.stdout[:500_000], p.stderr[:10_000], p.returncode
    except FileNotFoundError:
        return None, "tool not installed", 127
    except subprocess.TimeoutExpired:
        return None, "tool timed out", 124

def run_static_tools(source: str, filename: str = "submitted.py") -> tuple[list[dict], list[str]]:
    findings, warnings = [], []
    safe_name = os.path.basename(filename) or "submitted.py"
    if not safe_name.endswith(".py"): safe_name += ".py"
    with tempfile.TemporaryDirectory(prefix="bugforge-") as td:
        path = os.path.join(td, safe_name)
        with open(path, "w", encoding="utf-8") as fh: fh.write(source)
        # Ruff
        ruff = shutil.which("ruff") or os.path.join(os.path.dirname(sys.executable), "ruff")
        out, err, code = _run([ruff, "check", "--output-format=json", "--select", "E,F,B,S,SIM,C4,UP", path], td)
        if out is None: warnings.append(f"Ruff unavailable: {err}")
        elif code in (0, 1):
            try:
                for item in json.loads(out or "[]"):
                    rc = (item.get("code") or "E")
                    prefix = next((k for k in ("E9","SIM","C4","UP","F","B","S","E","W") if rc.startswith(k)), "E")
                    loc = item.get("location") or {}
                    findings.append(dict(title=f"{rc}: {item.get('message','')}"[:300],
                        description=item.get("message",""), category="security" if prefix=="S" else "maintainability",
                        severity=RUFF_SEV.get(prefix, "low"), confidence="high",
                        start_line=loc.get("row"), end_line=(item.get("end_location") or {}).get("row") or loc.get("row"),
                        evidence="", explanation=item.get("message",""),
                        remediation=(item.get("fix") or {}).get("message") or "See the Ruff rule documentation for a recommended fix.",
                        suggested_patch="", suggested_tests=[], source="ruff",
                        verification_status="tool-confirmed", rule_id=rc))
            except json.JSONDecodeError: warnings.append("Ruff output could not be parsed.")
        # Bandit
        bandit = shutil.which("bandit") or os.path.join(os.path.dirname(sys.executable), "bandit")
        out, err, code = _run([bandit, "-f", "json", "-q", path], td)
        if out is None: warnings.append(f"Bandit unavailable: {err}")
        elif code in (0, 1):
            try:
                for r in (json.loads(out or "{}").get("results") or []):
                    findings.append(dict(title=f"{r.get('test_id')}: {r.get('test_name')}"[:300],
                        description=r.get("issue_text",""), category="security",
                        severity=BANDIT_SEV.get(r.get("issue_severity","LOW"), "low"),
                        confidence=BANDIT_CONF.get(r.get("issue_confidence","LOW"), "low"),
                        start_line=r.get("line_number"), end_line=r.get("line_range",[r.get("line_number")])[-1] if r.get("line_range") else r.get("line_number"),
                        evidence=(r.get("code") or "").strip()[:500], explanation=r.get("issue_text",""),
                        remediation="Review the Bandit guidance for this check and apply the documented remediation.",
                        suggested_patch="", suggested_tests=[], source="bandit",
                        verification_status="tool-confirmed", rule_id=r.get("test_id","")))
            except json.JSONDecodeError: warnings.append("Bandit output could not be parsed.")
    return findings, warnings
