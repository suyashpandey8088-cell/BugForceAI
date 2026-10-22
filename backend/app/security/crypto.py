import base64, hashlib
from cryptography.fernet import Fernet
from app.core.config import get_settings

def _fernet() -> Fernet:
    s = get_settings()
    if s.token_encryption_key:
        return Fernet(s.token_encryption_key.encode())
    key = base64.urlsafe_b64encode(hashlib.sha256(s.session_secret.encode()).digest())
    return Fernet(key)

def encrypt_token(token: str | None) -> str | None:
    return _fernet().encrypt(token.encode()).decode() if token else None

def decrypt_token(enc: str | None) -> str | None:
    if not enc: return None
    try: return _fernet().decrypt(enc.encode()).decode()
    except Exception: return None
