# NewsPerspective v2

NewsPerspective v2 is a two-part app:

- FastAPI backend in `src/backend/`
- Next.js frontend in `src/frontend/`

The active product flow is: browse cached processed articles without a NewsAPI key, then trigger refreshes by sending a user-supplied key in the `X-News-Api-Key` header. Root-level v1 scripts remain in the repo only as legacy reference.

## Runtime overview

- Backend entrypoint: `uvicorn src.backend.main:app --reload --port 8000`
- Frontend entrypoint: `cd src/frontend && npm run dev`
- Frontend proxy: `src/frontend/next.config.ts` rewrites `/api/*` to `BACKEND_ORIGIN` and defaults to `http://localhost:8000`
- Database: SQLite via `DATABASE_URL`
- OpenAI config: `OPENAI_API_KEY` and optional `OPENAI_MODEL`
- NewsAPI key: request-scoped only, never stored as a backend env var

## Local setup

Node is pinned via `.nvmrc` to `22.17.0`.

Create the backend environment from the repo root:

```bash
python3 -m venv src/backend/.venv
source src/backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/backend/requirements.txt
```

Create a repo-root `.env` from `.env.template`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./newsperspective.db
```

`NEWS_API_KEY` is intentionally absent from backend env config. Refresh requests must send the user's key in the `X-News-Api-Key` header.

## Run locally

Start the backend from the repo root:

```bash
source src/backend/.venv/bin/activate
uvicorn src.backend.main:app --reload --port 8000
```

In a second shell, start the frontend:

```bash
cd src/frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.

Useful manual checks:

```bash
curl http://localhost:8000/api/articles

curl -X POST http://localhost:8000/api/refresh \
  -H "X-News-Api-Key: $NEWS_API_KEY"

curl http://localhost:8000/api/refresh/status
```

If cached browse is empty, seed deterministic local data first:

```bash
source src/backend/.venv/bin/activate
python -m src.backend.scripts.seed_manual_integration_data
```

## Docker app flow

The supported container workflow lives under `src/frontend/compose.yaml`. It starts a seeded backend and the frontend dev server together.

Start the app stack:

```bash
docker compose -f src/frontend/compose.yaml up --build app
```

Run the seeded Playwright cached-browse spec against that stack:

```bash
docker compose -f src/frontend/compose.yaml run --rm playwright
```

Stop the stack:

```bash
docker compose -f src/frontend/compose.yaml down
```

If dependencies changed and you need a clean container `node_modules` volume:

```bash
docker compose -f src/frontend/compose.yaml down -v
```

## Validation commands

Backend:

```bash
source src/backend/.venv/bin/activate
python -m unittest src.backend.tests.test_api_smoke -v
python -m unittest src.backend.tests.test_refresh_processing -v
python -m unittest src.backend.tests.test_manual_integration_evidence -v
```

Frontend:

```bash
cd src/frontend
npm run lint
npm run typecheck
npx playwright test tests/e2e/cached-browse.spec.ts
```

If `next build` is needed in this repo, prefer:

```bash
cd src/frontend
npx next build --webpack
```

## Ralph loop

Repo-local loop files:

- `AGENTS.md`
- `PROMPT_plan.md`
- `PROMPT_build.md`
- `IMPLEMENTATION_PLAN.md`
- `loop.sh`

Suggested workflow:

```bash
./loop.sh plan 1
./loop.sh build 1
```

Add `coach` or `homer` to enable the corresponding explanation mode:

```bash
./loop.sh build 1 coach
./loop.sh build 1 homer
```

On a trusted local machine, if Codex needs permission to write `.git` during build-mode commits:

```bash
RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1
```

## Legacy boundary

`READMEOLD.md` is legacy reference material. Root-level files such as `batch_processor.py`, `run.py`, `search.py`, and `web_app.py` are not part of the active v2 runtime.
