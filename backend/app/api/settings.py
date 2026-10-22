from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, Preference, Identity
from app.schemas.schemas import SettingsOut, SettingsPatch
from app.auth.deps import get_current_user, require_csrf

router = APIRouter(tags=["settings"])

def _prefs(db, u):
    p = db.query(Preference).filter(Preference.user_id == u.id).first()
    if not p: p = Preference(user_id=u.id); db.add(p); db.commit(); db.refresh(p)
    return p

def _out(db, u):
    p = _prefs(db, u); ids = db.query(Identity).filter(Identity.user_id == u.id).all()
    gh = next((i for i in ids if i.provider == "github"), None)
    return SettingsOut(theme=p.theme, default_language=p.default_language, llm_enabled=p.llm_enabled,
        include_info_findings=p.include_info_findings, display_name=u.display_name, email=u.email,
        google_connected=any(i.provider=="google" for i in ids), github_connected=bool(gh),
        github_username=gh.username if gh else "")

@router.get("/settings", response_model=SettingsOut)
def get_settings_api(db: Session = Depends(get_db), u: User = Depends(get_current_user)): return _out(db, u)

@router.patch("/settings", response_model=SettingsOut)
def patch_settings(body: SettingsPatch, request: Request, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_csrf(request)
    p = _prefs(db, u)
    for k, v in body.model_dump(exclude_none=True).items():
        if k == "display_name": u.display_name = v
        else: setattr(p, k, v)
    db.commit(); return _out(db, u)

@router.delete("/account")
def delete_account(request: Request, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_csrf(request)
    db.delete(u); db.commit()  # cascades reviews, findings, identities, preferences
    from fastapi.responses import JSONResponse
    resp = JSONResponse({"ok": True}); resp.delete_cookie("bugforge_session", path="/"); resp.delete_cookie("bugforge_csrf", path="/")
    return resp
