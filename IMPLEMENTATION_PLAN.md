# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (nineteenth pass, Codex GPT-5, homer mode).

### Verified repo state
- Current branch is `v3.0-MVP`.
- `HEAD`, `master`, `origin/master`, and `origin/v3.0-MVP` all point to merge commit `da33acc` (`Merge pull request #6 from ThomasJButler/v3.0`).
- Working tree is clean.
- The old active-plan items about "commit local work", "push v3.0", and "merge PR #6" are stale and should not be carried forward.

### Verified product state
- Cached browse still works without a stored NewsAPI key.
- `POST /api/refresh` still requires the user key in the `X-News-Api-Key` header.
- Guardrails, comparison, country filtering, category filtering, and refresh-status flows are present in the checked-in code.
- No new backend correctness regression was found in this planning pass.

### Current code review / validation findings
- [P2] Deterministic frontend browser coverage is not fully green. `npx playwright test tests/e2e/cached-browse.spec.ts` now starts both web servers successfully, but fails **1 of 7** tests because `getByRole("button", { name: "Add" })` matches both the API-key add button and the blocked-topic add button in Settings.
- [P3] Version and doc drift remains. [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) still reports FastAPI version `2.0.0`, and [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) still describes the frontend as "v2" and uses older phase wording.

### Validation snapshot from this pass
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing src.backend.tests.test_manual_integration_evidence src.backend.tests.test_config src.backend.tests.test_comparison src.backend.tests.test_custom_guardrails -v` — **113/113 passed**.
- `npx playwright test tests/e2e/refresh-path.spec.ts` — **5/5 passed**.
- `npx playwright test tests/e2e/cached-browse.spec.ts` — **6/7 passed**, 1 failed on an ambiguous `Add` button locator in Settings.

## 2. Active phase

**Phase 11 — Post-merge stabilization and v3.0 alignment.** The merge handoff is done. The remaining work is to fix the one real browser-suite failure, re-run targeted browser validation, and clean up the last version/doc mismatches. Do not invent new feature work unless a new verified regression appears.

## 3. Ordered checklist

- [x] [P1] Verify whether release handoff was still pending or already completed in git state.
- [x] [P1] Re-check backend and frontend validation instead of trusting the previous plan snapshot.
- [x] [P1] Confirm whether the old Playwright port-binding blocker still reproduces.
- [ ] [P2] Fix the cached-browse Playwright failure caused by the ambiguous `Add` button in Settings.
- [ ] [P2] Re-run `npx playwright test tests/e2e/cached-browse.spec.ts` and then `npm run test:e2e` to confirm the full browser suite is green.
- [ ] [P3] Update FastAPI app version in [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39).
- [ ] [P3] Update [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) so it no longer describes the frontend as v2 or points to stale phase wording.
- [ ] [P3] Decide whether trusted-machine manual evidence still needs a fresh post-merge capture for release confidence. If yes, run the helper and record the result; if no, record why it is no longer required.

## 4. Notes / discoveries that matter for the next loop

- The old active plan was internally stale. Merge/push/dirty-worktree notes no longer match the repo state on disk.
- The previous Playwright blocker was environment behavior in an older run. It is no longer the current blocker. In this environment, the Playwright web servers now start on `127.0.0.1:8000` and `127.0.0.1:3000`.
- The current browser failure is test-visible behavior, not a port-binding failure. The failing test is [`src/frontend/tests/e2e/cached-browse.spec.ts`](/Users/tombutler/Repos/NewsPerspective/src/frontend/tests/e2e/cached-browse.spec.ts#L255), where the locator `getByRole("button", { name: "Add" })` is now ambiguous inside Settings.
- The refresh-path Playwright spec is green, so the remaining browser issue is currently narrow rather than system-wide.
- `README.md` at repo root is broadly aligned with v3.0. The obvious doc drift found in this pass is in the frontend-local README and the backend FastAPI metadata version.
- `src/frontend/package.json` and the About modal already use `3.0.0`, so the version drift is partial, not repo-wide.
- Keep `IMPLEMENTATION_PLAN.md` active-only. Completed merge history now belongs in the completed archive, not here.

## 5. Next recommended build slice

**Fix the Settings "Add" ambiguity that breaks the cached-browse Playwright spec, then re-run the targeted cached-browse browser test.**

Concrete slice:
1. Inspect the Settings dialog and the failing Playwright step.
2. Make the smallest safe change that gives the blocked-topic add action a unique, stable target.
3. Re-run `npx playwright test tests/e2e/cached-browse.spec.ts`.
4. If that passes, move next to full `npm run test:e2e`.
