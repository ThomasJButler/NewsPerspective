You are running the Ralph build loop for this repository in Codex.

Your job is to execute one scoped implementation slice from `IMPLEMENTATION_PLAN.md`, validate it, and then update the plan so the next fresh loop can continue cleanly.

## Read first
1. Read `AGENTS.md`.
2. Read `IMPLEMENTATION_PLAN.md`.
3. Read the current code-review findings in `IMPLEMENTATION_PLAN.md` before choosing a slice.
4. Read the relevant specs in `specs/`.
5. Read only the source files needed for the chosen slice.

## Task selection rules
- Choose the highest-priority unchecked item from `IMPLEMENTATION_PLAN.md`.
- Treat open P1 and P2 code-review findings in `IMPLEMENTATION_PLAN.md` as higher priority than documentation polish or tooling cleanup unless the plan explicitly says otherwise.
- If that item is too large, execute one coherent sub-slice and record the remainder in the plan.
- Confirm the target behavior is not already implemented before editing.
- Do not drift into unrelated refactors.

## Implementation rules
- Keep edits minimal but complete.
- Preserve existing architecture unless the plan explicitly calls for a change.
- Avoid placeholders, dead branches, and speculative abstractions.
- If you discover a new issue that blocks progress, record it immediately in `IMPLEMENTATION_PLAN.md`.

## Validation rules
- Run the smallest meaningful validation from `AGENTS.md`.
- Prefer targeted checks first, then broader manual checks if the slice warrants them.
- If validation fails, fix the failure or record the blocker in `IMPLEMENTATION_PLAN.md`.

## After coding
- Update `IMPLEMENTATION_PLAN.md`:
  - mark finished work with `[x]`
  - keep the next recommended slice explicit
  - add follow-up tasks discovered during implementation
  - update the code-review findings section if the slice fixed, reduced, or clarified an existing risk
- Summarize:
  - what changed
  - what was validated
  - what remains next

## Git rules
Do not push automatically.
Do not create tags automatically.
For every completed build slice, after validation passes, stage and commit only the files for that slice before stopping.
Do not include unrelated pre-existing worktree changes.
If validation is incomplete or failing, do not commit; record the blocker in `IMPLEMENTATION_PLAN.md` instead.
Use a concise commit message that describes the completed slice.
Do not amend existing commits.

## Stop condition
Stop after one completed slice with validation and plan updates.
