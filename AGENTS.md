# AGENTS.md

## Repo purpose
NewsPerspective v3.0 is a two-part app:
- `src/backend/` is a FastAPI service that fetches headlines from NewsAPI, processes them with OpenAI, and stores article data in SQLite.
- `src/frontend/` is a Next.js + ShadCN UI for browsing rewritten headlines, summaries, source filters, search, and settings.

Legacy v1 runtime files were removed from the repo root on 2026-03-10. Use git history or the archived legacy docs for reference, and do not recreate root-level legacy runtime files unless the current task explicitly includes migration or archival work.

## Ralph operating rules
- Read `IMPLEMENTATION_PLAN.md` before changing code.
- In plan mode, update the plan only. Do not implement.
- In build mode, execute exactly one highest-priority unchecked task or one tightly related sub-slice of that task.
- Keep `AGENTS.md` operational and compact. Status, discoveries, and sequencing belong in `IMPLEMENTATION_PLAN.md`.
- Prefer small, reversible edits over broad refactors.
- Confirm a feature is actually missing before building it.
- Keep specs in `specs/` as the functional source of truth. If code and specs disagree, document the mismatch in `IMPLEMENTATION_PLAN.md` before changing behavior.

## Architecture summary
- Backend app: `src/backend/main.py`
- Backend modules live under `src/backend/`
- Frontend app lives under `src/frontend/`
- Specs live under `specs/`
- Shared Ralph loop files live at repo root:
  - `AGENTS.md`
  - `PROMPT_plan.md`
  - `PROMPT_build.md`
  - `IMPLEMENTATION_PLAN.md`
  - `loop.sh`

## Current product rules
- The backend no longer owns a server-side `NEWS_API_KEY`.
- Refresh requests must send the user key via the `X-News-Api-Key` header.
- Read-only article endpoints should keep working without a key by serving cached data.
- Single AI call per article should produce sentiment, rewrite decision/output, TLDR, and good-news flag.
- SQLite is the current persistence layer. Avoid introducing Azure Search into v3 work unless the task explicitly says so.

## Working agreements
- Keep changes scoped to the active plan item.
- Do not introduce placeholder implementations.
- Do not silently rewrite architecture when a local fix is sufficient.
- Do not auto-push, auto-tag, or auto-release from the loop.
- Make docs match the running system when a task touches setup, commands, or runtime behavior.

## Validation commands
Run the smallest meaningful validation that proves the changed slice works.

### Backend
```bash
source src/backend/.venv/bin/activate
python -m pip install -r src/backend/requirements.txt
python -m unittest src.backend.tests.test_api_smoke -v
python -m unittest src.backend.tests.test_refresh_processing -v
python -m unittest src.backend.tests.test_manual_integration_evidence -v
python -m unittest src.backend.tests.test_config -v
uvicorn src.backend.main:app --reload --port 8000
```

### Frontend
```bash
cd src/frontend
npm install
npm run lint
npm run typecheck
npm run dev
```

### Manual integration checks
```bash
# list cached articles
curl http://localhost:8000/api/articles

# trigger refresh with user-supplied key
curl --config - <<EOF
url = "http://localhost:8000/api/refresh"
request = POST
header = "X-News-Api-Key: ${NEWS_API_KEY:?set NEWS_API_KEY in this shell first}"
EOF
```

## Documentation update rules
- Update `IMPLEMENTATION_PLAN.md` whenever you discover a blocker, hidden dependency, or follow-up task.
- Update `README.md` when setup or architecture details change.
- Update this file only when repo-wide operating rules or validation commands change.

## Safety rules
- Never commit secrets, tokens, or populated `.env` files.
- Treat `.env.template` as documentation, not as a secret store.
- Avoid destructive file moves until the relevant step in `IMPLEMENTATION_PLAN.md` is active.
