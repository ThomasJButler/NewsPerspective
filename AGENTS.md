## Build & Run

```bash
# Backend (FastAPI)
cd src/backend
pip install fastapi uvicorn sqlalchemy pydantic-settings openai requests python-dotenv
uvicorn main:app --reload --port 8000

# Frontend (Next.js + ShadCN)
cd src/frontend
npm install
npm run dev

# Trigger article processing
curl -X POST http://localhost:8000/api/refresh
```

## Validation

- Backend health: `curl http://localhost:8000/api/articles`
- Frontend: open `http://localhost:3000`
- Pipeline: `curl -X POST http://localhost:8000/api/refresh` then check /api/articles

## Operational Notes

- Copy `.env.template` to `.env` — required: `NEWS_API_KEY`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`
- SQLite DB auto-created at path in `DATABASE_URL` (default: `sqlite:///./newsperspective.db`)
- Frontend proxies `/api/*` to backend via Next.js rewrites in `next.config.js`
- Legacy v1 code is in the project root (run.py, batch_processor.py, etc.)

### Codebase Patterns

- Specs live in `specs/` — these are the source of truth for what to build
- Backend source: `src/backend/`
- Frontend source: `src/frontend/`
- Single AI call per article (sentiment + rewrite + TLDR + good_news flag)
- Uses chat completions endpoint (GPT-4o), not legacy completions
- SQLite via SQLAlchemy (no Azure Search dependency)
- Deduplication by article URL
