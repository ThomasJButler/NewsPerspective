"""
@author Tom Butler
@date 2025-10-25
@description Pytest configuration and shared fixtures for test suite.
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        "title": "Breaking: Major Technology Breakthrough Announced",
        "url": "https://example.com/article/123",
        "source": "Tech News",
        "published_date": datetime.now().isoformat(),
        "content": "Scientists have made a significant discovery in quantum computing..."
    }


@pytest.fixture
def sample_clickbait_article():
    """Sample clickbait article for testing detection."""
    return {
        "title": "You Won't Believe What Happened Next! Shocking Results Inside",
        "url": "https://example.com/clickbait/456",
        "source": "Clickbait Daily",
        "published_date": datetime.now().isoformat(),
        "content": "Click to find out more..."
    }


@pytest.fixture
def sample_articles_list():
    """List of sample articles for batch testing."""
    return [
        {
            "title": f"Article {i}: Technology News Update",
            "url": f"https://example.com/article/{i}",
            "source": "Tech Source",
            "published_date": (datetime.now() - timedelta(days=i)).isoformat(),
            "content": f"Content for article {i}"
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_rss_feed():
    """Sample RSS feed XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test News Feed</title>
        <link>https://example.com</link>
        <description>Test feed</description>
        <item>
            <title>Test Article 1</title>
            <link>https://example.com/article1</link>
            <description>Test description 1</description>
            <pubDate>Wed, 25 Oct 2025 12:00:00 GMT</pubDate>
        </item>
        <item>
            <title>Test Article 2</title>
            <link>https://example.com/article2</link>
            <description>Test description 2</description>
            <pubDate>Wed, 25 Oct 2025 11:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""


@pytest.fixture
def mock_azure_openai_response():
    """Mock Azure OpenAI API response."""
    return {
        "choices": [
            {
                "text": "Rewritten: Technology Breakthrough Announced by Researchers",
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70
        }
    }


@pytest.fixture
def mock_azure_search_response():
    """Mock Azure Search upload response."""
    return {
        "value": [
            {
                "key": "doc1",
                "status": True,
                "statusCode": 201,
                "errorMessage": None
            },
            {
                "key": "doc2",
                "status": True,
                "statusCode": 201,
                "errorMessage": None
            }
        ]
    }


@pytest.fixture
def mock_sentiment_analysis_response():
    """Mock Azure AI Language sentiment analysis response."""
    return {
        "sentiment": "negative",
        "confidence_scores": {
            "positive": 0.15,
            "neutral": 0.25,
            "negative": 0.60
        },
        "enhanced_reason": "Contains negative language patterns"
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_source_reliability_data():
    """Sample source reliability tracking data."""
    return {
        "BBC News": {
            "total_analyzed": 100,
            "clickbait_count": 5,
            "average_clickbait_score": 15.3
        },
        "Clickbait Source": {
            "total_analyzed": 50,
            "clickbait_count": 35,
            "average_clickbait_score": 75.8
        }
    }


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    monkeypatch.setenv("MLFLOW_ENABLED", "false")
    monkeypatch.setenv("KEYVAULT_ENABLED", "false")
    monkeypatch.setenv("ARTICLE_SOURCE_MODE", "rss")


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("NEWS_API_KEY", "test_news_api_key")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test_openai_key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_SEARCH_KEY", "test_search_key")
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
    monkeypatch.setenv("AZURE_SEARCH_INDEX", "test-index")
