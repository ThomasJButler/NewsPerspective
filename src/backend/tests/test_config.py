"""Regression coverage for backend settings environment parsing.

Run with:
    python -m unittest src.backend.tests.test_config -v
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.backend.config import Settings


class SettingsRegressionTest(unittest.TestCase):
    def test_settings_ignore_news_api_key_from_environment(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NEWS_API_KEY": "user-supplied-news-key",
                "DATABASE_URL": "sqlite:///./settings-regression.db",
            },
            clear=False,
        ):
            settings = Settings()

        self.assertEqual(settings.DATABASE_URL, "sqlite:///./settings-regression.db")


if __name__ == "__main__":
    unittest.main()
