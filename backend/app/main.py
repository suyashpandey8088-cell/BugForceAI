from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.session import Base, engine, get_db
from app.models import models  # noqa: F401
from app.models.models import User, Review
from app.auth.deps import get_current_user
from app.api import auth, github, reviews, settings as settings_api

s = get_settings()
Base.metadata.create_all(bind=engine)  # dev convenience; production: Alembic

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app = FastAPI(title="BugForge AI API", version="1.0.0",
              description="AI-powered code review: AST + Ruff/Bandit static analysis, validated LLM hypotheses, GitHub PR review.")
app.state.limiter = limiter
app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["*"])
app.add_middleware(SessionMiddleware, secret_key=s.session_secret, same_site="lax",
                   https_only=(s.environment == "production"))

@app.exception_handler(RateLimitExceeded)
async def rl_handler(request: Request, exc):
    return JSONResponse({"detail": "Rate limit exceeded. Slow down and retry."}, status_code=429)

@app.get("/health")
def health():
    return {"status": "ok", "service": "bugforge-ai", "google_configured": s.google_configured,
            "github_configured": s.github_configured, "llm_configured": s.llm_configured}

@app.get("/api/v1/analytics/summary")
def analytics_summary(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    rows = db.query(Review).filter(Review.user_id == u.id).all()
    by_sev, by_cat, by_src, over_time, fle = {}, {}, {}, {}, {}
    for r in rows:
        day = str(r.created_at)[:10]; over_time[day] = over_time.get(day, 0) + 1
        for f in r.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
            by_src[f.source] = by_src.get(f.source, 0) + 1
            fle[f.file_path] = fle.get(f.file_path, 0) + 1
    return {"reviews": len(rows), "completed": sum(1 for r in rows if r.status == "completed"),
            "partial": sum(1 for r in rows if r.status == "partial"), "failed": sum(1 for r in rows if r.status == "failed"),
            "by_severity": by_sev, "by_category": by_cat, "by_source": by_src,
            "over_time": [{"date": k, "reviews": v} for k, v in sorted(over_time.items())],
            "top_files": sorted(({"file": k, "findings": v} for k, v in fle.items()), key=lambda x: -x["findings"])[:8]}

app.include_router(auth.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(settings_api.router, prefix="/api/v1")
