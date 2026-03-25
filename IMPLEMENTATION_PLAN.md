# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (eighteenth pass, Codex GPT-5, `v3.0` branch).

### Verified runtime state
- `POST /api/refresh` requires a user-supplied `X-News-Api-Key`. Cached read-only endpoints still work without a key.
- v3.0 feature work is shipped locally, including country-aware reading, Article Comparison, pluggable news sources, and user-configurable content guardrails.
- The latest local review-fix slice is also implemented: blocked-topic saves refresh the feed immediately, custom blocked topics use whole-word / whole-phrase matching, and comparison grouping is transitive.
- No open code-review findings remain in the active plan. Fully resolved history now lives in `specs/completedarchive/2026-03-25-implementation-completed-archive.md`.

### Validation snapshot
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_api_smoke -v` — **35/35 passed**.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_refresh_processing -v` — **13/13 passed**.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_manual_integration_evidence -v` — **14/14 passed**.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_config -v` — **4/4 passed**.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_custom_guardrails -v` — **25/25 passed**.
- `src/backend/.venv/bin/python -m unittest src.backend.tests.test_comparison -v` — **22/22 passed**.
- `npx playwright test tests/e2e/cached-browse.spec.ts` — blocked in this sandbox because the backend test server could not bind `127.0.0.1:8000` (`[Errno 1] operation not permitted`).

### Branch and worktree state
- Active branch: `v3.0`.
- `master` is commit `8b54903`.
- Local branch is **26 commits ahead** of `master`.
- PR #6 (`v3.0` → `master`) remains the intended merge path.
- The worktree is not clean: the local review-fix slice and this archive-cleanup/doc-update slice are still uncommitted.

## 2. Active phase

**Phase 10 — Release handoff and active-plan hygiene.** The implementation work is complete locally. The remaining work is release handoff, final browser validation outside this sandbox, and merge preparation. Ralph should not invent new feature work unless a new regression or missing requirement is discovered.

## 3. Ordered checklist

- [x] [P2] Archive bulky completed Ralph-loop history into `specs/completedarchive/2026-03-25-implementation-completed-archive.md`.
- [x] [P2] Update Ralph prompts so `IMPLEMENTATION_PLAN.md` stays active-only and bulky completed history moves into dated archive files.
- [ ] [P2] Commit the current local review-fix + archive-cleanup slice without mixing unrelated worktree changes.
- [ ] [P2] Run `npx playwright test tests/e2e/cached-browse.spec.ts` in an environment that can bind `127.0.0.1:8000`.
- [ ] [P2] Push `v3.0` and merge PR #6 into `master`.
- [ ] [P3] Record the post-merge state in `IMPLEMENTATION_PLAN.md` and archive any newly stale completed detail if the plan grows bulky again.
- [ ] [P3] Demo video: record with OBS, edit with DaVinci Resolve, upload to YouTube, and link from README and About modal.

## 4. Notes / discoveries that matter for the next loop

- Ralph loop behavior is prompt-driven. `loop.sh` and `loop-claude.sh` are thin wrappers and were intentionally left unchanged.
- `PROMPT_plan.md` is now the place where Ralph is told to archive bulky completed history into dated files under `specs/completedarchive/`.
- `PROMPT_build.md` now explicitly treats manual release handoff as a valid endgame slice and warns build runs not to invent fresh coding work when only handoff tasks remain.
- The active plan should stay focused on current state, blockers, validation, and next actions. Historical completion detail belongs in `specs/completedarchive/`.
- Network access is still blocked in this environment. `git push` and GitHub API operations must be done manually by the user.
- The Playwright blocker here is local sandboxing, not an app assertion failure: the backend test server could not bind `127.0.0.1:8000`.
- Existing local code changes from the review-fix slice are still present and should be considered part of the next commit unless the user explicitly wants a different split.
- Ralph is now on the right endgame track only if the next iteration is treated as release handoff, not another feature build.

## 5. Next recommended build slice

**Release handoff slice: commit the current local work, then validate the targeted Playwright path outside the sandbox.**

1. Review and stage only the intended files for the current local review-fix + archive-cleanup slice.
2. Create one concise commit for that slice.
3. Run `npx playwright test tests/e2e/cached-browse.spec.ts` on a machine that can start the backend test server on `127.0.0.1:8000`.
4. If that passes, `git push origin v3.0` and merge PR #6.
5. After merge, update the plan to reflect the merged state and keep only any still-active post-merge work.
