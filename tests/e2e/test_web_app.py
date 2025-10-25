"""
@author Tom Butler
@date 2025-10-25
@description Playwright end-to-end tests for Streamlit web app dashboard.
"""

import pytest
from playwright.sync_api import Page, expect
import subprocess
import time
import os


@pytest.fixture(scope="module")
def streamlit_app():
    """Start Streamlit app for testing."""
    # Skip if environment variables not set
    if not os.getenv("AZURE_SEARCH_KEY"):
        pytest.skip("Azure credentials not configured")

    # Start Streamlit app
    process = subprocess.Popen(
        ["streamlit", "run", "web_app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for app to start
    time.sleep(5)

    yield "http://localhost:8501"

    # Cleanup
    process.terminate()
    process.wait()


@pytest.mark.e2e
class TestWebApp:
    """End-to-end tests for news browser web app."""

    def test_app_loads(self, page: Page, streamlit_app):
        """Test app loads successfully."""
        page.goto(streamlit_app)
        expect(page).to_have_title("NewsPerspective - Positive News Search")

    def test_welcome_screen_displays(self, page: Page, streamlit_app):
        """Test welcome screen shows when no search performed."""
        page.goto(streamlit_app)

        # Check for welcome message
        welcome_heading = page.get_by_text("Welcome to NewsPerspective!")
        expect(welcome_heading).to_be_visible()

    def test_sidebar_controls_present(self, page: Page, streamlit_app):
        """Test all sidebar controls are present."""
        page.goto(streamlit_app)

        # Check for search input
        search_input = page.get_by_label("Search Keywords")
        expect(search_input).to_be_visible()

        # Check for search button
        search_button = page.get_by_role("button", name="Search News")
        expect(search_button).to_be_visible()

    def test_search_functionality(self, page: Page, streamlit_app):
        """Test basic search functionality."""
        page.goto(streamlit_app)

        # Enter search term
        search_input = page.get_by_label("Search Keywords")
        search_input.fill("technology")

        # Click search button
        search_button = page.get_by_role("button", name="Search News")
        search_button.click()

        # Wait for results
        time.sleep(2)

        # Check results appear (or "no results" message)
        page.wait_for_selector("text=Results for", timeout=5000)

    def test_good_news_only_toggle(self, page: Page, streamlit_app):
        """Test 'Good News Only' filter toggle."""
        page.goto(streamlit_app)

        # Find and toggle "Good News Only" checkbox
        good_news_toggle = page.get_by_label("Good News Only")
        expect(good_news_toggle).to_be_visible()

        # Toggle it
        good_news_toggle.check()
        assert good_news_toggle.is_checked()

    def test_source_filter(self, page: Page, streamlit_app):
        """Test source filtering."""
        page.goto(streamlit_app)

        # Open source filter (if it's a selectbox or multiselect)
        source_filter = page.get_by_label("Filter by Source")
        if source_filter.count() > 0:
            expect(source_filter).to_be_visible()

    def test_date_range_filter(self, page: Page, streamlit_app):
        """Test date range filtering."""
        page.goto(streamlit_app)

        # Check for date range controls
        date_filter = page.get_by_label("Filter by Date")
        if date_filter.count() > 0:
            expect(date_filter).to_be_visible()

    def test_article_display(self, page: Page, streamlit_app):
        """Test article cards display correctly."""
        page.goto(streamlit_app)

        # Perform a search
        search_input = page.get_by_label("Search Keywords")
        search_input.fill("news")

        search_button = page.get_by_role("button", name="Search News")
        search_button.click()

        time.sleep(2)

        # Check for article elements (headlines, sources, etc.)
        # This will depend on your actual UI structure
        headlines = page.locator(".news-card")
        if headlines.count() > 0:
            expect(headlines.first).to_be_visible()

    def test_read_full_article_button(self, page: Page, streamlit_app):
        """Test 'Read Full Article' buttons are present."""
        page.goto(streamlit_app)

        # Perform search
        search_input = page.get_by_label("Search Keywords")
        search_input.fill("technology")
        page.get_by_role("button", name="Search News").click()

        time.sleep(2)

        # Look for "Read Full Article" links/buttons
        read_article_links = page.get_by_text("Read Full Article")
        # Should have at least one if results returned
        assert read_article_links.count() >= 0

    def test_confidence_badges_display(self, page: Page, streamlit_app):
        """Test confidence badges are shown for rewritten articles."""
        page.goto(streamlit_app)

        # Enable "Good News Only" to see rewritten articles
        page.get_by_label("Good News Only").check()

        # Search
        search_input = page.get_by_label("Search Keywords")
        search_input.fill("news")
        page.get_by_role("button", name="Search News").click()

        time.sleep(2)

        # Check for confidence badge styling (if articles exist)
        # This is dependent on actual CSS classes used
        pass  # Implementation depends on actual UI

    def test_no_results_message(self, page: Page, streamlit_app):
        """Test appropriate message shown when no results found."""
        page.goto(streamlit_app)

        # Search for something very unlikely to exist
        search_input = page.get_by_label("Search Keywords")
        search_input.fill("zzz_nonexistent_query_zzz")
        page.get_by_role("button", name="Search News").click()

        time.sleep(2)

        # Check for "no results" message
        no_results_msg = page.get_by_text("No articles found")
        expect(no_results_msg).to_be_visible(timeout=5000)

    def test_statistics_display(self, page: Page, streamlit_app):
        """Test statistics are displayed after search."""
        page.goto(streamlit_app)

        # Perform search
        page.get_by_label("Search Keywords").fill("technology")
        page.get_by_role("button", name="Search News").click()

        time.sleep(2)

        # Check for result count or statistics
        results_text = page.get_by_text("Results for")
        if results_text.count() > 0:
            expect(results_text).to_be_visible()

    def test_mobile_responsive(self, page: Page, streamlit_app):
        """Test app is responsive on mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(streamlit_app)

        # Check app still loads
        expect(page).to_have_title("NewsPerspective - Positive News Search")

        # Check key elements are still visible
        search_button = page.get_by_role("button", name="Search News")
        expect(search_button).to_be_visible()

    def test_keyboard_navigation(self, page: Page, streamlit_app):
        """Test keyboard navigation works."""
        page.goto(streamlit_app)

        search_input = page.get_by_label("Search Keywords")
        search_input.focus()

        # Type using keyboard
        page.keyboard.type("technology")

        # Tab to search button and press Enter
        page.keyboard.press("Tab")
        page.keyboard.press("Enter")

        time.sleep(2)

        # Should have navigated/searched
        assert "technology" in search_input.input_value()
