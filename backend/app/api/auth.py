import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from authlib.integrations.starlette_client import OAuth
from app.core.config import get_settings
from app.database.session import get_db
from app.models.models import User, Identity, Preference
from app.schemas.schemas import RegisterIn, LoginIn, UserOut
from app.auth.deps import hash_password, verify_password, create_session_token, set_session_cookie, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
oauth = OAuth()
_s = get_settings()
if _s.google_configured:
    oauth.register(name="google", client_id=_s.google_client_id, client_secret=_s.google_client_secret,
                   server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                   client_kwargs={"scope": "openid email profile"})

def user_out(db: Session, u: User) -> UserOut:
    ids = db.query(Identity).filter(Identity.user_id == u.id).all()
    gh = next((i for i in ids if i.provider == "github"), None)
    return UserOut(id=u.id, email=u.email, display_name=u.display_name,
                   providers=[i.provider for i in ids],
                   github_username=gh.username if gh else "",
                   google_connected=any(i.provider == "google" for i in ids),
                   github_connected=bool(gh))

def _login_response(db, u, status=200):
    token = create_session_token(u.id)
    resp = JSONResponse({"user": user_out(db, u).model_dump()}, status_code=status)
    set_session_cookie(resp, token)
    return resp

@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(409, "An account with this email already exists. Try signing in.")
    u = User(email=body.email.lower(), display_name=body.display_name or body.email.split("@")[0],
             password_hash=hash_password(body.password))
    db.add(u); db.flush(); db.add(Preference(user_id=u.id)); db.commit(); db.refresh(u)
    return _login_response(db, u, status=201)

@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.lower()).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password. If you signed up with Google, use Google sign-in.")
    return _login_response(db, u)

@router.get("/google")
async def google_login(request: Request):
    if not get_settings().google_configured:
        raise HTTPException(503, "Google sign-in is not configured on this server. See docs/authentication.md.")
    request.session["oauth_state"] = secrets.token_urlsafe(24)
    request.session["oauth_nonce"] = secrets.token_urlsafe(24)
    return await oauth.google.authorize_redirect(request, get_settings().google_redirect_uri,
                                                 state=request.session["oauth_state"], nonce=request.session["oauth_nonce"])

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not get_settings().google_configured: raise HTTPException(503, "Google not configured")
    expected = request.session.pop("oauth_state", None)
    if not expected or request.query_params.get("state") != expected:
        raise HTTPException(400, "OAuth state validation failed. Please try signing in again.")
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(400, "Google authorization failed or was cancelled.")
    # Authlib validates signature/issuer/audience/exp/nonce against Google's JWKS during parse_id_token
    try:
        info = await oauth.google.parse_id_token(request, token, nonce=request.session.pop("oauth_nonce", None))
    except Exception:
        raise HTTPException(400, "Google ID token validation failed.")
    email = (info.get("email") or "").lower()
    if not email or not info.get("email_verified", True):
        raise HTTPException(400, "Google did not return a verified email.")
    sub = info["sub"]
    ident = db.query(Identity).filter(Identity.provider == "google", Identity.provider_user_id == sub).first()
    if ident:
        u = db.get(User, ident.user_id)
    else:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(email=email, display_name=info.get("name", email.split("@")[0])); db.add(u); db.flush()
            db.add(Preference(user_id=u.id))
        db.add(Identity(user_id=u.id, provider="google", provider_user_id=sub, email=email,
                        username=info.get("name", "")))
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409, "Identity conflict — contact support.")
    resp = RedirectResponse(f"{get_settings().frontend_url}/dashboard", status_code=302)
    set_session_cookie(resp, create_session_token(u.id))
    return resp

@router.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("bugforge_session", path="/"); resp.delete_cookie("bugforge_csrf", path="/")
    return resp

@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    return user_out(db, u)

@router.get("/config")
def auth_config():
    s = get_settings()
    return {"google_configured": s.google_configured, "github_configured": s.github_configured,
            "llm_configured": s.llm_configured, "llm_model": s.llm_model if s.llm_configured else ""}
