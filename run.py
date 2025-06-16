import requests
from openai import AzureOpenAI
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load keys and endpoints from environment variables
news_api_key = os.getenv("NEWS_API_KEY")
azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo-instruct")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX", "news-perspective-index")

# Validate required env variables
if not all([news_api_key, azure_openai_key, azure_openai_endpoint, azure_search_key, azure_search_endpoint]):
    raise EnvironmentError("One or more required environment variables are missing. Please check your .env file.")

# === STEP 1: NewsAPI ===
news_url = f"https://newsapi.org/v2/everything?q=UK&sortBy=publishedAt&language=en&apiKey={news_api_key}"
articles = requests.get(news_url).json().get("articles", [])
print(f"✅ Fetched {len(articles)} articles from NewsAPI.")

# === STEP 2: Azure OpenAI Setup ===
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=azure_openai_endpoint,
    api_key=azure_openai_key
)

# === STEP 3: Azure Search Setup ===
search_url = f"{azure_search_endpoint}/indexes/{azure_search_index}/docs/index?api-version=2023-11-01"
headers_search = {
    "Content-Type": "application/json",
    "api-key": azure_search_key
}

# === STEP 4: Rewrite + Upload ===
docs = []

for article in articles[:5]:  # test with 5
    title = article.get("title", "")
    if not title:
        continue

    prompt = f"Rewrite this headline in a calm, more positive tone:\n\n{title}"

    try:
        result = client.completions.create(
            model=deployment_name,
            prompt=prompt,
            max_tokens=60
        )
        rewritten = result.choices[0].text.strip()
        print(f"\n📰 Original: {title}")
        print(f"✨ Rewritten: {rewritten}")

        doc = {
            "@search.action": "upload",
            "id": str(uuid.uuid4()),
            "original_title": title,
            "rewritten_title": rewritten,
            "original_content": article.get("content", ""),
            "source": article.get("source", {}).get("name", ""),
            "published_date": article.get("publishedAt", "")
        }
        docs.append(doc)

    except Exception as e:
        print(f"❌ Error with headline: {title}\n{e}")

# === STEP 5: Upload to Azure Search ===
if docs:
    response = requests.post(
        search_url,
        headers=headers_search,
        json={"value": docs}
    )
    print("\n🚀 Upload complete. Azure Search response:", response.status_code, response.text)
else:
    print("⚠️ No documents to upload.")