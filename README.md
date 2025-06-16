# News Perspective AI

**News Perspective AI** is a Python-based tool that:
- Fetches the latest news headlines from [NewsAPI.org](https://newsapi.org/)
- Rewrites them in a more **positive**, **neutral**, or **factual** tone using [Azure OpenAI](https://azure.microsoft.com/en-us/services/cognitive-services/openai-service/)
- Uploads both the original and rewritten headlines to an Azure AI Search Index for fast semantic retrieval

This was created to help reduce doomscrolling, emotional bias, and misinformation caused by alarmist media.

---

## ⚙️ How It Works

1. **Fetch News** from NewsAPI
2. **Rewrite** headlines using an Azure OpenAI model (gpt-35-turbo)
3. **Upload** the results to an Azure AI Search Index

---

## 🚀 Quickstart

> ⚠️ This assumes you already have Azure OpenAI and Azure AI Search set up

1. Clone the repo
2. Create a `.env` file with the settings described below
3. Install the required Python packages
4. Run the script!

### Environment Variables

Create a `.env` file with:

```
NEWS_API_KEY=your_newsapi_key
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://<your-region>.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo-instruct
AZURE_SEARCH_KEY=your_azure_search_key
AZURE_SEARCH_ENDPOINT=https://<your-search-name>.search.windows.net
AZURE_SEARCH_INDEX=news-perspective-index
```

> **DO NOT COMMIT KEYS TO GIT.** Use environment variables or secure key management tools like Azure Key Vault.

---

## 🧠 Tech Stack
- Python 3.9+
- Azure OpenAI (gpt-35-turbo)
- Azure AI Search
- NewsAPI.org

---

## 💡 Ideas for Expansion
- Web UI (Streamlit, Flask, or Next.js)
- Schedule daily rewrites via GitHub Actions or Azure Functions
- Add sentiment analysis and topic clustering
- Build a Chrome extension that rewrites headlines live

---

🤘 *Built by Thomas Butler with a relentless need to make the web suck less.*