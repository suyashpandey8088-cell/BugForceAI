import secrets, urllib.parse
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.session import get_db
from app.models.models import User, Identity
from app.auth.deps import get_current_user
from app.security.crypto import encrypt_token, decrypt_token
from app.services import github_service as gh

router = APIRouter(prefix="/github", tags=["github"])

def get_github_token(db: Session, user: User) -> str:
    ident = db.query(Identity).filter(Identity.user_id == user.id, Identity.provider == "github").first()
    tok = decrypt_token(ident.encrypted_access_token) if ident else None
    if not tok: raise HTTPException(400, "GitHub is not connected. Connect GitHub in Settings first.")
    return tok

@router.get("/connect")
async def connect(request: Request, u: User = Depends(get_current_user)):
    s = get_settings()
    if not s.github_configured: raise HTTPException(503, "GitHub integration is not configured on this server. See docs/github-integration.md.")
    state = secrets.token_urlsafe(24); request.session["gh_state"] = state; request.session["gh_user"] = u.id
    params = urllib.parse.urlencode({"client_id": s.github_client_id, "redirect_uri": s.github_redirect_uri,
                                     "scope": "repo read:user", "state": state})
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}", status_code=302)

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    if request.query_params.get("state") != request.session.get("gh_state"):
        raise HTTPException(400, "GitHub OAuth state validation failed.")
    user_id = request.session.get("gh_user")
    if not user_id: raise HTTPException(401, "Session expired — sign in and reconnect GitHub.")
    code = request.query_params.get("code")
    async with httpx.AsyncClient(timeout=30) as c:
        tr = await c.post("https://github.com/login/oauth/access_token",
                          data={"client_id": s.github_client_id, "client_secret": s.github_client_secret,
                                "code": code, "redirect_uri": s.github_redirect_uri},
                          headers={"Accept": "application/json"})
        token = (tr.json() or {}).get("access_token")
        if not token: raise HTTPException(400, "GitHub authorization failed.")
        ur = await c.get("https://api.github.com/user", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        if ur.status_code != 200: raise HTTPException(400, "Could not fetch GitHub profile.")
        profile = ur.json()
    ident = db.query(Identity).filter(Identity.user_id == user_id, Identity.provider == "github").first()
    if ident:
        ident.encrypted_access_token = encrypt_token(token); ident.username = profile["login"]
        ident.provider_user_id = str(profile["id"])
    else:
        db.add(Identity(user_id=user_id, provider="github", provider_user_id=str(profile["id"]),
                        email=profile.get("email") or "", username=profile["login"],
                        encrypted_access_token=encrypt_token(token)))
    db.commit()
    return RedirectResponse(f"{s.frontend_url}/github?connected=1", status_code=302)

@router.post("/disconnect")
def disconnect(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    db.query(Identity).filter(Identity.user_id == u.id, Identity.provider == "github").delete()
    db.commit(); return {"ok": True}

@router.get("/repositories")
async def repos(page: int = 1, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    try: return {"repositories": await gh.list_repos(get_github_token(db, u), page)}
    except (PermissionError, RuntimeError, LookupError) as e: raise HTTPException(502, str(e))

@router.get("/repositories/{owner}/{repo}/pulls")
async def pulls(owner: str, repo: str, page: int = 1, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    try: return {"pulls": await gh.list_pulls(get_github_token(db, u), owner, repo, page)}
    except (PermissionError, RuntimeError, LookupError) as e: raise HTTPException(502, str(e))

@router.get("/pulls/{owner}/{repo}/{number}")
async def pull_detail(owner: str, repo: str, number: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    try:
        pr = await gh.get_pr_with_files(get_github_token(db, u), owner, repo, number)
        pr["files"] = [{k: v for k, v in f.items() if k != "content"} for f in pr["files"]]
        return pr
    except (PermissionError, RuntimeError, LookupError) as e: raise HTTPException(502, str(e))
