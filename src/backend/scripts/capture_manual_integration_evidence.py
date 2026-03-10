"""Capture a repeatable Phase 3 manual integration report.

Run with:
    python -m src.backend.scripts.capture_manual_integration_evidence \
        --api-key "$NEWS_API_KEY" \
        --output /tmp/phase3-manual-integration.md

This helper automates the backend-side HTTP checks needed for Step 16.7 and
emits a Markdown report with manual frontend placeholders. It does not replace
browser-level coverage; Step 16.8 still owns Playwright coverage.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_FRONTEND_URL = "http://localhost:3000"
DEFAULT_OUTPUT_PATH = "logs/phase3_manual_integration_report.md"
DEFAULT_INVALID_API_KEY = "invalid-key"
REQUEST_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    classification: str
    outcome: str
    evidence: str


@dataclass(frozen=True)
class HttpObservation:
    ok: bool
    status_code: int | None
    body: Any
    error: str | None = None


def _compact_json(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _capture_response(method: str, url: str, **kwargs: Any) -> HttpObservation:
    try:
        response = requests.request(
            method=method,
            url=url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        return HttpObservation(
            ok=False,
            status_code=None,
            body=None,
            error=str(exc),
        )

    try:
        body = response.json()
    except ValueError:
        body = response.text

    return HttpObservation(
        ok=True,
        status_code=response.status_code,
        body=body,
    )


def evaluate_cached_browse(observation: HttpObservation) -> ScenarioResult:
    if not observation.ok:
        return ScenarioResult(
            name="Cached browse without a key",
            classification="environment behavior",
            outcome="Could not reach GET /api/articles without a key.",
            evidence=observation.error or "Unknown transport error.",
        )

    if observation.status_code != 200:
        return ScenarioResult(
            name="Cached browse without a key",
            classification="documentation mismatch",
            outcome=f"GET /api/articles returned HTTP {observation.status_code} without a key.",
            evidence=_compact_json(observation.body),
        )

    total = None
    if isinstance(observation.body, dict):
        total = observation.body.get("total")

    if isinstance(total, int) and total > 0:
        return ScenarioResult(
            name="Cached browse without a key",
            classification="code behavior",
            outcome=f"Cached browse worked without a key and returned {total} processed articles.",
            evidence=_compact_json(observation.body),
        )

    return ScenarioResult(
        name="Cached browse without a key",
        classification="still unproven",
        outcome="The read endpoint was reachable without a key, but no cached articles were available to browse.",
        evidence=_compact_json(observation.body),
    )


def evaluate_invalid_key(observation: HttpObservation) -> ScenarioResult:
    if not observation.ok:
        return ScenarioResult(
            name="Invalid-key handling",
            classification="environment behavior",
            outcome="Could not reach POST /api/refresh for the invalid-key check.",
            evidence=observation.error or "Unknown transport error.",
        )

    body = observation.body
    if (
        observation.status_code == 401
        and isinstance(body, dict)
        and isinstance(body.get("detail"), dict)
        and body["detail"].get("code") == "invalid_api_key"
    ):
        return ScenarioResult(
            name="Invalid-key handling",
            classification="code behavior",
            outcome="Invalid-key refresh returned the structured 401 contract.",
            evidence=_compact_json(body),
        )

    return ScenarioResult(
        name="Invalid-key handling",
        classification="documentation mismatch",
        outcome=f"Invalid-key refresh did not match the expected structured 401 contract (HTTP {observation.status_code}).",
        evidence=_compact_json(body),
    )


def evaluate_refresh_start(observation: HttpObservation, api_key_supplied: bool) -> ScenarioResult:
    if not api_key_supplied:
        return ScenarioResult(
            name="Successful refresh with a real key",
            classification="still unproven",
            outcome="No real NewsAPI key was supplied to the helper.",
            evidence="Run again with --api-key to exercise the real refresh path.",
        )

    if not observation.ok:
        return ScenarioResult(
            name="Successful refresh with a real key",
            classification="environment behavior",
            outcome="Could not reach POST /api/refresh for the real-key check.",
            evidence=observation.error or "Unknown transport error.",
        )

    body = observation.body
    if observation.status_code == 200 and isinstance(body, dict) and body.get("status") == "processing":
        return ScenarioResult(
            name="Successful refresh with a real key",
            classification="code behavior",
            outcome="Real-key refresh was accepted and background processing started.",
            evidence=_compact_json(body),
        )

    return ScenarioResult(
        name="Successful refresh with a real key",
        classification="environment behavior",
        outcome=f"Real-key refresh did not start cleanly (HTTP {observation.status_code}).",
        evidence=_compact_json(body),
    )


def evaluate_duplicate_refresh(
    observation: HttpObservation | None,
    *,
    refresh_started: bool,
) -> ScenarioResult:
    if not refresh_started:
        return ScenarioResult(
            name="Duplicate refresh behavior",
            classification="still unproven",
            outcome="The helper did not observe a clean initial refresh start, so the duplicate claim was not meaningful.",
            evidence="See the real-key refresh result above.",
        )

    if observation is None:
        return ScenarioResult(
            name="Duplicate refresh behavior",
            classification="still unproven",
            outcome="No duplicate refresh request was attempted.",
            evidence="No duplicate observation captured.",
        )

    if not observation.ok:
        return ScenarioResult(
            name="Duplicate refresh behavior",
            classification="environment behavior",
            outcome="Could not reach POST /api/refresh for the duplicate check.",
            evidence=observation.error or "Unknown transport error.",
        )

    body = observation.body
    if (
        observation.status_code == 200
        and isinstance(body, dict)
        and body.get("message") == "Refresh already in progress."
    ):
        return ScenarioResult(
            name="Duplicate refresh behavior",
            classification="code behavior",
            outcome="A duplicate refresh request short-circuited while the first refresh was still running.",
            evidence=_compact_json(body),
        )

    return ScenarioResult(
        name="Duplicate refresh behavior",
        classification="still unproven",
        outcome="The duplicate request did not hit the in-progress window, so duplicate short-circuit behavior was not observed.",
        evidence=_compact_json(body),
    )


def evaluate_polling(
    observations: list[HttpObservation],
    *,
    timed_out: bool,
) -> tuple[ScenarioResult, ScenarioResult]:
    evidence = _compact_json(
        [
            {
                "status_code": observation.status_code,
                "body": observation.body,
                "error": observation.error,
            }
            for observation in observations
        ]
    )

    if not observations:
        return (
            ScenarioResult(
                name="Refresh-status polling during a long refresh",
                classification="still unproven",
                outcome="No refresh-status observations were captured.",
                evidence="[]",
            ),
            ScenarioResult(
                name="Final completion state",
                classification="still unproven",
                outcome="No terminal refresh state was captured.",
                evidence="[]",
            ),
        )

    first_error = next((item for item in observations if not item.ok), None)
    if first_error is not None:
        return (
            ScenarioResult(
                name="Refresh-status polling during a long refresh",
                classification="environment behavior",
                outcome="Polling /api/refresh/status failed before a usable state trail was captured.",
                evidence=first_error.error or evidence,
            ),
            ScenarioResult(
                name="Final completion state",
                classification="still unproven",
                outcome="A terminal refresh state could not be confirmed because polling failed.",
                evidence=first_error.error or evidence,
            ),
        )

    terminal_body = observations[-1].body if observations else None
    terminal_status = (
        terminal_body.get("status")
        if isinstance(terminal_body, dict)
        else None
    )
    saw_processing = any(
        isinstance(observation.body, dict) and observation.body.get("status") == "processing"
        for observation in observations
    )

    if timed_out:
        polling_result = ScenarioResult(
            name="Refresh-status polling during a long refresh",
            classification="still unproven",
            outcome="Polling timed out before the refresh reached a terminal state.",
            evidence=evidence,
        )
    elif saw_processing:
        polling_result = ScenarioResult(
            name="Refresh-status polling during a long refresh",
            classification="code behavior",
            outcome="Polling observed the refresh in a processing state before it finished.",
            evidence=evidence,
        )
    else:
        polling_result = ScenarioResult(
            name="Refresh-status polling during a long refresh",
            classification="still unproven",
            outcome="Polling only saw the terminal state, so a long-running processing window was not observed.",
            evidence=evidence,
        )

    if timed_out or terminal_status not in {"completed", "failed"}:
        final_result = ScenarioResult(
            name="Final completion state",
            classification="still unproven",
            outcome="A terminal completed/failed refresh state was not captured.",
            evidence=evidence,
        )
    else:
        final_result = ScenarioResult(
            name="Final completion state",
            classification="code behavior",
            outcome=f"Refresh status reached the terminal `{terminal_status}` state.",
            evidence=_compact_json(terminal_body),
        )

    return polling_result, final_result


def poll_refresh_status(
    backend_url: str,
    *,
    interval_seconds: float,
    timeout_seconds: float,
) -> tuple[list[HttpObservation], bool]:
    observations: list[HttpObservation] = []
    deadline = time.monotonic() + timeout_seconds

    while True:
        observation = _capture_response("GET", f"{backend_url}/api/refresh/status")
        observations.append(observation)

        if not observation.ok:
            return observations, False

        body = observation.body
        if not isinstance(body, dict):
            return observations, False

        if body.get("status") != "processing":
            return observations, False

        if time.monotonic() >= deadline:
            return observations, True

        time.sleep(interval_seconds)


def build_markdown_report(
    *,
    backend_url: str,
    frontend_url: str,
    results: list[ScenarioResult],
) -> str:
    lines = [
        "# Phase 3 Manual Integration Evidence",
        "",
        "## Environment",
        f"- Backend URL: `{backend_url}`",
        f"- Frontend URL: `{frontend_url}`",
        "- Seed cached data first if the feed is empty:",
        "  `python -m src.backend.scripts.seed_manual_integration_data`",
        "",
        "## Backend-side observations",
        "",
        "| Scenario | Classification | Outcome | Evidence |",
        "| --- | --- | --- | --- |",
    ]

    for result in results:
        lines.append(
            f"| {result.name} | {result.classification} | {result.outcome} | `{result.evidence}` |"
        )

    lines.extend(
        [
            "",
            "## Frontend manual follow-up",
            "",
            "- Cached browse without a key",
            "  Fill in whether `http://localhost:3000` still shows cached article cards and the inline API-key setup card when local storage is empty.",
            "- Refresh UI with a real key",
            "  Fill in the visible success, invalid-key, duplicate-refresh, and refresh-status states from the browser flow.",
            "- Docs drift",
            "  Note any mismatch between the observed UI/runtime behavior and `README.md` or `specs/`.",
            "",
            "## Classification guide",
            "",
            "- `code behavior`: observed runtime behavior that matches the current app contract.",
            "- `environment behavior`: local machine, network, or credential condition blocked the check.",
            "- `documentation mismatch`: the app responded, but the result differs from the written contract.",
            "- `still unproven`: the scenario did not execute deeply enough to confirm the target behavior.",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a Phase 3 manual integration evidence report."
    )
    parser.add_argument(
        "--backend-url",
        default=DEFAULT_BACKEND_URL,
        help=f"Backend base URL. Defaults to {DEFAULT_BACKEND_URL}.",
    )
    parser.add_argument(
        "--frontend-url",
        default=DEFAULT_FRONTEND_URL,
        help=f"Frontend base URL for the manual follow-up notes. Defaults to {DEFAULT_FRONTEND_URL}.",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="Real NewsAPI key for the successful refresh scenarios.",
    )
    parser.add_argument(
        "--invalid-api-key",
        default=DEFAULT_INVALID_API_KEY,
        help="Value to use for the invalid-key refresh scenario.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=2.0,
        help="Seconds between refresh-status polls after a successful refresh start.",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=float,
        default=120.0,
        help="Maximum polling window for the refresh-status check.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Where to write the Markdown report. Defaults to {DEFAULT_OUTPUT_PATH}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend_url = args.backend_url.rstrip("/")
    frontend_url = args.frontend_url.rstrip("/")

    results: list[ScenarioResult] = []

    cached_browse = _capture_response("GET", f"{backend_url}/api/articles")
    results.append(evaluate_cached_browse(cached_browse))

    invalid_key = _capture_response(
        "POST",
        f"{backend_url}/api/refresh",
        headers={"X-News-Api-Key": args.invalid_api_key},
    )
    results.append(evaluate_invalid_key(invalid_key))

    refresh_start = _capture_response(
        "POST",
        f"{backend_url}/api/refresh",
        headers={"X-News-Api-Key": args.api_key},
    ) if args.api_key else HttpObservation(
        ok=False,
        status_code=None,
        body=None,
        error="No real NewsAPI key supplied.",
    )
    refresh_started = (
        bool(args.api_key)
        and refresh_start.ok
        and refresh_start.status_code == 200
        and isinstance(refresh_start.body, dict)
        and refresh_start.body.get("status") == "processing"
    )
    results.append(evaluate_refresh_start(refresh_start, bool(args.api_key)))

    duplicate_refresh = (
        _capture_response(
            "POST",
            f"{backend_url}/api/refresh",
            headers={"X-News-Api-Key": args.api_key},
        )
        if refresh_started
        else None
    )
    results.append(
        evaluate_duplicate_refresh(
            duplicate_refresh,
            refresh_started=refresh_started,
        )
    )

    polling_observations, timed_out = (
        poll_refresh_status(
            backend_url,
            interval_seconds=args.poll_interval_seconds,
            timeout_seconds=args.poll_timeout_seconds,
        )
        if refresh_started
        else ([], False)
    )
    polling_result, final_result = evaluate_polling(
        polling_observations,
        timed_out=timed_out,
    )
    results.extend([polling_result, final_result])

    report = build_markdown_report(
        backend_url=backend_url,
        frontend_url=frontend_url,
        results=results,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote Phase 3 manual integration report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
