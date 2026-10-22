# Authentication
- Local: email + Argon2-hashed password (register/login), JWT in httpOnly cookie (7d), separate CSRF cookie + `x-csrf-token` header check on mutations, `Secure` in production, SameSite=Lax.
- Google: Authlib OpenID Connect (authorization-code + PKCE-capable client), server-side state + nonce, ID token validated by Authlib against Google JWKS (issuer/audience/signature/exp/nonce), verified email required. Setup: Google Cloud → OAuth consent screen → Web client → authorized origin `http://localhost:3000`, redirect `http://localhost:8000/api/v1/auth/google/callback`; set GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI in backend/.env. Never trust browser-supplied user IDs.
- Unconfigured Google returns HTTP 503 with setup guidance (no fake login).
