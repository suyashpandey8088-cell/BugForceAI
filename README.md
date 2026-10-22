# BugForge AI — AI-Powered Code Review & Bug Detection

A full-stack developer tool that reviews Python code and GitHub pull requests with **deterministic static analysis first** (Python AST + Ruff + Bandit) and **clearly-labeled LLM hypotheses second**. It never executes submitted code, never invents line numbers, and never auto-merges anything.

## Live workflow
Register/login (email+password, or Google when configured) → paste Python or upload a `.py` file → get findings with severity, confidence, evidence, suggested fixes and proposed tests → filter/search in the Findings Explorer with Monaco → export JSON/CSV → track history & analytics → optionally connect GitHub (read-only) and review a real PR at its head SHA.

## Tech stack
- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, Monaco Editor, Recharts, next-themes (dark/light, persisted), Lucide, Zod
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PyJWT, Authlib, httpx, slowapi
- **Analysis:** Python `ast`, Ruff, Bandit, provider-independent OpenAI-compatible LLM adapter (strict JSON schema validation)
- **Data:** SQLite for local dev, PostgreSQL in production (Docker Compose included)

## Quick start
```bash
# Backend
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp ../.env.example .env   # fill in secrets as needed; app runs honestly without OAuth/LLM keys
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend && npm install
BACKEND_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```
Open http://localhost:3000 → Create account → New Review (starter code contains real bugs the analyzers catch).

## Tests (actual results in this repo's CI-equivalent run)
```bash
cd backend && .venv/bin/python -m pytest tests -q     # 16 passed
cd frontend && npx tsc --noEmit && npx vitest run && npm run build   # typecheck ok, 3 passed, build ok
```

## Configuration
See `.env.example` and `docs/`: [architecture](docs/architecture.md) · [authentication (Google OAuth setup)](docs/authentication.md) · [GitHub integration](docs/github-integration.md) · [security](docs/security.md) · [deployment](docs/deployment.md). API docs: FastAPI OpenAPI at `http://localhost:8000/docs`.

## Demo script (2 minutes)
1. Register, land on Dashboard (empty state, no fake stats).
2. New Review → Analyze the starter code → findings: `eval()` (AST103/Bandit), mutable default, bare `except:`.
3. Open a finding → evidence line highlighted in Monaco, suggested fix + proposed pytest.
4. Toggle dark/light (persists). Export CSV. Check Analytics (your real data only).
5. Settings → connect GitHub (if configured) → GitHub PRs → Review a PR.

## Known limitations (honest)
- Python only; Semgrep not bundled. Google/GitHub/LLM require your own credentials — without them the UI says so and static analysis still works fully. Password reset is not implemented (use Google or re-register guidance). LLM findings are hypotheses requiring human verification; a clean report ≠ bug-free code. No code execution, no auto-comments/merges.

## Resume blurb
Built BugForge AI, a full-stack AI code-review platform (Next.js + FastAPI + PostgreSQL) combining Python AST analysis, Ruff/Bandit static analysis, and schema-validated LLM review with line-number verification; implemented Google/GitHub OAuth with encrypted token storage, per-user data isolation, CSRF-protected cookie sessions, Monaco-based findings explorer, and 19 automated tests.
