# News Perspective

A tool to fetch news headlines and rewrite them in a more positive, factual tone.

`READMEOLD.md` is legacy reference material. For the current v2 app, use the FastAPI backend in `src/backend/` and ignore the old root scripts like `batch_processor.py`, `run.py`, `search.py`, and `web_app.py`.

## Current v2 backend

Create and activate the local environment:

```bash
python3 -m venv src/backend/.venv
source src/backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/backend/requirements.txt
```

Create a repo-root `.env` file with:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./newsperspective.db
```

Run the current backend API from the repo root:

```bash
uvicorn src.backend.main:app --reload --port 8000
```

Refresh cached articles with your own NewsAPI key:

```bash
curl -X POST http://localhost:8000/api/refresh \
  -H "X-News-Api-Key: $NEWS_API_KEY"
```

## Legacy notes

Legacy root scripts are preserved only for reference:

- `batch_processor.py`
- `run.py`
- `search.py`
- `web_app.py`
- `azure_ai_language.py`
- `azure_document_intelligence.py`
- `logger_config.py`

They are not part of the active v2 runtime and should not be used for current setup or local development.
