import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import argparse
from tabulate import tabulate
import textwrap

# Load environment variables from .env file
load_dotenv()

# Load Azure Search configuration
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX", "news-perspective-index")

# Validate required env variables
if not all([azure_search_key, azure_search_endpoint]):
    raise EnvironmentError("Azure Search credentials missing from .env file.")

# Search API setup
search_base_url = f"{azure_search_endpoint}/indexes/{azure_search_index}/docs"
headers = {
    "Content-Type": "application/json",
    "api-key": azure_search_key
}

# Test connection
def test_connection():
    """Test if we can connect to Azure Search"""
    test_url = f"{azure_search_endpoint}/indexes/{azure_search_index}?api-version=2023-11-01"
    response = requests.get(test_url, headers=headers)
    if response.status_code == 200:
        print("✅ Connected to Azure Search successfully")
        return True
    else:
        print(f"❌ Connection failed: {response.status_code} - {response.text}")
        return False


def search_articles(query="*", top=10, filter_source=None, filter_date=None):
    """Search articles in Azure Search index"""
    
    # Build search query
    search_params = {
        "api-version": "2023-11-01",
        "search": query,
        "$top": top,
        "$orderby": "published_date desc",
        "$select": "original_title,rewritten_title,source,published_date",
        "$count": "true"
    }
    
    # Add filters if specified
    filters = []
    if filter_source:
        filters.append(f"source eq '{filter_source}'")
    if filter_date:
        filters.append(f"published_date ge {filter_date}T00:00:00Z")
    
    if filters:
        search_params["$filter"] = " and ".join(filters)
    
    # Execute search
    response = requests.get(
        search_base_url,
        headers=headers,
        params=search_params
    )
    
    if response.status_code != 200:
        print(f"❌ Search error: {response.status_code} - {response.text}")
        return None
    
    return response.json()


def display_results(results):
    """Display search results in a formatted table"""
    if not results or "@odata.count" not in results:
        print("❌ No results found")
        return
    
    count = results["@odata.count"]
    articles = results["value"]
    
    print(f"\n📊 Found {count} articles\n")
    
    # Prepare data for table
    table_data = []
    for i, article in enumerate(articles, 1):
        # Format date
        pub_date = article.get("published_date", "")
        if pub_date:
            try:
                date_obj = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = pub_date[:16]
        else:
            formatted_date = "Unknown"
        
        # Truncate titles for display
        original = textwrap.fill(article.get("original_title", ""), width=40)
        rewritten = textwrap.fill(article.get("rewritten_title", ""), width=40)
        
        table_data.append([
            i,
            article.get("source", "Unknown")[:20],
            formatted_date,
            original,
            rewritten
        ])
    
    # Display table
    headers = ["#", "Source", "Date", "Original Headline", "Rewritten Headline"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def get_recent_articles(hours=24):
    """Get articles from the last N hours"""
    # Calculate date filter
    from datetime import datetime, timedelta
    filter_date = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")
    
    print(f"🕒 Fetching articles from the last {hours} hours...")
    results = search_articles(filter_date=filter_date, top=20)
    display_results(results)


def get_by_source(source_name):
    """Get articles from a specific source"""
    print(f"📰 Fetching articles from {source_name}...")
    results = search_articles(filter_source=source_name, top=20)
    display_results(results)


def search_by_keyword(keyword):
    """Search articles by keyword"""
    print(f"🔍 Searching for '{keyword}'...")
    results = search_articles(query=keyword, top=20)
    display_results(results)


def get_sources_summary():
    """Get summary of articles by source"""
    # Use faceted search to get source counts
    search_params = {
        "api-version": "2023-11-01",
        "search": "*",
        "$top": 0,  # Don't return documents, just facets
        "facet": "source,count:20"
    }
    
    response = requests.get(
        search_base_url,
        headers=headers,
        params=search_params
    )
    
    if response.status_code != 200:
        print(f"❌ Error getting sources: {response.status_code}")
        return
    
    data = response.json()
    if "@search.facets" in data and "source" in data["@search.facets"]:
        sources = data["@search.facets"]["source"]
        
        print("\n📈 Articles by Source:\n")
        table_data = [[s["value"], s["count"]] for s in sources]
        print(tabulate(table_data, headers=["Source", "Count"], tablefmt="grid"))
    else:
        print("❌ Could not retrieve source summary")


def main():
    parser = argparse.ArgumentParser(
        description="Search and view NewsPerspective articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search.py --recent               # Show articles from last 24 hours
  python search.py --recent 48            # Show articles from last 48 hours
  python search.py --source "BBC"         # Show articles from BBC
  python search.py --keyword "technology" # Search for keyword
  python search.py --sources              # Show summary by source
  python search.py                        # Show latest 10 articles
        """
    )
    
    parser.add_argument("--recent", nargs="?", const=24, type=int, 
                       help="Show recent articles (default: 24 hours)")
    parser.add_argument("--source", type=str, 
                       help="Filter by news source")
    parser.add_argument("--keyword", type=str, 
                       help="Search by keyword")
    parser.add_argument("--sources", action="store_true", 
                       help="Show summary of articles by source")
    parser.add_argument("--top", type=int, default=10, 
                       help="Number of results to show (default: 10)")
    parser.add_argument("--test", action="store_true", 
                       help="Test connection to Azure Search")
    
    args = parser.parse_args()
    
    print("🔍 NewsPerspective Search Tool")
    print("=" * 50)
    
    try:
        if args.test:
            test_connection()
        elif args.sources:
            get_sources_summary()
        elif args.recent:
            get_recent_articles(args.recent)
        elif args.source:
            get_by_source(args.source)
        elif args.keyword:
            search_by_keyword(args.keyword)
        else:
            # Default: show latest articles
            print("📰 Latest articles:")
            results = search_articles(top=args.top)
            display_results(results)
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
