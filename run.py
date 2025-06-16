import requests
from openai import AzureOpenAI
import uuid
import os
import time
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

# Configuration variables
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "20"))  # Default to 20 articles
ARTICLES_PER_PAGE = 100  # NewsAPI max per request
RATE_LIMIT_DELAY = 1  # Delay between API calls in seconds

# Validate required env variables
if not all([news_api_key, azure_openai_key, azure_openai_endpoint, azure_search_key, azure_search_endpoint]):
    raise EnvironmentError("One or more required environment variables are missing. Please check your .env file.")

# === STEP 1: NewsAPI with Pagination ===
def fetch_articles_with_pagination(max_articles):
    """Fetch articles from NewsAPI with pagination support"""
    all_articles = []
    page = 1
    
    while len(all_articles) < max_articles:
        # Calculate how many articles we need for this request
        articles_needed = min(ARTICLES_PER_PAGE, max_articles - len(all_articles))
        
        news_url = f"https://newsapi.org/v2/everything?q=UK&sortBy=publishedAt&language=en&pageSize={articles_needed}&page={page}&apiKey={news_api_key}"
        
        try:
            print(f"🔄 Fetching page {page} (up to {articles_needed} articles)...")
            response = requests.get(news_url)
            
            if response.status_code == 429:  # Rate limit exceeded
                print("⚠️ Rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                continue
            elif response.status_code != 200:
                print(f"❌ API Error {response.status_code}: {response.text}")
                break
                
            data = response.json()
            articles = data.get("articles", [])
            
            if not articles:  # No more articles available
                print("📄 No more articles available from NewsAPI")
                break
                
            all_articles.extend(articles)
            print(f"✅ Fetched {len(articles)} articles from page {page}")
            
            # Check if we've reached the total available articles
            total_results = data.get("totalResults", 0)
            if len(all_articles) >= total_results:
                print(f"📚 Reached all available articles ({total_results} total)")
                break
                
            page += 1
            
            # Rate limiting - be respectful to the API
            if page > 1:  # Don't delay on first request
                time.sleep(RATE_LIMIT_DELAY)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching articles: {e}")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break
    
    return all_articles[:max_articles]  # Ensure we don't exceed the limit

print(f"🚀 Starting NewsAPI fetch (max {MAX_ARTICLES_PER_RUN} articles)...")
articles = fetch_articles_with_pagination(MAX_ARTICLES_PER_RUN)
print(f"✅ Successfully fetched {len(articles)} articles from NewsAPI.")

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
processed_count = 0
failed_count = 0

print(f"\n🧠 Starting headline rewriting for {len(articles)} articles...")

for i, article in enumerate(articles, 1):
    title = article.get("title", "")
    if not title or title == "[Removed]":  # Skip articles with no title or removed content
        continue

    print(f"\n[{i}/{len(articles)}] Processing: {title[:80]}{'...' if len(title) > 80 else ''}")
    
    prompt = f"Rewrite this headline in a calm, more positive tone:\n\n{title}"

    try:
        result = client.completions.create(
            model=deployment_name,
            prompt=prompt,
            max_tokens=60
        )
        rewritten = result.choices[0].text.strip()
        
        # Remove any leading quotes or formatting from the AI response
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        
        print(f"📰 Original:  {title}")
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
        processed_count += 1

    except Exception as e:
        print(f"❌ Error with headline: {title[:50]}... - {e}")
        failed_count += 1
        
    # Small delay to avoid overwhelming the API
    if i % 5 == 0:  # Every 5 articles
        time.sleep(1)

print(f"\n📊 Processing Summary:")
print(f"   ✅ Successfully processed: {processed_count}")
print(f"   ❌ Failed: {failed_count}")
print(f"   📝 Total documents ready for upload: {len(docs)}")

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
