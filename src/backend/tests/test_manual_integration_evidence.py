"""Tests for the Phase 3 manual integration evidence helper."""

from __future__ import annotations

import unittest

from src.backend.scripts.capture_manual_integration_evidence import (
    HttpObservation,
    build_markdown_report,
    evaluate_cached_browse,
    evaluate_duplicate_refresh,
    evaluate_invalid_key,
    evaluate_polling,
)


class ManualIntegrationEvidenceTest(unittest.TestCase):
    def test_cached_browse_marks_empty_feed_as_unproven(self) -> None:
        result = evaluate_cached_browse(
            HttpObservation(
                ok=True,
                status_code=200,
                body={"articles": [], "total": 0},
            )
        )

        self.assertEqual(result.classification, "still unproven")
        self.assertIn("no cached articles", result.outcome.lower())

    def test_invalid_key_accepts_structured_401_contract(self) -> None:
        result = evaluate_invalid_key(
            HttpObservation(
                ok=True,
                status_code=401,
                body={
                    "detail": {
                        "code": "invalid_api_key",
                        "message": "Invalid NewsAPI key.",
                    }
                },
            )
        )

        self.assertEqual(result.classification, "code behavior")
        self.assertIn("structured 401", result.outcome)

    def test_duplicate_refresh_marks_missed_window_as_unproven(self) -> None:
        result = evaluate_duplicate_refresh(
            HttpObservation(
                ok=True,
                status_code=200,
                body={
                    "status": "processing",
                    "message": "Fetching and processing articles in the background.",
                },
            ),
            refresh_started=True,
        )

        self.assertEqual(result.classification, "still unproven")
        self.assertIn("did not hit the in-progress window", result.outcome)

    def test_polling_distinguishes_processing_window_and_terminal_state(self) -> None:
        polling_result, final_result = evaluate_polling(
            [
                HttpObservation(
                    ok=True,
                    status_code=200,
                    body={"status": "processing", "message": "Working"},
                ),
                HttpObservation(
                    ok=True,
                    status_code=200,
                    body={"status": "completed", "message": "Done"},
                ),
            ],
            timed_out=False,
        )

        self.assertEqual(polling_result.classification, "code behavior")
        self.assertEqual(final_result.classification, "code behavior")
        self.assertIn("terminal `completed`", final_result.outcome)

    def test_report_includes_manual_frontend_follow_up_section(self) -> None:
        report = build_markdown_report(
            backend_url="http://localhost:8000",
            frontend_url="http://localhost:3000",
            results=[],
        )

        self.assertIn("## Frontend manual follow-up", report)
        self.assertIn("Classification guide", report)


if __name__ == "__main__":
    unittest.main()
