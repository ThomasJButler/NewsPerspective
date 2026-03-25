# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (twenty-third pass, Codex GPT-5, coach mode).

### Verified repo state
- Current branch is `v3.0-MVP`.
- `HEAD`, `master`, `origin/master`, and `origin/v3.0-MVP` all point to merge commit `da33acc` (`Merge pull request #6 from ThomasJButler/v3.0`).
- The previously blocked Settings locator slice in `IMPLEMENTATION_PLAN.md`, `src/frontend/components/settings-dialog.tsx`, and `src/frontend/tests/e2e/cached-browse.spec.ts` is being committed successfully in this pass.
- This environment can write the git index; `git add` on exactly those three files succeeded, so the earlier `.git/index.lock` handoff blocker is resolved.
- No unrelated worktree changes were present while finishing this slice.
- The old active-plan items about "commit local work", "push v3.0", and "merge PR #6" are stale and should not be carried forward.

### Verified product state
- Cached browse still works without a stored NewsAPI key.
- `POST /api/refresh` still requires the user key in the `X-News-Api-Key` header.
- Guardrails, comparison, country filtering, category filtering, and refresh-status flows are present in the checked-in code.
- The blocked-topics settings behavior in the validated slice still matches [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L100): the dialog loads guardrails on open, saves added keywords immediately, and keeps cached browsing available without a saved API key.
- No new backend correctness regression was found in this planning pass.
- No new product behavior changed in this pass; this slice only completes the previously validated Settings locator handoff.

### Current code review / validation findings
- [P2] Deterministic frontend browser coverage still needs one broader confirmation pass. `npx playwright test tests/e2e/cached-browse.spec.ts` is now green again, but `npm run test:e2e` has not yet been re-run after the Settings locator fixes.
- [P3] Version and doc drift remains. [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39) still reports FastAPI version `2.0.0`, and [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) still describes the frontend as "v2" and uses older phase wording.

### Latest validation snapshot
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing src.backend.tests.test_manual_integration_evidence src.backend.tests.test_config src.backend.tests.test_comparison src.backend.tests.test_custom_guardrails -v` — **113/113 passed**.
- `npx playwright test tests/e2e/refresh-path.spec.ts` — **5/5 passed**.
- `npx playwright test tests/e2e/cached-browse.spec.ts` — **7/7 passed** after giving the blocked-topic submit button and footer close button unique accessible names and updating the spec flow to dismiss Settings before using background filters.
- `git status --short` — only `IMPLEMENTATION_PLAN.md`, `src/frontend/components/settings-dialog.tsx`, and `src/frontend/tests/e2e/cached-browse.spec.ts` before this handoff commit.
- `git add IMPLEMENTATION_PLAN.md src/frontend/components/settings-dialog.tsx src/frontend/tests/e2e/cached-browse.spec.ts` — passed in this environment.

## 2. Active phase

**Phase 11 — Post-merge stabilization and v3.0 alignment.** The Settings locator fix is now committed, so the remaining work is broader browser confirmation and the last version/doc cleanup items. Do not invent new feature work unless a new verified regression appears.

## 3. Ordered checklist

- [x] [P1] Re-confirm that the validated Settings locator slice is still isolated to the same three files and remains blocked only by git-index permissions.
- [x] [P1] Stage and commit the already-validated Settings locator slice once running in a git-writable environment.
- [x] [P1] Verify whether release handoff was still pending or already completed in git state.
- [x] [P1] Re-check backend and frontend validation instead of trusting the previous plan snapshot.
- [x] [P1] Confirm whether the old Playwright port-binding blocker still reproduces.
- [x] [P2] Fix the cached-browse Playwright failure caused by the ambiguous Settings actions and re-run the targeted cached-browse spec.
- [ ] [P2] Run `npm run test:e2e` to confirm the full browser suite is green after the Settings locator fixes.
- [ ] [P3] Update FastAPI app version in [`src/backend/main.py`](/Users/tombutler/Repos/NewsPerspective/src/backend/main.py#L39).
- [ ] [P3] Update [`src/frontend/README.md`](/Users/tombutler/Repos/NewsPerspective/src/frontend/README.md) so it no longer describes the frontend as v2 or points to stale phase wording.
- [ ] [P3] Decide whether trusted-machine manual evidence still needs a fresh post-merge capture for release confidence. If yes, run the helper and record the result; if no, record why it is no longer required.

## 4. Notes / discoveries that matter for the next loop

- The old active plan was internally stale. Merge/push/dirty-worktree notes no longer match the repo state on disk.
- Fresh in this pass: the earlier git-index blocker did not reproduce. `git add` on exactly the three Settings locator slice files succeeded, allowing the validated slice to be committed cleanly.
- The relevant frontend spec remains aligned with the validated slice. [`specs/FRONTEND.md`](/Users/tombutler/Repos/NewsPerspective/specs/FRONTEND.md#L100) still requires guardrails to load on dialog open, save immediately when adding/removing blocked topics, and preserve cached browsing when no API key is stored.
- The previous Playwright blocker was environment behavior in an older run. It is no longer the current blocker. In this environment, the Playwright web servers now start on `127.0.0.1:8000` and `127.0.0.1:3000`.
- The original cached-browse blocker is fixed. [`src/frontend/components/settings-dialog.tsx`](/Users/tombutler/Repos/NewsPerspective/src/frontend/components/settings-dialog.tsx) now gives the blocked-topic submit button and the footer dismiss button distinct accessible names, and [`src/frontend/tests/e2e/cached-browse.spec.ts`](/Users/tombutler/Repos/NewsPerspective/src/frontend/tests/e2e/cached-browse.spec.ts) now targets those names and closes the modal before using background filters.
- The refresh-path Playwright spec is green, so the remaining browser issue is currently narrow rather than system-wide.
- A second strict-locator collision on `Close` only became visible after fixing the original `Add` ambiguity; it is resolved in the same slice and does not need separate follow-up.
- `README.md` at repo root is broadly aligned with v3.0. The obvious doc drift found in this pass is in the frontend-local README and the backend FastAPI metadata version.
- `src/frontend/package.json` and the About modal already use `3.0.0`, so the version drift is partial, not repo-wide.
- Keep `IMPLEMENTATION_PLAN.md` active-only. Completed merge history now belongs in the completed archive, not here.

## 5. Next recommended build slice

**Run the full frontend Playwright suite now that the Settings locator slice is committed.**

Concrete slice:
1. Run `npm run test:e2e`.
2. If the full suite passes, mark browser coverage green and move to the FastAPI version/doc drift cleanup.
3. If any case fails, capture the exact failing spec and keep the next slice narrowed to that regression.
4. Keep the follow-up commit limited to the validation result and any directly required fix.
