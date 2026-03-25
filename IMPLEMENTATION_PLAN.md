# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (build slice: release-handoff state refresh, Codex GPT-5).

### Verified repo state
- Current branch is `v3.0-MVP`.
- `origin/v3.0-MVP` currently points to `e40772a` (`Finalize settings locator browser fix`).
- The pre-slice worktree was clean with no unrelated local modifications to sort around before handoff prep.
- The previously open Settings locator/browser-fix slice is no longer a handoff item. It is already committed.
- No repo-local issue tracker files or separate code-review note files were found; the active findings live in this plan.
- Legacy v1 runtime files are still absent from the checked-out repo root. Keep using git history or archived docs for legacy reference rather than recreating root-level runtime files.

### Verified product state
- Cached browse still works without a saved NewsAPI key.
- `POST /api/refresh` still requires the user key in the `X-News-Api-Key` header.
- Guardrails, comparison, category filtering, country filtering, and persistent refresh-status flows are present in the checked-in code.
- The blocked-topics flow in [`src/frontend/components/settings-dialog.tsx`](/Users/tombutler/Repos/NewsPerspective/src/frontend/components/settings-dialog.tsx) still matches [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md): guardrails load on dialog open, saves are immediate, and cached browsing remains available without a stored key.
- No new correctness regression was found in backend or frontend verification during this planning pass.
- FastAPI app metadata and the checked-in README files now report the shipped release as v3.0 consistently.
- The frontend production build now succeeds with the default `npm run build` path in this environment, so the older webpack fallback caveat is no longer current.

### Current code review / validation findings
- No open code-review or validation findings remain in the current automated build scope.

### Latest validation snapshot
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke.BackendApiSmokeTest.test_backend_entrypoint_imports_as_top_level_module -v` — passed on 2026-03-25 (**1/1 passed**, 0.036s) during release-handoff prep.
- `npm run test:e2e` — passed on 2026-03-25 (**12/12 passed**, 49.3s).
- `cd src/frontend && npm run build` — passed on 2026-03-25 using the default `next build` / Turbopack path.
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing src.backend.tests.test_manual_integration_evidence src.backend.tests.test_config src.backend.tests.test_comparison src.backend.tests.test_custom_guardrails -v` — passed on 2026-03-25 (**113/113 passed**, 1.08s).

## 2. Active phase

**Phase 12 — release handoff.** Automated correctness, browser-stability, documentation, and production-build work are closed. This loop only refreshed the handoff record and reran a minimal backend sentinel check; a trusted-machine rerun remains optional extra confidence rather than a blocker.

## 3. Ordered checklist

- [x] [P1] Verify whether the previously open Settings locator fix was still uncommitted or already landed.
- [x] [P1] Re-run the full frontend Playwright suite after the Settings locator fix instead of relying on targeted spec results.
- [x] [P1] Re-run the backend unittest suite to confirm no backend regression slipped in alongside the frontend stabilization work.
- [x] [P2] Decide whether trusted-machine manual refresh evidence is still a release blocker.
- [x] [P3] Update FastAPI app metadata in [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) from `2.0.0` to `3.0.0`.
- [x] [P3] Rewrite [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) so it describes the frontend as v3.0, removes stale "Phase 3" wording, and keeps the current trusted-machine evidence path accurate.
- [x] [P3] Update the backend validation count and nearby wording in [`README.md`](/Users/tombutler/Repos/NewsPerspective/README.md#L132) so the top-level docs match the current 113-test suite.
- [x] [P4] Verify whether the frontend production-build caveat in [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L238) still reproduces. `cd src/frontend && npm run build` passed on 2026-03-25, so the stale webpack fallback note was removed from the spec.
- [x] [P4] Refresh the release-handoff record after the validation/documentation cleanup pass so the next loop does not reopen closed implementation work.

## 4. Notes / discoveries that matter for the next loop

- The old active plan was stale about commit/handoff status. The Settings locator/browser-fix slice is already committed in `e40772a`; do not spend another build loop rediscovering or restaging it.
- The earlier Playwright port-binding issue is not an active blocker in this environment. During `npm run test:e2e`, Playwright successfully started backend and frontend web servers on `127.0.0.1:8000` and `127.0.0.1:3000`.
- Full browser coverage is green again. The two e2e files now pass together, so there is no open P1/P2 frontend regression from the recent review cycle.
- The remaining frontend build caveat is closed. `cd src/frontend && npm run build` completed successfully with the default Turbopack production-build path on 2026-03-25, so `specs/FRONTEND.md` no longer documents a webpack fallback.
- The trusted-machine evidence file already exists at [`logs/phase3_manual_integration_report.md`](/Users/tombutler/Repos/NewsPerspective/logs/phase3_manual_integration_report.md). It records a 2026-03-12 real-key backend helper run, reuse-path Playwright pass, and manual browser outcome with no documented mismatch. Because the current pass re-validated the mocked refresh flow and no later code change altered the real-key backend contract, a fresh trusted-machine rerun is optional release confidence, not a blocker.
- The remaining verified documentation/metadata mismatches are closed in this pass:
  - [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) now reports `3.0.0`
  - [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) now describes the frontend as v3.0 and refers to trusted-machine evidence without stale phase wording
  - [`README.md`](/Users/tombutler/Repos/NewsPerspective/README.md#L132) now reports the current 113-test backend suite
- The evidence filename [`logs/phase3_manual_integration_report.md`](/Users/tombutler/Repos/NewsPerspective/logs/phase3_manual_integration_report.md) remains intentionally unchanged for now. The content is still the active trusted-machine record even though the filename carries older phase naming.
- This loop reran the smallest backend sentinel from the validation list and it still passed, so the release-handoff state is not relying solely on earlier notes.
- Keep the v1/v3 boundary intact. No root-level legacy runtime files should be recreated unless a future plan item explicitly covers archival or migration work.

## 5. Next recommended build slice

**No further repo-safe implementation slice is queued.**

Concrete slice:
1. Treat the repo as release-ready from the automated-validation side.
2. If additional release confidence is needed, run the optional trusted-machine manual refresh verification already referenced in [`logs/phase3_manual_integration_report.md`](/Users/tombutler/Repos/NewsPerspective/logs/phase3_manual_integration_report.md).
3. Otherwise hand off or push/release from the current green state; do not invent new code work without a new finding or requirement.
