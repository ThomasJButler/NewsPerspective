# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (build slice: v3.0 docs/metadata alignment, Codex GPT-5).

### Verified repo state
- Current branch is `v3.0-MVP`.
- `origin/v3.0-MVP` currently points to `e40772a` (`Finalize settings locator browser fix`).
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

### Current code review / validation findings
- [P4] Frontend production-build caveat remains unverified in the current environment. [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L238) still carries the earlier `npm run build` / `npx next build --webpack` fallback note and needs a fresh confirmation pass.

### Latest validation snapshot
- `npm run test:e2e` — passed on 2026-03-25 (**12/12 passed**, 49.3s).
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing src.backend.tests.test_manual_integration_evidence src.backend.tests.test_config src.backend.tests.test_comparison src.backend.tests.test_custom_guardrails -v` — passed on 2026-03-25 (**113/113 passed**, 1.08s).
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke.BackendApiSmokeTest.test_backend_entrypoint_imports_as_top_level_module -v` — passed on 2026-03-25 (**1/1 passed**, 0.057s).

## 2. Active phase

**Phase 11 — release-facing validation cleanup.** Recent correctness, browser-stability, and doc/metadata alignment regressions are closed for now. The remaining active work is a lower-priority verification pass for the frontend production-build caveat.

## 3. Ordered checklist

- [x] [P1] Verify whether the previously open Settings locator fix was still uncommitted or already landed.
- [x] [P1] Re-run the full frontend Playwright suite after the Settings locator fix instead of relying on targeted spec results.
- [x] [P1] Re-run the backend unittest suite to confirm no backend regression slipped in alongside the frontend stabilization work.
- [x] [P2] Decide whether trusted-machine manual refresh evidence is still a release blocker.
- [x] [P3] Update FastAPI app metadata in [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) from `2.0.0` to `3.0.0`.
- [x] [P3] Rewrite [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) so it describes the frontend as v3.0, removes stale "Phase 3" wording, and keeps the current trusted-machine evidence path accurate.
- [x] [P3] Update the backend validation count and nearby wording in [`README.md`](/Users/tombutler/Repos/NewsPerspective/README.md#L132) so the top-level docs match the current 113-test suite.
- [ ] [P4] Verify whether the frontend production-build caveat in [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L238) still reproduces. If it no longer reproduces, simplify the docs; if it does, record the exact current fallback command and environment limitation.

## 4. Notes / discoveries that matter for the next loop

- The old active plan was stale about commit/handoff status. The Settings locator/browser-fix slice is already committed in `e40772a`; do not spend another build loop rediscovering or restaging it.
- The earlier Playwright port-binding issue is not an active blocker in this environment. During `npm run test:e2e`, Playwright successfully started backend and frontend web servers on `127.0.0.1:8000` and `127.0.0.1:3000`.
- Full browser coverage is green again. The two e2e files now pass together, so there is no open P1/P2 frontend regression from the recent review cycle.
- The trusted-machine evidence file already exists at [`logs/phase3_manual_integration_report.md`](/Users/tombutler/Repos/NewsPerspective/logs/phase3_manual_integration_report.md). It records a 2026-03-12 real-key backend helper run, reuse-path Playwright pass, and manual browser outcome with no documented mismatch. Because the current pass re-validated the mocked refresh flow and no later code change altered the real-key backend contract, a fresh trusted-machine rerun is optional release confidence, not a blocker.
- The remaining verified documentation/metadata mismatches are closed in this pass:
  - [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) now reports `3.0.0`
  - [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) now describes the frontend as v3.0 and refers to trusted-machine evidence without stale phase wording
  - [`README.md`](/Users/tombutler/Repos/NewsPerspective/README.md#L132) now reports the current 113-test backend suite
- The evidence filename [`logs/phase3_manual_integration_report.md`](/Users/tombutler/Repos/NewsPerspective/logs/phase3_manual_integration_report.md) remains intentionally unchanged for now. The content is still the active trusted-machine record even though the filename carries older phase naming.
- Keep the v1/v3 boundary intact. No root-level legacy runtime files should be recreated unless a future plan item explicitly covers archival or migration work.

## 5. Next recommended build slice

**Verify the frontend production-build caveat and either close it or document the exact current fallback.**

Concrete slice:
1. From `src/frontend`, run `npm run build`.
2. If the build passes, update [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L238) and any nearby docs to remove the stale caveat and fallback wording.
3. If the build fails for the known environment-sensitive reason, capture the exact failure mode and confirm whether `npx next build --webpack` still works as the documented fallback.
4. Stop after documenting that verification result; do not expand into unrelated frontend refactors.
