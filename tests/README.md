# NewsPerspective Test Suite

Comprehensive test suite with unit tests, integration tests, and end-to-end tests using Playwright.

## Test Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   ├── test_clickbait_detector.py  # Clickbait detection logic
│   ├── test_content_validator.py   # Article validation
│   ├── test_mlflow_tracker.py      # MLflow integration (mocked)
│   └── test_azure_key_vault.py     # Key Vault manager (mocked)
│
├── integration/                    # Integration tests (moderate speed)
│   ├── test_scrapers.py            # RSS scraping from real feeds
│   └── test_batch_processor.py     # End-to-end workflow
│
├── e2e/                            # End-to-end tests (slow, requires running apps)
│   ├── test_web_app.py             # Streamlit news browser
│   └── test_analytics_dashboard.py # Streamlit analytics dashboard
│
├── fixtures/                       # Test data and fixtures
├── conftest.py                     # Shared pytest fixtures
└── README.md                       # This file
```

## Installation

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Install Playwright Browsers

```bash
playwright install
```

Or install only Chromium (lighter):

```bash
playwright install chromium
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run by Category

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only (requires apps running)
pytest tests/e2e/
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test File

```bash
pytest tests/unit/test_clickbait_detector.py
```

### Run Specific Test

```bash
pytest tests/unit/test_clickbait_detector.py::TestClickbaitDetector::test_detect_clickbait_with_obvious_clickbait
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Skip network-dependent tests
pytest -m "not requires_network"

# Run slow tests
pytest -m slow
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Print Statements

```bash
pytest -s
```

## End-to-End Tests with Playwright

### Headless Mode (Default)

```bash
pytest tests/e2e/
```

### Headed Mode (See Browser)

```bash
pytest tests/e2e/ --headed
```

### Debug Mode (Slow, Interactive)

```bash
pytest tests/e2e/ --headed --slowmo=1000
```

### Specific Browser

```bash
# Chromium (default)
pytest tests/e2e/ --browser chromium

# Firefox
pytest tests/e2e/ --browser firefox

# WebKit (Safari-like)
pytest tests/e2e/ --browser webkit
```

### Run with Video Recording

```bash
pytest tests/e2e/ --video=on
```

## Test Configuration

### pytest.ini

Main pytest configuration file with:
- Test discovery patterns
- Coverage settings
- Markers
- Warning filters

### .coveragerc

Coverage configuration with:
- Source paths
- Exclusions (venv, tests, etc.)
- Report formatting

### conftest.py

Shared fixtures for all tests:
- `sample_article`: Mock article data
- `sample_clickbait_article`: Clickbait example
- `sample_articles_list`: Batch of articles
- `mock_azure_responses`: Mocked API responses
- `temp_data_dir`: Temporary directory for testing
- `mock_env_vars`: Environment variable mocking

## Writing Tests

### Unit Test Example

```python
import pytest
from clickbait_detector import ClickbaitDetector

class TestClickbaitDetector:
    def setup_method(self):
        self.detector = ClickbaitDetector()

    def test_detector_initialization(self):
        assert hasattr(self.detector, 'clickbait_patterns')

    def test_detect_clickbait(self):
        result = self.detector.detect_clickbait_score("Shocking News!")
        assert result['clickbait_score'] > 50
```

### Integration Test Example

```python
import pytest
from scrapers.scraper_manager import scraper_manager

@pytest.mark.integration
@pytest.mark.requires_network
def test_fetch_articles():
    articles = scraper_manager.get_all_articles_flat(max_articles_per_source=5)
    assert len(articles) > 0
```

### Playwright E2E Test Example

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_web_app(page: Page, streamlit_app):
    page.goto(streamlit_app)
    expect(page).to_have_title("NewsPerspective")

    search_input = page.get_by_label("Search Keywords")
    search_input.fill("technology")

    search_button = page.get_by_role("button", name="Search News")
    search_button.click()

    page.wait_for_selector("text=Results", timeout=5000)
```

## Continuous Integration

GitHub Actions automatically runs tests on:
- Pull requests to main/master/develop
- Pushes to develop branch

### CI Test Stages

1. **Linting**: Black formatter, Flake8
2. **Unit Tests**: Fast isolated tests (must pass)
3. **Integration Tests**: Network-dependent tests (can fail)
4. **E2E Tests**: Playwright browser tests (can fail)
5. **Coverage Upload**: Codecov reporting

## Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Overall Coverage**: >85% coverage

## Troubleshooting

### Playwright Installation Issues

```bash
# Install system dependencies
playwright install-deps

# Reinstall browsers
playwright install --force
```

### Import Errors

```bash
# Ensure you're in project root
cd /path/to/NewsPerspective

# Install in development mode
pip install -e .
```

### Port Already in Use (E2E Tests)

```bash
# Kill processes on ports 8501, 8502
lsof -ti:8501 | xargs kill
lsof -ti:8502 | xargs kill
```

### Test Discovery Issues

```bash
# Verify pytest finds tests
pytest --collect-only
```

### Azure Service Tests Failing

```bash
# Set mock environment variables
export MLFLOW_ENABLED=false
export KEYVAULT_ENABLED=false

# Run without network tests
pytest -m "not requires_network"
```

## Mocking Best Practices

### Mock External Services

```python
from unittest.mock import patch, Mock

@patch('module.requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = function_that_calls_api()
    assert result == {"data": "test"}
```

### Use responses Library

```python
import responses

@responses.activate
def test_http_request():
    responses.add(responses.GET, 'https://api.example.com/data',
                  json={'result': 'success'}, status=200)

    result = make_request()
    assert result['result'] == 'success'
```

### Fixture-Based Mocking

```python
@pytest.fixture
def mock_azure_client(monkeypatch):
    mock = Mock()
    monkeypatch.setattr('azure_module.client', mock)
    return mock

def test_with_mock_client(mock_azure_client):
    mock_azure_client.get_secret.return_value = "test_secret"
    # Your test code
```

## Performance Optimization

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

### Run Only Failed Tests

```bash
# First run
pytest

# Re-run only failures
pytest --lf
```

### Run Tests by Duration

```bash
# Run fastest tests first
pytest --durations=0
```

## Test Markers

Available markers:
- `@pytest.mark.unit`: Unit test
- `@pytest.mark.integration`: Integration test
- `@pytest.mark.e2e`: End-to-end test
- `@pytest.mark.slow`: Slow-running test
- `@pytest.mark.requires_network`: Requires internet connection

Example usage:

```python
@pytest.mark.unit
@pytest.mark.slow
def test_expensive_operation():
    # Test code
    pass
```

## Best Practices

1. **Keep Unit Tests Fast**: < 1 second each
2. **Mock External Dependencies**: Don't call real APIs in unit tests
3. **Use Fixtures**: Share test data via conftest.py
4. **Test Edge Cases**: Empty inputs, None values, boundary conditions
5. **Descriptive Names**: `test_detect_clickbait_with_obvious_clickbait` not `test1`
6. **One Assert Per Test**: Easier to debug failures
7. **Clean Up**: Reset state between tests
8. **Document Complex Tests**: Add docstrings explaining what's being tested

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
