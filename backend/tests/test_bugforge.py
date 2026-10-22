import os, sys
os.environ["DATABASE_URL"] = "sqlite:///./test_bugforge.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from fastapi.testclient import TestClient

if os.path.exists("test_bugforge.db"): os.remove("test_bugforge.db")
from app.main import app
from app.services.ast_analyzer import analyze_python_ast
from app.services.finding_normalizer import validate_and_dedupe
from app.services.llm_review import LLMOutput
from pydantic import ValidationError

client = TestClient(app, raise_server_exceptions=False)

def auth_client(email="a@example.com"):
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/auth/register", json={"email": email, "password": "Password1", "display_name": "A"})
    assert r.status_code in (201, 409), r.text
    if r.status_code == 409:
        r = c.post("/api/v1/auth/login", json={"email": email, "password": "Password1"}); assert r.status_code == 200
    csrf = c.cookies.get("bugforge_csrf")
    c.headers.update({"x-csrf-token": csrf or ""})
    return c

# --- AST ---
def test_ast_mutable_default_and_eval():
    src = "def f(x=[]):\n    return eval(x)\n"
    findings, err = analyze_python_ast(src, "a.py")
    rules = {f["rule_id"] for f in findings}
    assert err is None and "AST101" in rules and "AST103" in rules

def test_ast_syntax_error():
    findings, err = analyze_python_ast("def broken(:\n", "a.py")
    assert err and findings[0]["rule_id"] == "AST001"

def test_ast_clean_code_no_high():
    findings, _ = analyze_python_ast("def add(a, b):\n    return a + b\n", "a.py")
    assert not [f for f in findings if f["severity"] in ("high", "critical")]

def test_open_with_not_flagged():
    findings, _ = analyze_python_ast("with open('x') as f:\n    print(f.read())\n", "a.py")
    assert not [f for f in findings if f["rule_id"] == "AST108"]

# --- normalizer ---
def test_invalid_llm_line_rejected():
    out = validate_and_dedupe([{"title": "x", "severity": "bogus", "confidence": "bogus", "category": "bogus",
                                "source": "llm", "file_path": "a.py", "start_line": 999}], {"a.py": "x=1\n"})
    assert out[0]["severity"] == "low" and out[0]["start_line"] is None and out[0]["verification_status"] == "line-unverified"

def test_dedupe():
    f = {"title": "Same issue here", "severity": "low", "confidence": "low", "category": "maintainability", "source": "ruff", "file_path": "a.py", "start_line": 1, "rule_id": "E1"}
    assert len(validate_and_dedupe([dict(f), dict(f)], {"a.py": "x\n"})) == 1

def test_llm_schema_rejects_bad_severity_type():
    with pytest.raises(ValidationError):
        LLMOutput.model_validate({"findings": [{"title": "t", "start_line": "not-a-number"}]})

# --- API auth / isolation ---
def test_unauthenticated_protected():
    assert client.get("/api/v1/reviews").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401

def test_register_login_me_logout():
    c = auth_client("flow@example.com")
    assert c.get("/api/v1/auth/me").json()["email"] == "flow@example.com"
    assert c.post("/api/v1/auth/logout").status_code == 200

def test_duplicate_register_conflict():
    c = TestClient(app)
    assert c.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "Password1"}).status_code == 201
    assert c.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "Password1"}).status_code == 409

def test_weak_password_rejected():
    assert client.post("/api/v1/auth/register", json={"email": "w@example.com", "password": "onlyletters"}).status_code == 422

BUGGY = '''import os
def load(user_input, cache=[]):
    cache.append(user_input)
    return eval(user_input)
try:
    risky()
except:
    pass
'''

def test_review_flow_and_isolation():
    c1, c2 = auth_client("owner@example.com"), auth_client("other@example.com")
    r = c1.post("/api/v1/reviews/code", json={"title": "t", "files": [{"path": "app.py", "content": BUGGY}], "include_llm": False})
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert r.json()["summary"]["total_findings"] >= 2
    assert any(f["rule_id"] == "AST103" for f in r.json()["findings"])
    assert c2.get(f"/api/v1/reviews/{rid}").status_code == 404  # isolation
    assert c1.get(f"/api/v1/reviews/{rid}/export?format=csv").status_code == 200
    assert "AST103" in c1.get(f"/api/v1/reviews/{rid}/export?format=json").text or "eval" in c1.get(f"/api/v1/reviews/{rid}/export?format=json").text
    assert c1.delete(f"/api/v1/reviews/{rid}").status_code == 200
    assert c1.get(f"/api/v1/reviews/{rid}").status_code == 404

def test_empty_and_oversized_rejected():
    c = auth_client("limits@example.com")
    assert c.post("/api/v1/reviews/code", json={"files": [{"path": "a.py", "content": "   "}]}).status_code == 422
    big = "x=1\n" * 40000
    assert c.post("/api/v1/reviews/code", json={"files": [{"path": "a.py", "content": big}]}).status_code == 422

def test_settings_persist_and_account_scope():
    c = auth_client("settings@example.com")
    assert c.patch("/api/v1/settings", json={"theme": "dark", "default_language": "python"}).json()["theme"] == "dark"
    assert c.get("/api/v1/settings").json()["theme"] == "dark"
    assert c.patch("/api/v1/settings", json={"theme": "purple"}).status_code == 422

def test_github_not_configured_is_honest():
    c = auth_client("gh@example.com")
    assert c.get("/api/v1/github/repositories").status_code == 400  # not connected
    cfg = client.get("/api/v1/auth/config").json()
    assert "google_configured" in cfg and "llm_configured" in cfg

def test_health(): assert client.get("/health").json()["status"] == "ok"
