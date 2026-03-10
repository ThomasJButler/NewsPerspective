# News Perspective Legacy Notes

`READMEOLD.md` is retained only as legacy v1 reference material.

For the active v2 app:

- use [README.md](README.md) for setup and runtime instructions
- use the FastAPI backend in `src/backend/`
- use the Next.js frontend in `src/frontend/`

Do not use this file for current local setup, Docker setup, validation, or Ralph loop work. Root-level scripts are historical artifacts and are not part of the supported v2 runtime.

## Legacy root files

These files remain in the repo only so older implementation choices can be inspected when needed:

- `batch_processor.py`
- `run.py`
- `search.py`
- `web_app.py`
- `azure_ai_language.py`
- `azure_document_intelligence.py`
- `logger_config.py`

If a legacy behavior needs to be recovered, prefer git history or the archived specs/completed-plan records over treating these files as a supported runtime.
