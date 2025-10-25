# NewsPerspective

AI-powered news processing pipeline that transforms sensational headlines into balanced, factual reporting using Azure AI services.

## Overview

NewsPerspective is a production-ready system that:
- Fetches news from multiple sources (NewsAPI + RSS feeds)
- Detects clickbait and sensational language
- Rewrites negative headlines in a calmer, factual tone
- Provides analytics on source reliability
- Offers searchable archive via web interface
- Tracks performance with MLflow integration

Built to combat doomscrolling and provide a more balanced perspective on news.

## Key Features

### Core Processing
- **Multi-Source Fetching**: NewsAPI + RSS feeds (BBC, CNN, Reuters, Guardian, TechCrunch)
- **Clickbait Detection**: Pattern-based scoring with source reliability tracking
- **AI Headline Rewriting**: Azure OpenAI transforms negative headlines
- **Sentiment Analysis**: Azure AI Language for tone detection
- **Semantic Search**: Azure AI Search for intelligent article retrieval

### Analytics & Monitoring
- **Source Reliability Dashboard**: Track clickbait scores per news source
- **Performance Metrics**: Monitor processing volume, success rates, API usage
- **MLflow Integration**: Experiment tracking with Azure AI Foundry
- **Interactive Visualisations**: Plotly charts for trend analysis

### Deployment & Security
- **Azure Functions**: Serverless scheduled execution
- **GitHub Actions CI/CD**: Automated testing and deployment
- **Azure Key Vault**: Secure secret management
- **Multi-Environment Support**: Local, Docker, Azure deployment options

## Quick Start

### Prerequisites
- Python 3.10 or 3.11
- Azure subscription (OpenAI, Search, AI Language services)
- NewsAPI key (optional - can use RSS-only mode)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/NewsPerspective.git
cd NewsPerspective

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your Azure credentials
```

### Basic Usage

```bash
# Single run (20 articles)
python run.py

# Batch processing (500 articles)
python batch_processor.py

# Launch web interface
streamlit run web_app.py

# Launch analytics dashboard
streamlit run analytics_dashboard.py

# Search articles
python search.py --keyword "technology" --recent 24
```

## Configuration

### Article Source Modes

Set `ARTICLE_SOURCE_MODE` in `.env`:

- **`newsapi`**: Use NewsAPI only (requires `NEWS_API_KEY`)
- **`rss`**: Use RSS feeds only (no API key needed)
- **`mixed`**: Combine both sources (recommended)

### Optional Features

```bash
# Enable MLflow tracking
MLFLOW_ENABLED=true
MLFLOW_TRACKING_URI=https://your-workspace.azure.com

# Enable Azure Key Vault
KEYVAULT_ENABLED=true
KEYVAULT_URL=https://your-keyvault.vault.azure.net/
```

## Deployment

### Azure Functions (Serverless)

Automated daily runs with zero maintenance:

```bash
# Deploy using Azure CLI
func azure functionapp publish news-perspective-func

# Or push to GitHub for automatic deployment via GitHub Actions
git push origin main
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

### Streamlit Cloud

Deploy dashboards with one click:
1. Push to GitHub
2. Connect at https://share.streamlit.io
3. Add secrets from `.env`

### Docker

```bash
docker build -t news-perspective .
docker run -d --env-file .env news-perspective
```

## Architecture

```
┌─────────────────┐
│  News Sources   │
│  - NewsAPI      │
│  - RSS Feeds    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Batch Processor │
│  - Fetch         │
│  - Validate      │
│  - Deduplicate   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  AI Analysis    │────▶│ Azure OpenAI │
│  - Sentiment    │     │ - Rewriting  │
│  - Clickbait    │     └──────────────┘
│  - Entities     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Azure Search   │
│  - Indexing     │
│  - Semantic     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Interfaces    │
│  - Web App      │
│  - Analytics    │
│  - CLI Search   │
└─────────────────┘
```

## Project Structure

```
NewsPerspective/
├── Core Processing
│   ├── run.py                          # Single-run processor
│   ├── batch_processor.py              # Large-scale batch processor
│   ├── azure_ai_language.py            # Sentiment analysis
│   ├── azure_document_intelligence.py  # Content extraction
│   ├── clickbait_detector.py           # Clickbait scoring
│   └── search.py                       # CLI search tool
│
├── Data Sources
│   └── scrapers/
│       ├── base_scraper.py             # Abstract scraper class
│       ├── rss_scraper.py              # RSS feed parser
│       ├── html_scraper.py             # HTML fallback scraper
│       ├── scraper_manager.py          # Multi-source orchestration
│       ├── content_validator.py        # Deduplication & validation
│       └── sources/
│           ├── bbc_scraper.py
│           ├── cnn_scraper.py
│           ├── reuters_scraper.py
│           ├── guardian_scraper.py
│           └── techcrunch_scraper.py
│
├── Monitoring & Analytics
│   ├── mlflow_tracker.py               # Experiment tracking
│   ├── analytics_dashboard.py          # Performance metrics
│   └── logger_config.py                # Logging utilities
│
├── Security
│   └── azure_key_vault.py              # Secret management
│
├── Web Interfaces
│   ├── web_app.py                      # News browser
│   └── analytics_dashboard.py          # Analytics dashboard
│
├── Deployment
│   ├── function_app.py                 # Azure Functions
│   ├── host.json                       # Function app config
│   ├── .github/workflows/
│   │   ├── azure-functions-deploy.yml  # CD pipeline
│   │   └── ci.yml                      # CI pipeline
│   └── .funcignore                     # Deployment exclusions
│
└── Documentation
    ├── README.md                        # This file
    ├── DEPLOYMENT.md                    # Deployment guide
    ├── SECURITY.md                      # Security best practices
    ├── DASHBOARDS.md                    # Dashboard usage
    └── LEARNING_GUIDE.md                # System explanation
```

## Tech Stack

**Azure Services:**
- Azure OpenAI (gpt-35-turbo-instruct)
- Azure AI Language (sentiment analysis, entity recognition)
- Azure AI Document Intelligence (content extraction)
- Azure AI Search (semantic indexing)
- Azure Functions (serverless compute)
- Azure Key Vault (secret management)
- Azure AI Foundry (MLflow tracking)

**Python Libraries:**
- Streamlit (web interfaces)
- Plotly (visualisations)
- feedparser (RSS parsing)
- BeautifulSoup (HTML scraping)
- requests (HTTP client)
- MLflow (experiment tracking)

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Complete deployment guide for Azure Functions, Streamlit Cloud, Docker
- **[SECURITY.md](SECURITY.md)**: Azure Key Vault setup, secret rotation, incident response
- **[DASHBOARDS.md](DASHBOARDS.md)**: Web app and analytics dashboard usage
- **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)**: Simple explanation of how everything works

## Performance

Typical batch processing (500 articles):
- **Fetch Time**: 2-3 minutes
- **Processing Time**: 8-12 minutes
- **API Calls**: ~2,500
- **Azure Cost**: £0.50-£1.00 per run
- **Success Rate**: 98%+

## Monitoring

### Web Dashboards

```bash
# News browser (port 8501)
streamlit run web_app.py

# Analytics dashboard (port 8502)
streamlit run analytics_dashboard.py --server.port 8502
```

### MLflow Tracking

Enable in `.env`:

```bash
MLFLOW_ENABLED=true
MLFLOW_EXPERIMENT_NAME=NewsPerspective
```

View experiments at configured tracking URI or local mlruns/ directory.

### Source Reliability

Clickbait scores tracked per source in `data/source_reliability.json`:
- Average clickbait score (0-100)
- Detection rate percentage
- Total articles analysed
- Reliability rating

## Development

### Running Tests

```bash
# Test RSS scrapers
python test_rss_scrapers.py

# Test Azure Search connection
python search.py --test
```

### Code Quality

GitHub Actions CI runs on every PR:
- Black formatter check
- Flake8 linting
- Pytest test suite
- Coverage reporting

### Adding New Sources

1. Create scraper in `scrapers/sources/your_source.py`
2. Inherit from `RSSFeedScraper` or `HTMLScraper`
3. Add to `scraper_manager.py`

Example:

```python
from scrapers.rss_scraper import RSSFeedScraper

class YourSourceScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            source_name="Your Source",
            rss_url="https://yoursource.com/feed",
            rate_limit_delay=2
        )
```

## Troubleshooting

**Import errors:**
```bash
pip install -r requirements.txt
```

**Azure connection failures:**
- Verify credentials in `.env`
- Check network connectivity
- Validate service endpoint URLs

**No articles fetched:**
- Check NewsAPI key validity and rate limits
- Verify RSS feed URLs are accessible
- Review logs in `logs/` directory

**Clickbait detector not working:**
- Ensure `data/` directory exists
- Check file permissions
- Review `data/source_reliability.json`

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

CI will run tests automatically.

## Roadmap

- [x] Production HTTP timeouts and error handling
- [x] Clickbait detection system
- [x] RSS scraping framework (5 sources)
- [x] MLflow experiment tracking
- [x] Azure Functions deployment
- [x] Analytics dashboard
- [x] Azure Key Vault integration
- [ ] Chrome extension for in-browser headline replacement
- [ ] FastAPI service for third-party integration
- [ ] Mobile PWA version
- [ ] Email digest subscription
- [ ] Multi-language support with Azure Translator

## License

This project is for educational and personal use.

## Acknowledgements

- Azure AI services for powerful NLP capabilities
- NewsAPI for comprehensive news aggregation
- Streamlit for rapid dashboard development
- feedparser for robust RSS parsing

---

Built with precision and care by Tom Butler
