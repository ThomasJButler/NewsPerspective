# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (no requirements.txt — infer from imports)
pip install requests openai python-dotenv streamlit pandas tabulate

# Single-run processing (up to MAX_ARTICLES_PER_RUN articles, default 20)
python run.py

# Batch processing (up to BATCH_TOTAL_ARTICLES articles, default 500)
python batch_processor.py

# Streamlit web UI
streamlit run web_app.py

# CLI search tool
python search.py                         # Latest 10 articles
python search.py --keyword "technology"
python search.py --source "BBC"
python search.py --recent 24             # Last 24 hours
python search.py --sources               # Summary by source
python search.py --test                  # Test Azure Search connection
```

There is no test suite.

## Environment Setup

Copy `.env.template` to `.env`. Required keys: `NEWS_API_KEY`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_SEARCH_KEY`, `AZURE_SEARCH_ENDPOINT`. Optional (services gracefully disable if absent): `AZURE_AI_LANGUAGE_*`, `AZURE_DOCUMENT_INTELLIGENCE_*`.

## Architecture

**Pipeline flow (both `run.py` and `batch_processor.py`):**
1. Fetch articles from NewsAPI (UK general + sports, configurable mix)
2. Analyse each headline with Azure AI Language → sentiment + confidence scores
3. Extract problematic phrases via keyword matching in `AzureAILanguage.extract_problematic_phrases()`
4. If rewrite needed: optionally extract article body via Azure Document Intelligence, then call Azure OpenAI completions to rewrite
5. Upload processed docs to Azure AI Search index

**Rewrite decision logic** (duplicated in both `run.py` and `batch_processor.py`): rewrite if `negative_confidence > 60` OR problematic phrases found, with `confidence >= 60` threshold. Uses gpt-35-turbo-instruct via the **completions** endpoint (not chat completions).

**Azure Search document schema:** `id`, `original_title`, `rewritten_title`, `original_content`, `source`, `published_date`, `article_url`, `was_rewritten` (bool), `original_tone`, `confidence_score` (int), `rewrite_reason`

**Module structure:**
- `run.py` — procedural single-run script (executes at import time, not just when called as main)
- `batch_processor.py` — `BatchProcessor` class with configurable `BATCH_SIZE`/`BATCH_DELAY`/`TOTAL_ARTICLES`
- `azure_ai_language.py` — `AzureAILanguage` class; instantiates global `ai_language` singleton at module load
- `azure_document_intelligence.py` — `AzureDocumentIntelligence` class; instantiates global `document_intelligence` singleton at module load
- `web_app.py` — Streamlit app querying Azure Search directly via REST (no Python SDK)
- `search.py` — CLI wrapper around Azure Search REST; validates env vars at module load (raises on import if credentials missing)
- `logger_config.py` — `setup_logger()`, `StatsTracker`, `@log_performance` decorator, `log_error_details()`

**Fallback behaviour:** Both Azure Language and Document Intelligence services check for credentials on init and set `self.enabled = False` if absent, returning neutral/empty fallback results rather than raising exceptions.

**Logging:** Writes rotating logs to `logs/` directory (auto-created). Daily log files `logs/news_perspective_YYYYMMDD.log` plus `logs/errors.log`.
