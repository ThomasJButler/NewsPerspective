# Completed Implementation Archive

Created: 2026-03-25

This archive captures bulky completed history that was removed from the active `IMPLEMENTATION_PLAN.md` so Ralph can use that file as a short-lived working plan rather than a long-term project ledger.

## Source basis
- Current `IMPLEMENTATION_PLAN.md` before archive cleanup on 2026-03-25.
- Existing archive pattern in `specs/completedarchive/2026-03-10-implementation-completed-archive.md`.
- Current `v3.0` branch state at the time of cleanup.

## Material moved out of the active plan
- The `v3.0 commits (not yet on master)` reference block.
- Fully completed checklist history for Phases 5, 6, 7, and 8.
- Resolved review findings that no longer require implementation work.

## Archived v3.0 commit ledger
These commit references were preserved here as historical context and removed from the active plan:

```
de0344d Enforce content guardrails consistently across all read endpoints
a4a23b2 Fix cross-module test isolation for unified test runner
6b08328 Update README test count from 66/4 to 98/6 modules
81bc4c9 Fix spec text drift and add missing test_comparison validation command
d90370a Add user-configurable content guardrails frontend
c3ab0cf Add user-configurable content guardrails backend
26bffa8 Add pluggable NewsSource protocol with dependency injection
779f586 Add /comparison page with side-by-side article groups and AI analysis
df2df84 Add POST /api/comparison/analyse endpoint with AI framing analysis
016b2c5 Add GET /api/comparison endpoint with fuzzy title grouping
f5f7d68 Add AGPLv3 LICENSE, fix about-modal URLs, update e2e test selectors
ea88844 Rewrite README for open-source audience and clean up stale ROADMAP sections
7d03b5f Wire CategoryFilter into page state, URL params, and metadata loading
2aba547 Create category-filter.tsx
3d2a4f8 Add ARIA attributes to improve accessibility
3b5c72b Add accessibility improvements: aria-labels, nav landmark, live region, aria-busy
dc41059 Update plan for v3.0 → master PR and fresh validation run
1e4f5cd Add content guardrails for war, suicide, depression, death, and grief
9b37e29 Align all specs, docs, and package.json to v3.0 naming
ce17dd1 Implementation plan v3.0 and Claude flag update
2501624 Update specs for country support, banner images, and new components
f87e332 Update About modal version to v3.0.0 and fix premature license claim
2f240b2 Tighten country param validation and include country in normalization
4c43e0f Fix skeleton loading to show image placeholders on all cards
b10a31c Add country support, banner images, About modal
```

## UX and feature buildout
- Phase 5 verification and stabilization work was completed and removed from the active plan:
  - full source verification
  - test isolation fixes
  - security dependency bump
  - spec and validation-command alignment
  - Playwright e2e stabilization
  - package-lock persistence
  - v2 branch cleanup after merge
- Phase 6 UX polish was completed and removed from the active plan:
  - headline rewrite visibility evaluation
  - article card layout upgrade
  - header/feed layout alignment
  - roadmap evaluation
- Phase 7 feature buildout was completed and removed from the active plan:
  - country-aware reading
  - About modal
  - v3.0 spec-version alignment
  - built-in content guardrails
  - accessibility pass
  - topic filtering UI

## Open-source launch and comparison work
- Phase 8 work was completed and removed from the active plan:
  - AGPLv3 license adoption
  - README overhaul for open-source use
  - Article Comparison backend grouping
  - Article Comparison AI analysis
  - Article Comparison frontend page
  - pluggable news source architecture
  - user-configurable content guardrails in both backend and frontend

## Closed review and correctness slices
- The following fully resolved review findings were moved out of the active plan:
  - spec text drift for shipped features
  - stale README test counts and missing validation-command docs
  - version naming drift across specs and package metadata
  - missing `/api/categories`
  - inconsistent guardrail enforcement across read endpoints
  - blocked-topics save flow not refreshing visible feed state
  - custom blocked-topic false positives from substring matching
  - order-dependent comparison grouping

## Validation and developer-workflow updates
- The following validation and workflow updates were completed and removed from the active plan:
  - cross-module backend test isolation fixes
  - updated backend validation coverage for comparison and custom guardrails
  - lint and typecheck alignment for the shipped frontend state
  - documentation of the current sandbox limitation for Playwright web-server binding on `127.0.0.1:8000`
- Ralph loop behavior was confirmed during this cleanup:
  - `loop.sh` and `loop-claude.sh` are thin runners
  - `PROMPT_plan.md` and `PROMPT_build.md` are the correct place to teach Ralph how to keep `IMPLEMENTATION_PLAN.md` active-only and archive bulky completed history
