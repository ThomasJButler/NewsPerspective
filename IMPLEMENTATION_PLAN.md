# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-25 (build slice, Codex GPT-5).

### Verified repo state
- Current branch is `v3.0-MVP`.
- At the start of this slice, `HEAD` matched `origin/v3.0-MVP` at `9b5c5ae` (`Refresh release handoff plan`).
- The worktree was clean at the start of this build slice.
- Reviewed repo-local planning scratch context in `twinkly-yawning-minsky.md` and the completed-plan archive under `specs/completedarchive/`. The older `v2.0` findings in that scratch file appear resolved/superseded by the shipped v3 code/spec state and do not reopen the active queue.
- `gh issue list --limit 10` returned no visible open GitHub issues from this environment, and `gh pr status` reports no pull request attached to `v3.0-MVP`.
- Legacy v1 runtime files remain absent from the repo root. Keep using git history or archived docs for legacy reference instead of recreating root-level runtime files.

### Verified implementation state
- Backend and frontend source still match the shipped v3 runtime contract in `specs/OVERVIEW.md`, `specs/BACKEND.md`, and `specs/FRONTEND.md`: cached browse works without a saved NewsAPI key, refresh uses the `X-News-Api-Key` header, SQLite remains the active store, comparison and content guardrails are present, and refresh status is process-local with persistent frontend status UX.
- `src/backend/main.py` still reports version `3.0.0`.
- Frontend runtime prerequisites are repo-pinned to Node `22.17.0` via `.nvmrc`, and `src/frontend/package.json` requires `>=22.17.0 <23`.
- No new backend or frontend correctness regression was verified in the inspected runtime paths during this planning review/build slice.

### Current code review / validation findings
- No open P1/P2 runtime correctness regressions are currently verified in repo code, inspected tests, or today's spot checks.
- [P4] Manual-evidence tooling/docs still use older `phase3` naming (`logs/phase3_manual_integration_report.md`, helper-script text, backend spec note, frontend README, and related tests). This is consistent repo-wide today, but it is remaining v3 terminology and DX debt rather than a runtime bug.
- [P4] `logs/phase3_manual_integration_report.md` remains useful as historical trusted-machine runtime evidence, but it still reflects a 2026-03-12 trusted-machine run rather than current-loop validation.

### Latest validation snapshot
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke.BackendApiSmokeTest.test_backend_entrypoint_imports_as_top_level_module -v` — passed on 2026-03-25 (**1/1 passed**, 0.061s).
- `cd src/frontend && npm run lint` — passed on 2026-03-25. In this shell, `npm` printed an `nvm` help preamble before the normal lint output, but the command still exited `0`.
- `cd src/frontend && npm run typecheck` — passed on 2026-03-25. In this shell, `npm` printed the same `nvm` help preamble before the normal typecheck output, but the command still exited `0`.
- `README.md` Quick Start wording was re-read against `specs/OVERVIEW.md`, `specs/FRONTEND.md`, `.nvmrc`, and `src/frontend/package.json` on 2026-03-25 after the docs-only edit; the prerequisite and NewsAPI-key wording now match the shipped runtime contract.
- Not rerun in this planning pass: full backend unittest suite, `npm run build`, `npm run test:e2e`, or the trusted-machine real-key manual refresh evidence flow.

## 2. Active phase

**Phase 12 — release-facing docs alignment and handoff.** The verified remaining work is documentation cleanup plus optional trusted-machine handoff evidence. Do not invent new product or infrastructure tasks unless a new defect or spec mismatch is discovered.

## 3. Ordered checklist

- [x] Verify current branch, origin alignment, worktree state, and GitHub issue/PR status instead of relying on a stale prior handoff snapshot.
- [x] Re-read recent repo-local planning/review context and confirm older findings were either still active or already resolved before carrying them forward.
- [x] Re-read the active specs and inspect enough backend/frontend source to confirm the shipped v3 contract still matches code.
- [x] Re-run the smallest meaningful backend/frontend validation sample on the current branch.
- [x] [P2] Update `README.md` Quick Start prerequisites and setup wording so they match the shipped runtime: Node `22.17.0`/repo pinning, cached browsing without a saved NewsAPI key, and NewsAPI key requirement only when the user chooses refresh.
- [ ] [P4] Decide whether `phase3` manual-evidence naming should remain as historical terminology for the current trusted-machine report path or be renamed for v3 consistency. If renamed, update the helper script, tests, specs/docs, and default output path together in one coordinated slice.
- [ ] [P4] If release handoff needs fresh trusted-machine evidence after the README fix, rerun the manual refresh evidence flow and refresh `logs/phase3_manual_integration_report.md`; otherwise treat the existing 2026-03-12 report as historical runtime evidence only and stop.

## 4. Notes / discoveries that matter for the next loop

- Before this slice, the active branch state was `9b5c5ae`; do not reuse older plan text that still points at earlier `origin/v3.0-MVP` commits.
- The repo does contain older planning scratch context in `twinkly-yawning-minsky.md`, but it is not the active queue. Its earlier P1/P2 findings were checked against current specs/source and should not be revived unless a fresh validation run reproduces them.
- The top-level `README.md` Quick Start now matches the shipped cached-browse contract and the repo-pinned frontend Node requirement.
- The frontend runtime requirement remains pinned in repo metadata: `.nvmrc` is `22.17.0`, and `src/frontend/package.json` requires `>=22.17.0 <23`.
- The trusted-machine report at `logs/phase3_manual_integration_report.md` is dated 2026-03-12. Treat it as historical runtime evidence only unless a human explicitly wants fresh handoff evidence rerun.
- The `phase3` evidence/report naming is spread across backend helper text, backend tests, backend spec notes, and `src/frontend/README.md`. Treat any rename as coordinated cleanup rather than as an opportunistic one-line edit.
- Frontend validation commands currently exit successfully in this environment, but the shell prints an `nvm` usage preamble before `npm run lint` and `npm run typecheck`. Treat that as environment-local noise unless it is reproduced as a repo setup issue on a trusted local machine.
- A fresh manual evidence rerun is a trusted-machine task that depends on an already running local backend/frontend stack and a real exported `NEWS_API_KEY`; it is not something to manufacture inside the normal build loop if no human handoff refresh is needed.
- Keep the v1/v3 boundary intact. No root-level legacy runtime files should be recreated unless a future plan item explicitly covers archival or migration work.

## 5. Next recommended build slice

**Release-handoff slice:** decide whether the remaining `phase3` manual-evidence naming should stay as historical terminology or be renamed in one coordinated docs/test/helper pass.

Scope:
1. Decide explicitly whether `logs/phase3_manual_integration_report.md` and related references are historical names worth keeping or low-priority terminology debt worth renaming now.
2. If keeping the name, record that handoff decision and stop.
3. If renaming, update the helper script, tests, specs/docs, and default output path together in one coordinated slice.
4. Do not invent new product/runtime work; the remaining queue after that is optional trusted-machine evidence refresh only.

After that slice, the remaining queue is optional trusted-machine evidence refresh, not new feature or correctness work.
