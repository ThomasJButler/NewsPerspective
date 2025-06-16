import requests
from openai import AzureOpenAI
import uuid
import os
import time
from dotenv import load_dotenv
from logger_config import setup_logger, StatsTracker, log_performance, log_error_details
from azure_ai_language import ai_language
from azure_document_intelligence import document_intelligence

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = setup_logger("NewsPerspective.Main")
stats = StatsTracker(logger)

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
    logger.critical("Missing required environment variables")
    raise EnvironmentError("One or more required environment variables are missing. Please check your .env file.")

logger.info("NewsPerspective Application Started")
logger.info(f"Configuration: MAX_ARTICLES={MAX_ARTICLES_PER_RUN}, DEPLOYMENT={deployment_name}")

# === STEP 1: NewsAPI with Pagination ===
@log_performance(logger)
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
            logger.info(f"Fetching NewsAPI page {page}, requesting {articles_needed} articles")
            stats.increment('api_calls')
            
            response = requests.get(news_url)
            
            if response.status_code == 429:  # Rate limit exceeded
                print("⚠️ Rate limit hit. Waiting 60 seconds...")
                logger.warning("NewsAPI rate limit hit, waiting 60 seconds")
                stats.increment('api_errors')
                time.sleep(60)
                continue
            elif response.status_code != 200:
                print(f"❌ API Error {response.status_code}: {response.text}")
                logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
                stats.increment('api_errors')
                break
                
            data = response.json()
            articles = data.get("articles", [])
            
            if not articles:  # No more articles available
                print("📄 No more articles available from NewsAPI")
                break
                
            all_articles.extend(articles)
            print(f"✅ Fetched {len(articles)} articles from page {page}")
            logger.info(f"Successfully fetched {len(articles)} articles from page {page}")
            stats.increment('articles_fetched', len(articles))
            
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
            log_error_details(logger, e, f"Network error on page {page}")
            stats.increment('api_errors')
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            log_error_details(logger, e, f"Unexpected error on page {page}")
            stats.increment('api_errors')
            break
    
    return all_articles[:max_articles]  # Ensure we don't exceed the limit

print(f"🚀 Starting NewsAPI fetch (max {MAX_ARTICLES_PER_RUN} articles)...")
try:
    articles = fetch_articles_with_pagination(MAX_ARTICLES_PER_RUN)
    print(f"✅ Successfully fetched {len(articles)} articles from NewsAPI.")
    logger.info(f"Fetch complete: {len(articles)} articles retrieved")
except Exception as e:
    logger.critical("Failed to fetch articles from NewsAPI")
    log_error_details(logger, e, "Article fetching failed")
    stats.log_summary()
    raise

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
        logger.debug(f"Skipping article {i} - no title or removed content")
        continue

    print(f"\n[{i}/{len(articles)}] Processing: {title[:80]}{'...' if len(title) > 80 else ''}")
    logger.info(f"Processing article {i}/{len(articles)}: {title[:50]}...")
    stats.increment('articles_processed')
    
    # Step 1: Enhanced analysis using Azure AI Language (if available)
    try:
        # Get enhanced analysis from Azure AI Language
        logger.debug("Requesting enhanced AI analysis for headline")
        stats.increment('api_calls')
        
        ai_analysis = ai_language.analyze_text(title)
        problematic_phrases = ai_language.extract_problematic_phrases(title)
        
        # Extract sentiment information
        sentiment = ai_analysis.get('sentiment', 'neutral')
        confidence_scores = ai_analysis.get('confidence_scores', {})
        enhanced_reason = ai_analysis.get('enhanced_reason', '')
        entities = ai_analysis.get('entities', [])
        key_phrases = ai_analysis.get('key_phrases', [])
        
        # Determine if rewrite is needed based on enhanced analysis
        negative_confidence = confidence_scores.get('negative', 0)
        positive_confidence = confidence_scores.get('positive', 0)
        
        needs_rewrite = False
        confidence = 50
        current_tone = "NEUTRAL"
        
        if sentiment == 'negative' and negative_confidence > 60:
            needs_rewrite = True
            confidence = int(negative_confidence)
            current_tone = "NEGATIVE"
        elif sentiment == 'positive' and positive_confidence > 80:
            needs_rewrite = False
            confidence = int(positive_confidence)
            current_tone = "POSITIVE"
        elif problematic_phrases:  # Has problematic phrases even if neutral sentiment
            needs_rewrite = True
            confidence = 75
            current_tone = "NEGATIVE/SENSATIONAL"
        else:
            # Fallback to neutral
            confidence = max(confidence_scores.values()) if confidence_scores else 50
            current_tone = sentiment.upper()
            needs_rewrite = negative_confidence > positive_confidence and negative_confidence > 40
        
        # Build enhanced reason with specific examples
        reason_parts = []
        if enhanced_reason:
            reason_parts.append(enhanced_reason)
        
        if problematic_phrases:
            phrase_examples = [f"'{p['phrase']}'" for p in problematic_phrases[:2]]
            reason_parts.append(f"Contains negative language: {', '.join(phrase_examples)}")
        
        if entities:
            high_conf_entities = [e['text'] for e in entities if e['confidence'] > 80]
            if high_conf_entities:
                reason_parts.append(f"Key entities: {', '.join(high_conf_entities[:3])}")
        
        reason = '. '.join(reason_parts) if reason_parts else "Standard tone analysis"
        
        print(f"🔍 Enhanced Analysis: {current_tone} tone, Confidence: {confidence}%")
        print(f"📊 Sentiment Scores: Pos:{positive_confidence:.0f}% Neu:{confidence_scores.get('neutral', 0):.0f}% Neg:{negative_confidence:.0f}%")
        if problematic_phrases:
            phrases_text = ', '.join([p['phrase'] for p in problematic_phrases])
            print(f"⚠️  Problematic phrases: {phrases_text}")
        
        logger.info(f"Enhanced headline analysis: tone={current_tone}, confidence={confidence}%, needs_rewrite={needs_rewrite}")
        
        # Step 1.5: Enhanced content analysis using Document Intelligence (if URL available)
        content_extraction = None
        article_url = article.get("url", "")
        
        if article_url and needs_rewrite:
            try:
                print(f"📄 Analyzing article content from URL...")
                logger.debug(f"Starting Document Intelligence analysis for: {article_url}")
                
                content_extraction = document_intelligence.extract_content_from_url(article_url)
                
                if content_extraction.get('content_extracted'):
                    print(f"📋 Content Analysis: {content_extraction['content_summary']}")
                    
                    # Extract key quotes that justify the rewrite
                    key_quotes = content_extraction.get('key_quotes', [])
                    if key_quotes:
                        print(f"💬 Found problematic content: {len(key_quotes)} concerning phrases")
                        for quote in key_quotes[:2]:  # Show first 2
                            print(f"   → \"{quote['quote'][:80]}...\" (trigger: {quote['trigger_word']})")
                    
                    # Enhance the reasoning with content analysis
                    enhanced_content_reason = document_intelligence.enhance_rewrite_reasoning(title, content_extraction)
                    if enhanced_content_reason:
                        reason = f"{reason}. {enhanced_content_reason}"
                        
                    logger.info(f"Document Intelligence analysis completed: {content_extraction['content_summary']}")
                else:
                    print(f"⚠️  Content extraction unavailable for this URL")
                    logger.debug("Document Intelligence extraction failed or disabled")
                    
            except Exception as e:
                print(f"⚠️  Content analysis error: {str(e)}")
                logger.warning(f"Document Intelligence analysis failed: {str(e)}")
                content_extraction = None
        
        # Step 2: Only rewrite if needed and confidence is reasonable
        if needs_rewrite and confidence >= 60:
            # Choose rewrite style based on current tone
            if "SENSATIONAL" in current_tone or "NEGATIVE" in current_tone:
                style = "calm, factual"
            else:
                style = "slightly more positive"
                
            rewrite_prompt = f"""Rewrite this headline in a {style} tone while preserving all factual information:

Original: "{title}"

Requirements:
- Keep all facts accurate
- Maintain the core message
- Use {style} language
- Return ONLY the rewritten headline"""

            logger.debug(f"Requesting rewrite with {style} style")
            stats.increment('api_calls')
            
            result = client.completions.create(
                model=deployment_name,
                prompt=rewrite_prompt,
                max_tokens=80
            )
            rewritten = result.choices[0].text.strip()
            
            # Clean up the response
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            if rewritten.startswith('Rewritten:') or rewritten.startswith('New:'):
                rewritten = rewritten.split(':', 1)[1].strip()
            
            print(f"📰 Original:  {title}")
            print(f"✨ Rewritten: {rewritten}")
            
            logger.info(f"Headline rewritten successfully")
            stats.increment('rewrites_successful')
            
            doc = {
                "@search.action": "upload",
                "id": str(uuid.uuid4()),
                "original_title": title,
                "rewritten_title": rewritten,
                "original_content": article.get("content", ""),
                "source": article.get("source", {}).get("name", ""),
                "published_date": article.get("publishedAt", ""),
                "article_url": article.get("url", ""),
                "was_rewritten": True,
                "original_tone": current_tone,
                "confidence_score": int(confidence), # Convert to integer
                "rewrite_reason": reason
            }
        else:
            print(f"📰 Original:  {title}")
            print(f"⏭️  Skipped: {reason} (Confidence: {confidence}%)")
            
            logger.info(f"Skipping rewrite: {reason}")
            stats.increment('articles_skipped')
            
            doc = {
                "@search.action": "upload",
                "id": str(uuid.uuid4()),
                "original_title": title,
                "rewritten_title": title,  # Keep original
                "original_content": article.get("content", ""),
                "source": article.get("source", {}).get("name", ""),
                "published_date": article.get("publishedAt", ""),
                "article_url": article.get("url", ""),
                "was_rewritten": False,
                "original_tone": current_tone,
                "confidence_score": int(confidence), # Convert to integer
                "rewrite_reason": reason
            }
        
        docs.append(doc)
        processed_count += 1

    except Exception as e:
        print(f"❌ Error with headline: {title[:50]}... - {e}")
        log_error_details(logger, e, f"Error processing headline: {title[:50]}...")
        stats.increment('rewrites_failed')
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
    try:
        logger.info(f"Uploading {len(docs)} documents to Azure Search")
        stats.increment('api_calls')
        
        response = requests.post(
            search_url,
            headers=headers_search,
            json={"value": docs}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"\n🚀 Upload complete. Azure Search response: {response.status_code}")
            logger.info(f"Successfully uploaded {len(docs)} documents to Azure Search")
            stats.increment('uploads_successful', len(docs))
        else:
            print(f"\n❌ Upload failed. Azure Search response: {response.status_code} - {response.text}")
            logger.error(f"Failed to upload documents: {response.status_code} - {response.text}")
            stats.increment('uploads_failed', len(docs))
            
    except Exception as e:
        print(f"\n❌ Upload error: {e}")
        log_error_details(logger, e, "Azure Search upload failed")
        stats.increment('uploads_failed', len(docs))
else:
    print("⚠️ No documents to upload.")
    logger.warning("No documents to upload - all processing may have failed")

# Log final statistics
stats.log_summary()
logger.info("NewsPerspective Application Completed")
