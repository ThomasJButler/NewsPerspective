"""Regression coverage for backend settings environment parsing.

Run with:
    python -m unittest src.backend.tests.test_config -v
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.backend.config import Settings


class SettingsRegressionTest(unittest.TestCase):
    def test_settings_env_file_points_to_repo_root_env(self) -> None:
        expected = str(Path(__file__).resolve().parents[3] / ".env")

        self.assertEqual(Settings.model_config.get("env_file"), expected)

    def test_settings_normalize_relative_sqlite_database_url_to_repo_root(self) -> None:
        expected = f"sqlite:///{Path(__file__).resolve().parents[3] / 'newsperspective.db'}"

        with patch.dict(
            os.environ,
            {"DATABASE_URL": "sqlite:///./newsperspective.db"},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.DATABASE_URL, expected)

    def test_settings_default_database_url_points_to_repo_root_db(self) -> None:
        expected = f"sqlite:///{Path(__file__).resolve().parents[3] / 'newsperspective.db'}"

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.DATABASE_URL, expected)

    def test_settings_ignore_news_api_key_from_environment(self) -> None:
        expected = f"sqlite:///{Path(__file__).resolve().parents[3] / 'settings-regression.db'}"

        with patch.dict(
            os.environ,
            {
                "NEWS_API_KEY": "user-supplied-news-key",
                "DATABASE_URL": "sqlite:///./settings-regression.db",
            },
            clear=False,
        ):
            settings = Settings()

        self.assertEqual(settings.DATABASE_URL, expected)


if __name__ == "__main__":
    unittest.main()
