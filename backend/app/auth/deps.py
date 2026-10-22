import datetime, secrets
import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.config import get_settings
from app.database.session import get_db
from app.models.models import User

ph = PasswordHasher()
ALG = "HS256"

def hash_password(pw: str) -> str: return ph.hash(pw)
def verify_password(pw: str, h: str | None) -> bool:
    if not h: return False
    try: return ph.verify(h, pw)
    except VerifyMismatchError: return False
    except Exception: return False

def create_session_token(user_id: str) -> str:
    s = get_settings()
    payload = {"sub": user_id, "iat": datetime.datetime.now(datetime.timezone.utc),
               "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7),
               "csrf": secrets.token_urlsafe(24)}
    return jwt.encode(payload, s.session_secret, algorithm=ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().session_secret, algorithms=[ALG])

def set_session_cookie(resp, token: str):
    s = get_settings()
    secure = s.environment == "production"
    resp.set_cookie("bugforge_session", token, httponly=True, secure=secure,
                    samesite="lax", max_age=7*24*3600, path="/")
    try:
        csrf = decode_token(token)["csrf"]
        resp.set_cookie("bugforge_csrf", csrf, httponly=False, secure=secure,
                        samesite="lax", max_age=7*24*3600, path="/")
    except Exception: pass

async def get_current_user(request: Request, db: Session = Depends(get_db),
                           session: str | None = Cookie(default=None, alias="bugforge_session")) -> User:
    if not session: raise HTTPException(401, "Not authenticated")
    try: payload = decode_token(session)
    except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired session")
    user = db.get(User, payload.get("sub", ""))
    if not user or not user.is_active: raise HTTPException(401, "User not found")
    # CSRF: state-changing requests must echo the double-submit token
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        # OAuth callbacks / login endpoints are GET or exempted by route; API mutations check header
        if request.headers.get("x-csrf-token"):
            if request.headers["x-csrf-token"] != payload.get("csrf"):
                raise HTTPException(403, "CSRF token mismatch")
    request.state.user = user
    return user

def require_csrf(request: Request):
    """Explicit CSRF check used by mutation routes."""
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        cookie_token = request.cookies.get("bugforge_session")
        hdr = request.headers.get("x-csrf-token")
        if cookie_token and not hdr:
            raise HTTPException(403, "Missing CSRF token")
        if cookie_token and hdr:
            try:
                if decode_token(cookie_token).get("csrf") != hdr:
                    raise HTTPException(403, "CSRF token mismatch")
            except jwt.PyJWTError:
                raise HTTPException(401, "Invalid session")
