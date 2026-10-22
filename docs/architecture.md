# Architecture
Monorepo: `frontend/` (Next.js 15 + TypeScript + Tailwind + Monaco + Recharts + next-themes) talks to `backend/` (FastAPI + SQLAlchemy 2 + Alembic) only through `/api/v1/*` (Next rewrites proxy to `BACKEND_URL`, so browsers never call localhost directly).
Pipeline: input validation → Python AST (ast module, no execution) → Ruff + Bandit (subprocess, no shell, temp dir, timeout) → optional OpenAI-compatible LLM (strict pydantic JSON schema, bounded retry, line validation) → dedupe/normalize → PostgreSQL/SQLite persistence.
Layers: `app/api` (routes) · `app/services` (ast_analyzer, static_analyzer, llm_review, finding_normalizer, review_orchestrator, github_service) · `app/auth`, `app/security` (Fernet token encryption), `app/models`, `app/schemas`.
