# ✅ NewsPerspectiveAI — Development To-Do List

This file outlines key improvements and feature ideas for upcoming versions of the project.

---

## 🔁 Data & Ingestion Improvements

- [x] 🔼 **Increase the number of articles fetched per run (support pagination)**
  - [x] Remove 5-article limit in `run.py` 
  - [x] Add pagination support for NewsAPI (max 100 per request, up to 1000 per day)
  - [x] Add configuration variable for articles per run
  - [x] Implement page looping with rate limiting
  - [x] Add error handling for API rate limits

- [ ] 🌐 **Add support for direct scraping from trusted sources** *(Future Reference Plan)*:
  
  ### **🌍 Major International Sources**
  - [ ] **CNN** - RSS: `http://rss.cnn.com/rss/edition.rss` | Selectors: `.cd__headline`, `.zn-body__paragraph`
  - [ ] **BBC News** - RSS: `http://feeds.bbci.co.uk/news/rss.xml` | Selectors: `.media__title`, `.story-body__inner`
  - [ ] **Reuters** - RSS: `https://www.reuters.com/rssFeed/topNews` | Selectors: `.ArticleHeader_headline`, `.StandardArticleBody_body`
  - [ ] **AP News** - RSS: `https://rsshub.app/ap/topics/apf-topnews` | Selectors: `.Page-headline`, `.RichTextStoryBody`
  - [ ] **New York Times** - RSS: `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` | Selectors: `.css-1j88qqx`, `.css-18sbwfn`
  - [ ] **Washington Post** - RSS: `http://feeds.washingtonpost.com/rss/world` | Selectors: `[data-qa="headline"]`, `.article-body`
  - [ ] **Wall Street Journal** - Selectors: `.wsj-article-headline`, `.article-content`

  ### **🇪🇺 European Sources**
  - [ ] **The Guardian** - API: `https://open-platform.theguardian.com/` | RSS: `https://www.theguardian.com/world/rss`
  - [ ] **Sky News** - RSS: `http://feeds.skynews.com/feeds/rss/world.xml` | Selectors: `.sdc-article-header__headline`, `.sdc-article-body`
  - [ ] **Daily Mail** - Selectors: `.mol-para-with-font`, `.articleText`
  - [ ] **Telegraph** - Selectors: `.headline__text`, `.article-body-text`
  - [ ] **Le Monde** (FR) - RSS: `https://www.lemonde.fr/rss/une.xml` | Selectors: `.article__title`, `.article__content`
  - [ ] **Der Spiegel** (DE) - RSS: `https://www.spiegel.de/schlagzeilen/tops/index.rss` | Selectors: `.headline-intro`, `.article-section`

  ### **💼 Tech & Business**
  - [ ] **TechCrunch** - RSS: `http://feeds.feedburner.com/TechCrunch/` | Selectors: `.article__title`, `.article-content`
  - [ ] **Ars Technica** - RSS: `http://feeds.arstechnica.com/arstechnica/index` | Selectors: `.heading`, `.post-content`
  - [ ] **Bloomberg** - Selectors: `.lede-text-only__highlight`, `.body-copy-v2`
  - [ ] **Financial Times** - Selectors: `.article__headline--wrapper`, `.article__content-core`
  - [ ] **Forbes** - Selectors: `.headlineText`, `.article-body`

  ### **🗺️ Alternative & International**
  - [ ] **Al Jazeera** - RSS: `https://www.aljazeera.com/xml/rss/all.xml` | Selectors: `.article-header__title`, `.wysiwyg`
  - [ ] **NPR** - RSS: `https://feeds.npr.org/1001/rss.xml` | Selectors: `.storytitle`, `.storytext`
  - [ ] **Politico** - RSS: `https://rss.politico.com/politics-news.xml` | Selectors: `.headline`, `.story-text`
  - [ ] **The Hill** - RSS: `https://thehill.com/news/feed/` | Selectors: `.headline__text`, `.field-item`
  - [ ] **Axios** - Selectors: `.gtm-story-title`, `.gtm-story-text`

  ### **🌏 Non-English (with Translation)**
  - [ ] **NHK World** (Japan) - RSS: `https://www3.nhk.or.jp/rss/news/cat0.xml` | Translation: Azure Translator
  - [ ] **Deutsche Welle** (Germany) - RSS: `https://rss.dw.com/xml/rss-en-all` | Selectors: `.col2 h1`, `.longText`
  - [ ] **RT** (Russia) - RSS: `https://www.rt.com/rss/` | Selectors: `.article__heading`, `.article__text`

  ### **📋 Scraping Implementation Plan**
  ```python
  # Architecture Structure:
  scrapers/
  ├── base_scraper.py          # Abstract scraper class
  ├── rss_scraper.py           # RSS feed parser
  ├── html_scraper.py          # BeautifulSoup HTML parser
  ├── sources/
  │   ├── bbc_scraper.py       # BBC-specific logic
  │   ├── cnn_scraper.py       # CNN-specific logic
  │   └── [source]_scraper.py  # Each source
  └── scraper_manager.py       # Orchestrates all scrapers
  ```

  **Implementation Strategy per Source:**
  1. **RSS First**: Try RSS feed for structured data
  2. **HTML Fallback**: Parse main page if RSS fails
  3. **Rate Limiting**: 1-2 requests per second per source
  4. **robots.txt Compliance**: Check and respect robots.txt
  5. **Error Handling**: Graceful fallback if source unavailable
  6. **Caching**: Cache articles to avoid re-scraping
  7. **Content Validation**: Ensure article has headline + content

- [ ] 🧠 **Compare headline vs article content** *(Advanced Analysis)*:
  - [ ] **Clickbait Detection Engine**:
    - [ ] Analyze headline sentiment vs article content sentiment
    - [ ] Use prompt: `"Rate this headline's accuracy vs content: [HEADLINE] vs [FIRST_PARAGRAPH]. Return: ACCURATE/SLIGHTLY_EXAGGERATED/CLICKBAIT"`
    - [ ] Store confidence score (0-100) for rewrite necessity
  - [ ] **Smart Rewriting Logic**:
    - [ ] Only rewrite if confidence score < 70 (needs improvement)
    - [ ] Preserve factual accuracy while reducing sensationalism
    - [ ] Add rewrite justification to metadata
  - [ ] **Tone Analysis & Flagging**:
    - [ ] Flag extremely misaligned headlines (clickbait score > 80)
    - [ ] Log flagged articles for manual review
    - [ ] Track source reliability over time
    - [ ] Generate daily summary of most misleading sources

---

## 🧠 Rewriting Logic

- [x] Use OpenAI prompt engineering to:
  - [x] Rewrite *only* if needed
  - [x] Return a summary of tone difference (optional)
- [x] Add confidence score or justification from model
- [x] Support different tone styles:
  - [x] Positive
  - [x] Factual
  - [x] Neutral
  - [ ] Satirical (just for fun)

---

## 🔍 Azure Search + Data Handling

- [x] Display most recent entries in the terminal/log
- [x] Add basic search interface (CLI or web)
- [x] Add filtering by:
  - [x] Source
  - [x] Date
  - [ ] Confidence score (future feature)

---

## 🌐 Frontend Ideas

- [ ] ✅ Simple web viewer (Streamlit, Flask, or FastAPI)
- [ ] 🧩 Chrome Extension (replaces headlines in-page with rewritten versions)
- [ ] 📱 Mobile-friendly news feed (PWA-style)

---

## 🚀 Next Level Possibilities

- [ ] **Web Interface** - Beautiful dashboard to browse your positive news
- [ ] **Chrome Extension** - Replace negative headlines on websites with your rewritten versions
- [ ] **Daily Email Digest** - Automated positive news summaries
- [ ] **API Service** - Other apps could use your positive news data
- [ ] **Trend Analysis** - Track which sources are most negative over time

---

## ⚡ Immediate Next Steps

- [ ] Build a simple web viewer (Streamlit/Flask)
- [ ] Add automated scheduling (run daily)
- [ ] Implement source bias tracking
- [ ] Create export features (JSON, CSV)
- [ ] Add "Good News Only" sorting mechanic (filter rewritten articles)

---

## 🔐 Security & Deployment

- [ ] Move keys to `.env` (already done!)
- [ ] Use Azure Key Vault (stretch goal)
- [ ] Create deployable Azure Function or Cron job
- [ ] Add GitHub Actions for auto-deploy / scheduled runs

---

## 🧪 Testing & Monitoring

- [x] Add logging (basic at first)
- [x] Add error reporting (e.g. failed rewrites)
- [x] Test edge cases:
  - [x] No content
  - [x] Already positive headlines
  - [x] Misleading titles

---

## 📊 Azure AI Foundry (MLflow) Integration

### **Goal:** Implement MLflow tracking for NewsPerspective to monitor AI performance and operational metrics.

### **Steps:**

1.  **Install Azure ML SDK & MLflow:**
    *   Add `azure-ai-ml` and `mlflow` to `requirements.txt`.
    *   Run `pip install -r requirements.txt`.

2.  **Connect to Azure ML Workspace:**
    *   Use `azure.ai.ml.MLClient` to connect using `config.json` (subscription\_id, resource\_group, account\_name).
    *   Ensure `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` (or other authentication methods) are set in `.env` for programmatic access.

3.  **Integrate MLflow Tracking in `run.py` and `batch_processor.py`:**
    *   **Import MLflow:** `import mlflow`
    *   **Start MLflow Run:** At the beginning of the main processing function (`run()` in `run.py`, `run_batch_processing()` in `batch_processor.py`), add:
        ```python
        with mlflow.start_run() as run:
            mlflow.log_param("max_articles_per_run", MAX_ARTICLES_PER_RUN)
            mlflow.log_param("openai_deployment", deployment_name)
            # For batch_processor.py:
            # mlflow.log_param("batch_total_articles", self.TOTAL_ARTICLES)
            # mlflow.log_param("batch_size", self.BATCH_SIZE)
            # mlflow.log_param("batch_delay", self.BATCH_DELAY)
            # mlflow.log_param("news_sources_mix", self.news_sources)
            # ... rest of your processing logic ...
        ```
    *   **Log Metrics:** After processing is complete (or after each batch in `batch_processor.py`), log the `stats` data:
        ```python
        # Example for run.py (after stats.log_summary()):
        mlflow.log_metric("articles_fetched", stats.get_metric('articles_fetched'))
        mlflow.log_metric("articles_processed", stats.get_metric('articles_processed'))
        mlflow.log_metric("rewrites_successful", stats.get_metric('rewrites_successful'))
        mlflow.log_metric("articles_skipped", stats.get_metric('articles_skipped'))
        mlflow.log_metric("rewrites_failed", stats.get_metric('rewrites_failed'))
        mlflow.log_metric("api_calls", stats.get_metric('api_calls'))
        mlflow.log_metric("api_errors", stats.get_metric('api_errors'))
        mlflow.log_metric("uploads_successful", stats.get_metric('uploads_successful'))
        mlflow.log_metric("uploads_failed", stats.get_metric('uploads_failed'))
        mlflow.log_metric("rewrite_success_rate", stats.get_metric('rewrite_success_rate'))
        mlflow.log_metric("total_duration_seconds", total_time)
        # Add average confidence if calculated
        ```
    *   **Set MLflow Tracking URI:** Ensure MLflow knows where to log. This is usually done via environment variables or `mlflow.set_tracking_uri()`. For Azure ML, it often auto-configures if you're authenticated.

4.  **Update `config.json` (Optional):** If you need to store more specific MLflow-related configurations, you can extend this file.

5.  **Update `.env.template`:** Add placeholders for Azure ML authentication (e.g., `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`).

---

## 🎯 Stretch Goals

- [ ] Add sentiment detection pre- and post-rewrite
- [ ] Store tone delta in metadata for each article
- [ ] Add timeline of headline rewrites (track media changes over time)
- [ ] NewsAPI alternative fallback (in case of rate limits)

---

## 📌 Version Roadmap

### 🔸 v1.2
- Clean pagination
- Content scraping (Guardian or BBC)
- More OpenAI rewrite polish

### 🔸 v1.3
- Azure search browser or CLI viewer
- Frontend beta

### 🔸 v1.4
- Chrome extension alpha
- Metadata enrichment (sentiment, source bias, tone score)

---

👑 *Crafted with intent by the Future King of Software Developers*
