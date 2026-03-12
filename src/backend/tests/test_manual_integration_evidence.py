"""Tests for the Phase 3 manual integration evidence helper."""

from __future__ import annotations

import unittest

from src.backend.scripts.capture_manual_integration_evidence import (
    HttpObservation,
    build_markdown_report,
    evaluate_cached_browse,
    evaluate_duplicate_refresh,
    evaluate_frontend_reachability,
    evaluate_invalid_key,
    evaluate_polling,
    evaluate_refresh_start,
    refresh_start_was_accepted,
)


class ManualIntegrationEvidenceTest(unittest.TestCase):
    def test_frontend_reachability_marks_successful_response_as_code_behavior(self) -> None:
        result = evaluate_frontend_reachability(
            HttpObservation(
                ok=True,
                status_code=200,
                body="<!doctype html>",
            ),
            "http://localhost:3000",
        )

        self.assertEqual(result.classification, "code behavior")
        self.assertIn("frontend responded", result.outcome.lower())
        self.assertEqual(result.evidence, "HTTP 200")

    def test_frontend_reachability_marks_transport_failure_as_environment_behavior(self) -> None:
        result = evaluate_frontend_reachability(
            HttpObservation(
                ok=False,
                status_code=None,
                body=None,
                error="Connection refused",
            ),
            "http://127.0.0.1:3100",
        )

        self.assertEqual(result.classification, "environment behavior")
        self.assertIn("could not reach the frontend", result.outcome.lower())
        self.assertEqual(result.evidence, "Connection refused")

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

    def test_refresh_start_accepts_only_the_backend_accepted_processing_message(self) -> None:
        observation = HttpObservation(
            ok=True,
            status_code=200,
            body={
                "status": "processing",
                "message": "Fetching and processing articles in the background.",
            },
        )

        self.assertTrue(refresh_start_was_accepted(observation))

        result = evaluate_refresh_start(observation, api_key_supplied=True)
        self.assertEqual(result.classification, "code behavior")
        self.assertIn("background processing started", result.outcome.lower())

    def test_refresh_start_treats_duplicate_processing_response_as_unproven(self) -> None:
        observation = HttpObservation(
            ok=True,
            status_code=200,
            body={
                "status": "processing",
                "message": "Refresh already in progress.",
            },
        )

        self.assertFalse(refresh_start_was_accepted(observation))

        result = evaluate_refresh_start(observation, api_key_supplied=True)
        self.assertEqual(result.classification, "still unproven")
        self.assertIn("did not start a new one", result.outcome.lower())

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

    def test_polling_marks_http_error_responses_as_contract_failures(self) -> None:
        polling_result, final_result = evaluate_polling(
            [
                HttpObservation(
                    ok=True,
                    status_code=500,
                    body={"detail": "backend broke"},
                )
            ],
            timed_out=False,
        )

        self.assertEqual(polling_result.classification, "documentation mismatch")
        self.assertIn("http 500", polling_result.outcome.lower())
        self.assertEqual(final_result.classification, "documentation mismatch")
        self.assertIn("http 500", final_result.outcome.lower())

    def test_report_includes_manual_frontend_follow_up_section(self) -> None:
        report = build_markdown_report(
            backend_url="http://localhost:8000",
            frontend_url="http://localhost:3000",
            results=[],
        )

        self.assertIn("## Trusted-machine execution checklist", report)
        self.assertIn("## Frontend manual follow-up", report)
        self.assertIn("| Reuse-path Playwright check |", report)
        self.assertIn("npm run test:e2e:reuse -- tests/e2e/refresh-path.spec.ts", report)
        self.assertIn("## IMPLEMENTATION_PLAN.md paste template", report)
        self.assertIn("- Backend helper report path: TODO", report)
        self.assertIn("Classification guide", report)

    def test_report_uses_supplied_urls_in_manual_placeholders(self) -> None:
        report = build_markdown_report(
            backend_url="http://127.0.0.1:8100",
            frontend_url="http://127.0.0.1:3100",
            results=[],
        )

        self.assertIn("Open `http://127.0.0.1:3100`", report)
        self.assertIn(
            "`http://127.0.0.1:8100/api/articles` stayed readable without a key",
            report,
        )
        self.assertIn(
            '--backend-url "http://127.0.0.1:8100" --frontend-url "http://127.0.0.1:3100"',
            report,
        )
        self.assertIn(
            'PLAYWRIGHT_SKIP_WEBSERVER=1 PLAYWRIGHT_BASE_URL="http://127.0.0.1:3100" npx playwright test tests/e2e/refresh-path.spec.ts',
            report,
        )
        self.assertIn(
            "- Manual browser outcome at `http://127.0.0.1:3100`: TODO",
            report,
        )


if __name__ == "__main__":
    unittest.main()
