"""
@author Tom Butler
@date 2025-10-24
@description Batch processor for handling large volumes of news articles.
             Fetches headlines from NewsAPI, rewrites negative headlines using Azure OpenAI,
             and uploads results to Azure AI Search with sentiment analysis.
"""

import requests
from openai import AzureOpenAI
import uuid
import os
import time
from dotenv import load_dotenv
from logger_config import setup_logger, StatsTracker, log_performance, log_error_details
from azure_ai_language import ai_language
from azure_document_intelligence import document_intelligence
from clickbait_detector import clickbait_detector
from scrapers.scraper_manager import scraper_manager
from scrapers.content_validator import content_validator
from mlflow_tracker import mlflow_tracker
from datetime import datetime

load_dotenv()

# Setup logging
logger = setup_logger("NewsPerspective.BatchProcessor")

class BatchProcessor:
    """
    Batch processor for news headline rewriting and indexing.
    Orchestrates fetching, analysis, rewriting, and upload of news articles.
    """

    def __init__(self):
        """Initialise batch processor with configuration and Azure clients."""
        self.stats = StatsTracker(logger)
        self.setup_clients()

        self.TOTAL_ARTICLES = int(os.getenv("BATCH_TOTAL_ARTICLES", "500"))
        self.BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
        self.BATCH_DELAY = int(os.getenv("BATCH_DELAY", "10"))
        self.RATE_LIMIT_DELAY = 1

        # Article source mode: 'newsapi', 'rss', or 'mixed'
        self.SOURCE_MODE = os.getenv("ARTICLE_SOURCE_MODE", "mixed").lower()

        # News sources configuration (NewsAPI)
        self.news_sources = {
            "general": {
                "query": "UK",
                "domains": "bbc.co.uk,theguardian.com,independent.co.uk,telegraph.co.uk",
                "weight": 0.5  # 50% of articles
            },
            "sports": {
                "query": "sports OR football OR rugby OR cricket OR tennis OR golf",
                "domains": "skysports.com,bbc.co.uk/sport,espn.co.uk,theguardian.com/sport",
                "weight": 0.5  # 50% of articles
            }
        }

        logger.info(f"Batch Processor initialised: {self.TOTAL_ARTICLES} articles in {self.BATCH_SIZE}-article batches")
        logger.info(f"Article source mode: {self.SOURCE_MODE}")

    def setup_clients(self):
        """Initialise Azure clients and validate credentials."""
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo-instruct")
        self.azure_search_key = os.getenv("AZURE_SEARCH_KEY")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.azure_search_index = os.getenv("AZURE_SEARCH_INDEX", "news-perspective-index")

        if not all([self.news_api_key, self.azure_openai_key, self.azure_openai_endpoint,
                   self.azure_search_key, self.azure_search_endpoint]):
            raise EnvironmentError("Missing required environment variables. Please check your .env file.")

        self.openai_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=self.azure_openai_endpoint,
            api_key=self.azure_openai_key
        )

        self.search_url = f"{self.azure_search_endpoint}/indexes/{self.azure_search_index}/docs/index?api-version=2023-11-01"
        self.search_headers = {
            "Content-Type": "application/json",
            "api-key": self.azure_search_key
        }

        logger.info("Azure clients initialised successfully")

    def fetch_articles_mixed_sources(self, total_articles):
        """
        Fetch articles from multiple sources (general + sports).
        @param {int} total_articles - Target number of articles to fetch
        @return {list} List of fetched article objects
        """
        all_articles = []

        general_count = int(total_articles * self.news_sources["general"]["weight"])
        sports_count = total_articles - general_count

        print(f"Article Mix: {general_count} general news + {sports_count} sports news")
        logger.info(f"Fetching mixed articles: {general_count} general, {sports_count} sports")

        if general_count > 0:
            print(f"Fetching {general_count} general news articles...")
            general_articles = self.fetch_articles_by_source("general", general_count)
            all_articles.extend(general_articles)
            print(f"Fetched {len(general_articles)} general articles")

        if sports_count > 0:
            print(f"Fetching {sports_count} sports news articles...")
            sports_articles = self.fetch_articles_by_source("sports", sports_count)
            all_articles.extend(sports_articles)
            print(f"Fetched {len(sports_articles)} sports articles")
        
        # Shuffle to mix sources
        import random
        random.shuffle(all_articles)
        
        return all_articles[:total_articles]

    def fetch_articles_by_source(self, source_type, count):
        """
        Fetch articles from a specific news source.
        @param {str} source_type - Type of source (general, sports, etc.)
        @param {int} count - Number of articles to fetch
        @return {list} List of article objects
        """
        source_config = self.news_sources[source_type]
        articles = []
        page = 1
        articles_per_page = min(100, count)

        while len(articles) < count:
            try:
                remaining = count - len(articles)
                page_size = min(articles_per_page, remaining)

                url = (f"https://newsapi.org/v2/everything"
                       f"?q={source_config['query']}"
                       f"&domains={source_config['domains']}"
                       f"&sortBy=publishedAt"
                       f"&language=en"
                       f"&pageSize={page_size}"
                       f"&page={page}"
                       f"&apiKey={self.news_api_key}")

                logger.debug(f"Fetching {source_type} articles: page {page}, size {page_size}")
                self.stats.increment('api_calls')

                try:
                    response = requests.get(url, timeout=30)
                except requests.exceptions.Timeout:
                    print(f"Timeout fetching {source_type} articles. Retrying...")
                    logger.warning(f"Timeout on {source_type} page {page}")
                    self.stats.increment('api_errors')
                    time.sleep(5)
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Network error fetching {source_type}: {str(e)}")
                    logger.error(f"RequestException on {source_type} page {page}: {str(e)}")
                    self.stats.increment('api_errors')
                    break

                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    try:
                        wait_seconds = int(retry_after)
                    except ValueError:
                        from email.utils import parsedate_to_datetime
                        try:
                            retry_date = parsedate_to_datetime(retry_after)
                            wait_seconds = max(0, (retry_date - datetime.now()).total_seconds())
                        except:
                            wait_seconds = 60
                    wait_seconds = min(wait_seconds, 300)
                    print(f"Rate limit hit for {source_type}. Waiting {wait_seconds} seconds...")
                    logger.warning(f"Rate limit (429) for {source_type}, waiting {wait_seconds}s")
                    self.stats.increment('api_errors')
                    time.sleep(wait_seconds)
                    continue
                elif response.status_code != 200:
                    logger.error(f"NewsAPI error for {source_type}: {response.status_code}")
                    self.stats.increment('api_errors')
                    break

                data = response.json()
                page_articles = data.get("articles", [])

                if not page_articles:
                    print(f"No more {source_type} articles available")
                    break

                valid_articles = [a for a in page_articles
                                if a.get("title") and a.get("title") != "[Removed]"]

                articles.extend(valid_articles)
                self.stats.increment('articles_fetched', len(valid_articles))

                page += 1
                time.sleep(self.RATE_LIMIT_DELAY)

            except Exception as e:
                logger.error(f"Error fetching {source_type} articles: {str(e)}")
                self.stats.increment('api_errors')
                break

        return articles[:count]

    def fetch_articles_from_rss(self, total_articles):
        """
        Fetch articles from RSS feeds using scraper manager.
        @param {int} total_articles - Target number of articles to fetch
        @return {list} List of validated article objects
        """
        print(f"Fetching articles from RSS feeds...")
        logger.info(f"Fetching {total_articles} articles from RSS sources")

        # Calculate articles per source
        available_sources = scraper_manager.get_available_sources()
        source_count = len(available_sources)
        articles_per_source = (total_articles // source_count) + 5  # Slight excess for deduplication

        print(f"Fetching from {source_count} RSS sources: {', '.join(available_sources.values())}")

        # Fetch from all sources
        all_articles = scraper_manager.get_all_articles_flat(max_articles_per_source=articles_per_source)

        print(f"Fetched {len(all_articles)} total articles from RSS feeds")
        logger.info(f"Fetched {len(all_articles)} articles before validation")

        # Validate and deduplicate
        content_validator.reset()
        validated_articles = content_validator.validate_articles(
            all_articles,
            max_age_days=7,
            title_similarity_threshold=0.85
        )

        print(f"Validated {len(validated_articles)} unique articles")
        logger.info(f"Validated {len(validated_articles)} articles after deduplication")

        self.stats.increment('articles_fetched', len(validated_articles))

        return validated_articles[:total_articles]

    def fetch_articles_mixed_mode(self, total_articles):
        """
        Fetch articles from both NewsAPI and RSS sources.
        @param {int} total_articles - Target number of articles to fetch
        @return {list} List of article objects from mixed sources
        """
        newsapi_count = total_articles // 2
        rss_count = total_articles - newsapi_count

        print(f"Mixed mode: {newsapi_count} from NewsAPI + {rss_count} from RSS")
        logger.info(f"Mixed source mode: {newsapi_count} NewsAPI, {rss_count} RSS")

        all_articles = []

        # Fetch from NewsAPI
        if newsapi_count > 0:
            newsapi_articles = self.fetch_articles_mixed_sources(newsapi_count)
            all_articles.extend(newsapi_articles)
            print(f"Fetched {len(newsapi_articles)} articles from NewsAPI")

        # Fetch from RSS
        if rss_count > 0:
            rss_articles = self.fetch_articles_from_rss(rss_count)
            all_articles.extend(rss_articles)
            print(f"Fetched {len(rss_articles)} articles from RSS")

        # Shuffle to mix sources
        import random
        random.shuffle(all_articles)

        return all_articles[:total_articles]

    def process_article(self, article, article_num, total_articles):
        """
        Process a single article for headline analysis and rewriting.
        @param {dict} article - Article object from NewsAPI or RSS feed
        @param {int} article_num - Current article number in batch
        @param {int} total_articles - Total articles in processing run
        @return {dict} Document ready for Azure Search upload or None if skipped
        """
        title = article.get("title", "")
        if not title or title == "[Removed]":
            return None

        print(f"[{article_num}/{total_articles}] {title[:60]}{'...' if len(title) > 60 else ''}")
        logger.info(f"Processing article {article_num}: {title[:50]}...")

        try:
            self.stats.increment('api_calls')
            ai_analysis = ai_language.analyze_text(title)
            problematic_phrases = ai_language.extract_problematic_phrases(title)

            sentiment = ai_analysis.get('sentiment', 'neutral')
            confidence_scores = ai_analysis.get('confidence_scores', {})
            enhanced_reason = ai_analysis.get('enhanced_reason', '')

            # Clickbait detection
            article_url = article.get("url", "")

            # Handle both NewsAPI format (source is dict) and RSS format (source is string)
            source_data = article.get("source", "Unknown")
            if isinstance(source_data, dict):
                source = source_data.get("name", "Unknown")
            else:
                source = source_data
            clickbait_analysis = clickbait_detector.detect_clickbait_score(
                title,
                article_content=None,
                article_url=article_url
            )

            clickbait_score = clickbait_analysis.get('clickbait_score', 0)
            is_clickbait = clickbait_analysis.get('is_clickbait', False)
            clickbait_reasons = clickbait_analysis.get('reasons', [])

            # Track source reliability
            clickbait_detector.track_source_reliability(source, clickbait_score, is_clickbait)

            print(f"   Clickbait score: {clickbait_score}/100 {'(CLICKBAIT DETECTED)' if is_clickbait else ''}")
            logger.info(f"Clickbait score: {clickbait_score}, is_clickbait: {is_clickbait}")

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
            elif problematic_phrases:
                needs_rewrite = True
                confidence = 75
                current_tone = "NEGATIVE/SENSATIONAL"
            else:
                confidence = max(confidence_scores.values()) if confidence_scores else 50
                current_tone = sentiment.upper()
                needs_rewrite = negative_confidence > positive_confidence and negative_confidence > 40
            
            # Build reason with examples
            reason_parts = []
            if enhanced_reason:
                reason_parts.append(enhanced_reason)
            if problematic_phrases:
                phrase_examples = [f"'{p['phrase']}'" for p in problematic_phrases[:2]]
                reason_parts.append(f"Contains negative language: {', '.join(phrase_examples)}")
            
            reason = '. '.join(reason_parts) if reason_parts else "Standard tone analysis"
            
            # Rewrite if needed
            rewritten_title = title
            if needs_rewrite and confidence >= 60:
                style = "calm, factual" if "SENSATIONAL" in current_tone or "NEGATIVE" in current_tone else "slightly more positive"
                
                rewrite_prompt = f"""Rewrite this headline in a {style} tone while preserving all factual information:

Original: "{title}"

Requirements:
- Keep all facts accurate
- Maintain the core message
- Use {style} language
- Return ONLY the rewritten headline"""

                self.stats.increment('api_calls')
                result = self.openai_client.completions.create(
                    model=self.deployment_name,
                    prompt=rewrite_prompt,
                    max_tokens=80
                )
                rewritten_title = result.choices[0].text.strip()
                
                # Clean up response
                if rewritten_title.startswith('"') and rewritten_title.endswith('"'):
                    rewritten_title = rewritten_title[1:-1]
                if rewritten_title.startswith('Rewritten:') or rewritten_title.startswith('New:'):
                    rewritten_title = rewritten_title.split(':', 1)[1].strip()

                print(f"   Rewritten: {rewritten_title[:50]}{'...' if len(rewritten_title) > 50 else ''}")
                self.stats.increment('rewrites_successful')
            else:
                print(f"   Skipped: {reason[:50]}{'...' if len(reason) > 50 else ''}")
                self.stats.increment('articles_skipped')
            
            # Create document for upload
            # Handle both NewsAPI (publishedAt) and RSS (published_date) formats
            published_date = article.get("published_date") or article.get("publishedAt", "")

            doc = {
                "@search.action": "upload",
                "id": str(uuid.uuid4()),
                "original_title": title,
                "rewritten_title": rewritten_title,
                "original_content": article.get("content", ""),
                "source": source,
                "published_date": published_date,
                "article_url": article_url,
                "was_rewritten": needs_rewrite and confidence >= 60,
                "original_tone": current_tone,
                "confidence_score": int(confidence),
                "rewrite_reason": reason,
                "clickbait_score": clickbait_score,
                "is_clickbait": is_clickbait,
                "clickbait_reasons": '; '.join(clickbait_reasons) if clickbait_reasons else ""
            }
            
            self.stats.increment('articles_processed')
            return doc
            
        except Exception as e:
            logger.error(f"Error processing article: {str(e)}")
            self.stats.increment('rewrites_failed')
            return None

    def upload_batch(self, docs, batch_num):
        """
        Upload a batch of documents to Azure Search.
        @param {list} docs - List of documents ready for upload
        @param {int} batch_num - Batch number for logging
        @return {bool} Success status
        """
        if not docs:
            return False

        try:
            print(f"Uploading batch {batch_num} ({len(docs)} articles)...")
            self.stats.increment('api_calls')

            try:
                response = requests.post(
                    self.search_url,
                    headers=self.search_headers,
                    json={"value": docs},
                    timeout=30
                )
            except requests.exceptions.Timeout:
                print(f"Batch {batch_num} upload timeout")
                logger.error(f"Timeout uploading batch {batch_num}")
                self.stats.increment('uploads_failed', len(docs))
                return False
            except requests.exceptions.RequestException as e:
                print(f"Batch {batch_num} network error: {str(e)}")
                logger.error(f"RequestException uploading batch {batch_num}: {str(e)}")
                self.stats.increment('uploads_failed', len(docs))
                return False

            if response.status_code in [200, 201]:
                try:
                    result_data = response.json()
                    results = result_data.get('value', [])
                    successful = sum(1 for r in results if r.get('status') or r.get('statusCode') == 200 or r.get('statusCode') == 201)
                    failed = len(results) - successful

                    if failed > 0:
                        print(f"Batch {batch_num}: {successful} succeeded, {failed} failed")
                        logger.warning(f"Batch {batch_num}: {failed} documents failed indexing")
                        for r in results:
                            if r.get('statusCode') not in [200, 201]:
                                logger.error(f"Document {r.get('key')} failed: {r.get('errorMessage')}")
                    else:
                        print(f"Batch {batch_num} uploaded successfully")
                        logger.info(f"Successfully uploaded batch {batch_num}: {successful} documents")

                    self.stats.increment('uploads_successful', successful)
                    if failed > 0:
                        self.stats.increment('uploads_failed', failed)
                    return successful > 0
                except (ValueError, KeyError) as e:
                    print(f"Batch {batch_num} uploaded (unable to parse per-document results)")
                    logger.warning(f"Could not parse per-document results for batch {batch_num}: {str(e)}")
                    self.stats.increment('uploads_successful', len(docs))
                    return True
            else:
                print(f"Batch {batch_num} upload failed: {response.status_code}")
                logger.error(f"Failed to upload batch {batch_num}: {response.status_code} - {response.text}")
                self.stats.increment('uploads_failed', len(docs))
                return False

        except Exception as e:
            print(f"Batch {batch_num} upload error: {str(e)}")
            logger.error(f"Upload error for batch {batch_num}: {str(e)}")
            self.stats.increment('uploads_failed', len(docs))
            return False

    def run_batch_processing(self):
        """
        Main batch processing orchestration.
        Fetches articles, analyses headlines, rewrites as needed, and uploads to Azure Search.
        """
        start_time = time.time()
        run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Start MLflow run
        with mlflow_tracker.start_run(run_name=f"batch_processing_{run_timestamp}"):
            # Log configuration parameters
            mlflow_tracker.log_params({
                "batch_total_articles": self.TOTAL_ARTICLES,
                "batch_size": self.BATCH_SIZE,
                "batch_delay": self.BATCH_DELAY,
                "source_mode": self.SOURCE_MODE,
                "openai_deployment": self.deployment_name,
                "azure_search_index": self.azure_search_index
            })

            # Set tags
            mlflow_tracker.set_tags({
                "run_type": "batch_processing",
                "source_mode": self.SOURCE_MODE,
                "timestamp": run_timestamp
            })

            print(f"\nStarting Batch Processing")
            print(f"Target: {self.TOTAL_ARTICLES} articles in batches of {self.BATCH_SIZE}")
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            self._run_batch_processing_internal(start_time)

    def _run_batch_processing_internal(self, start_time):
        """
        Internal batch processing logic.
        @param {float} start_time - Start timestamp
        """

        # Choose article source based on configuration
        if self.SOURCE_MODE == 'rss':
            print(f"\nFetching {self.TOTAL_ARTICLES} articles from RSS feeds...")
            articles = self.fetch_articles_from_rss(self.TOTAL_ARTICLES)
        elif self.SOURCE_MODE == 'newsapi':
            print(f"\nFetching {self.TOTAL_ARTICLES} articles from NewsAPI...")
            articles = self.fetch_articles_mixed_sources(self.TOTAL_ARTICLES)
        else:  # mixed mode
            print(f"\nFetching {self.TOTAL_ARTICLES} articles from mixed sources (NewsAPI + RSS)...")
            articles = self.fetch_articles_mixed_mode(self.TOTAL_ARTICLES)

        if not articles:
            print("No articles fetched. Exiting.")
            return

        print(f"Successfully fetched {len(articles)} articles")

        total_batches = (len(articles) + self.BATCH_SIZE - 1) // self.BATCH_SIZE

        for batch_num in range(1, total_batches + 1):
            batch_start = (batch_num - 1) * self.BATCH_SIZE
            batch_end = min(batch_start + self.BATCH_SIZE, len(articles))
            batch_articles = articles[batch_start:batch_end]

            print(f"\nProcessing Batch {batch_num}/{total_batches} ({len(batch_articles)} articles)")
            
            # Process articles in this batch
            batch_docs = []
            for i, article in enumerate(batch_articles, 1):
                article_num = batch_start + i
                doc = self.process_article(article, article_num, len(articles))
                if doc:
                    batch_docs.append(doc)
                    
                # Small delay to avoid overwhelming APIs
                if i % 5 == 0:
                    time.sleep(1)
            
            if batch_docs:
                success = self.upload_batch(batch_docs, batch_num)
                if not success:
                    print(f"Batch {batch_num} upload failed, but continuing...")

            processed_articles = batch_end
            progress_pct = (processed_articles / len(articles)) * 100
            elapsed_time = time.time() - start_time

            if processed_articles < len(articles):
                avg_time_per_article = elapsed_time / processed_articles
                remaining_articles = len(articles) - processed_articles
                eta_seconds = avg_time_per_article * remaining_articles
                eta_minutes = eta_seconds / 60

                print(f"Progress: {processed_articles}/{len(articles)} ({progress_pct:.1f}%) | ETA: {eta_minutes:.1f} minutes")

            if batch_num < total_batches:
                print(f"Waiting {self.BATCH_DELAY} seconds before next batch...")
                time.sleep(self.BATCH_DELAY)

        total_time = time.time() - start_time
        print(f"\nBatch Processing Complete!")
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Final Statistics:")
        self.stats.log_summary()

        # Log metrics to MLflow
        mlflow_tracker.log_metrics({
            "articles_fetched": self.stats.get_metric('articles_fetched'),
            "articles_processed": self.stats.get_metric('articles_processed'),
            "articles_skipped": self.stats.get_metric('articles_skipped'),
            "rewrites_successful": self.stats.get_metric('rewrites_successful'),
            "rewrites_failed": self.stats.get_metric('rewrites_failed'),
            "api_calls": self.stats.get_metric('api_calls'),
            "api_errors": self.stats.get_metric('api_errors'),
            "uploads_successful": self.stats.get_metric('uploads_successful'),
            "uploads_failed": self.stats.get_metric('uploads_failed'),
            "rewrite_success_rate": self.stats.get_metric('rewrite_success_rate'),
            "total_duration_seconds": total_time,
            "total_duration_minutes": total_time / 60,
            "avg_seconds_per_article": total_time / max(self.stats.get_metric('articles_processed'), 1)
        })

def main():
    """Main entry point for batch processor."""
    try:
        processor = BatchProcessor()
        processor.run_batch_processing()
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        logger.critical(f"Fatal error in batch processing: {str(e)}")

if __name__ == "__main__":
    main()
