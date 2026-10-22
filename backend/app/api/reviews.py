import csv, io, json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, Review, Finding, ReviewFile
from app.schemas.schemas import CodeReviewIn, PRReviewIn, ReviewOut, ReviewDetailOut, FindingOut
from app.auth.deps import get_current_user, require_csrf
from app.api.github import get_github_token
from app.services import github_service as gh
from app.services.review_orchestrator import run_review

router = APIRouter(prefix="/reviews", tags=["reviews"])

def counts(r: Review):
    c = {}
    for f in r.findings: c[f.severity] = c.get(f.severity, 0) + 1
    return c

def to_out(r: Review) -> ReviewOut:
    d = ReviewOut.model_validate(r); d.finding_counts = counts(r); return d

def owned(db, user, rid):
    r = db.get(Review, rid)
    if not r or r.user_id != user.id: raise HTTPException(404, "Review not found")
    return r

async def persist(db, user, title, source_type, label, files_map, result, github_url="", pr_number=None, head_sha=""):
    r = Review(user_id=user.id, title=title, source_type=source_type, language="python",
               status=result["status"], source_label=label, summary=result["summary"],
               warnings=result["warnings"], github_url=github_url, pr_number=pr_number, head_sha=head_sha)
    db.add(r); db.flush()
    for path, content in files_map.items(): db.add(ReviewFile(review_id=r.id, path=path, content=content))
    for f in result["findings"]:
        db.add(Finding(review_id=r.id, title=f.get("title","Finding"), description=f.get("description",""),
            category=f.get("category","maintainability"), severity=f.get("severity","low"),
            confidence=f.get("confidence","low"), file_path=f.get("file_path",""),
            start_line=f.get("start_line"), end_line=f.get("end_line"), evidence=f.get("evidence",""),
            explanation=f.get("explanation",""), remediation=f.get("remediation",""),
            suggested_patch=f.get("suggested_patch",""), suggested_tests=f.get("suggested_tests",[]),
            source=f.get("source","ast"), verification_status=f.get("verification_status","unverified"),
            rule_id=f.get("rule_id","")))
    db.commit(); db.refresh(r); return r

@router.post("/code", response_model=ReviewDetailOut, status_code=201)
async def review_code(body: CodeReviewIn, request: Request, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_csrf(request)
    if not any(f.content.strip() for f in body.files): raise HTTPException(422, "Source code is empty — paste or upload code first.")
    try:
        result = await run_review([{"path": f.path, "content": f.content} for f in body.files], include_llm=body.include_llm)
    except ValueError as e: raise HTTPException(422, str(e))
    r = await persist(db, u, body.title, "paste", body.files[0].path, result["files"], result)
    return detail(db, r)

@router.post("/pull-request", response_model=ReviewDetailOut, status_code=201)
async def review_pr(body: PRReviewIn, request: Request, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_csrf(request)
    try:
        pr = await gh.get_pr_with_files(get_github_token(db, u), body.owner, body.repo, body.number)
    except HTTPException: raise
    except (PermissionError, RuntimeError, LookupError) as e: raise HTTPException(502, str(e))
    py_files = [{"path": f["path"], "content": f["content"]} for f in pr["files"] if f["path"].endswith(".py") and f["content"]]
    if not py_files: raise HTTPException(422, "No analyzable Python file content was returned for this PR. BugForge currently analyzes Python only.")
    diff = "\n".join(f"--- {f['path']} ---\n{f['patch']}" for f in pr["files"] if f.get("patch"))
    try: result = await run_review(py_files, include_llm=body.include_llm, diff_text=diff)
    except ValueError as e: raise HTTPException(422, str(e))
    result["summary"] = {**result["summary"], "pr_purpose": pr["title"], "changed_files": [f["path"] for f in pr["files"]],
                         "analysis_scope": "Python files with retrievable content at the PR head revision; diff context included for the LLM."}
    r = await persist(db, u, f"PR #{pr['number']}: {pr['title']}", "github_pr", f"{body.owner}/{body.repo}#{pr['number']}",
                      result["files"], result, github_url=pr["html_url"], pr_number=pr["number"], head_sha=pr["head_sha"])
    return detail(db, r)

def detail(db, r: Review) -> ReviewDetailOut:
    base = ReviewOut.model_validate(r)
    d = ReviewDetailOut(**base.model_dump()); d.finding_counts = counts(r)
    d.findings = [FindingOut.model_validate(f) for f in r.findings]
    d.files = [{"path": f.path, "content": f.content} for f in r.files]
    return d

@router.get("", response_model=list[ReviewOut])
def list_reviews(db: Session = Depends(get_db), u: User = Depends(get_current_user), limit: int = 50, offset: int = 0):
    rows = db.query(Review).filter(Review.user_id == u.id).order_by(Review.created_at.desc()).offset(offset).limit(min(limit, 100)).all()
    return [to_out(r) for r in rows]

@router.get("/{review_id}", response_model=ReviewDetailOut)
def get_review(review_id: str, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    return detail(db, owned(db, u, review_id))

@router.delete("/{review_id}")
def delete_review(review_id: str, request: Request, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_csrf(request)
    r = owned(db, u, review_id); db.delete(r); db.commit(); return {"ok": True}

@router.get("/{review_id}/export")
def export_review(review_id: str, format: str = "json", db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    r = owned(db, u, review_id)
    if format == "csv":
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["title","category","severity","confidence","source","verification","file","line","rule","description","remediation"])
        for f in r.findings: w.writerow([f.title, f.category, f.severity, f.confidence, f.source, f.verification_status, f.file_path, f.start_line or "", f.rule_id, f.description, f.remediation])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="bugforge-{r.id}.csv"'})
    payload = {"review": {"id": r.id, "title": r.title, "status": r.status, "created_at": str(r.created_at), "summary": r.summary, "warnings": r.warnings, "github_url": r.github_url, "head_sha": r.head_sha},
               "findings": [{c.name: getattr(f, c.name) for c in Finding.__table__.columns if c.name not in ("review_id",)} for f in r.findings]}
    return PlainTextResponse(json.dumps(payload, indent=2, default=str), media_type="application/json",
                             headers={"Content-Disposition": f'attachment; filename="bugforge-{r.id}.json"'})
