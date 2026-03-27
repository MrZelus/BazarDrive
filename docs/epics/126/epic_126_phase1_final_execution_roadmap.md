# Epic #126 — Final Execution Roadmap (Phase 1)

This document consolidates all previously analyzed sections of Epic #126 into one final execution plan and freezes Phase 1 planning output.

## Scope lock (strict)

### In scope
- Theme tokens centralization and consistent usage.
- Contrast/readability stabilization.
- Unified component states: `default/hover/active/disabled/loading`.
- Visual regression checklist and execution protocol (desktop/mobile, Chrome/Edge).
- Theme Contract documentation and adoption in UI PRs.

### Out of scope
- Full UI redesign.
- Tailwind CLI/PostCSS migration.
- API/business logic changes.

---

## A) Final prioritized epic execution roadmap

## P0 — Foundation and contrast baseline (must land first)

### 1) Token inventory and drift report
- **Objective:** identify all hardcoded color usage and token drift on critical surfaces (`Лента/Правила/Профиль`) first.
- **Why now:** without inventory, token refactor and contrast work are blind and high-risk.

### 2) Token normalization in theme source
- **Objective:** enforce one source of truth for theme tokens in `web/js/tailwind-config.js`, including safe handling of legacy aliases.
- **Why now:** downstream state and contrast work depend on stable token semantics.

### 3) Critical surface migration to tokens
- **Objective:** remove hardcoded color usage on `Лента/Правила/Профиль`, align with approved tokens.
- **Why now:** this is the highest user-impact area and prerequisite for reliable contrast validation.

### 4) Contrast stabilization gate
- **Objective:** define and run baseline contrast checks (WCAG-oriented) for text/buttons/cards across key surfaces.
- **Why now:** closes the incident class addressed by #121 and validates that token migration actually solves readability.

## P1 — Interaction consistency and repeatable regression process

### 5) Unified component states (button/tab)
- **Objective:** standardize `default/hover/active/disabled/loading`, including contrast behavior in each state.
- **Why here:** state consistency depends on P0 token and contrast baseline.

### 6) Visual regression checklist and runbook
- **Objective:** codify reproducible verification across desktop/mobile and Chrome/Edge.
- **Why here:** checklist must reflect stabilized tokens/states rather than moving targets.

### 7) Regression-driven fix pass
- **Objective:** close mismatches found during formal regression runs.
- **Why here:** ensures process produces actionable quality outcomes before documentation freeze.

## P2 — Institutionalization

### 8) Theme Contract documentation
- **Objective:** publish definitive rules: allowed tokens, anti-patterns, state matrix, verification expectations.
- **Why here:** docs are authoritative only after token/state/regression rules are validated in code.

### 9) PR protocol enforcement
- **Objective:** require Theme Contract + checklist evidence in UI PR workflow.
- **Why here:** governance should encode finalized rules, not draft assumptions.

---

## B) Dependency order (normalized)

Sequential dependency chain:

`P0.1 → P0.2 → P0.3 → P0.4 → P1.5 → P1.6 → P1.7 → P2.8 → P2.9`

Parallelization policy:
- **Allowed in parallel:** P1.5 and drafting shell of P1.6 (final checklist criteria merged only after P1.5 settles).
- **Must remain sequential:** all of P0; P1.7 after P1.6; P2.8 after P1 deliverables; P2.9 after P2.8.

---

## C) Subtask roadmap (one PR per subtask)

| # | Title (PR title format) | Priority | Objective | Likely files affected | Acceptance criteria | Verification steps | Effort | Risks | Rollback note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `Part of #126: Theme token inventory and drift report` | P0 | Build complete inventory of non-token/hardcoded color usage with migration candidates. | `web/**`, `docs/epics/126/epic_126_*` report files | Inventory complete for `Лента/Правила/Профиль`; drift list prioritized by impact. | Desktop+mobile checks in Chrome/Edge; baseline notes attached. | S | Missed usage due to dynamic class composition. | Documentation-only; no runtime rollback needed. |
| 2 | `Part of #126: Normalize theme tokens in tailwind config` | P0 | Consolidate token definitions and deprecate/alias legacy usage safely. | `web/js/tailwind-config.js`, optional shared theme helpers | Single token contract with no ambiguous duplicates; legacy handling explicitly defined. | Smoke render across key screens in Chrome/Edge and mobile emulation. | M | Visual breakage from alias removal. | Reintroduce compatibility aliases and revert unsafe removals. |
| 3 | `Part of #126: Migrate Feed/Rules/Profile to canonical theme tokens` | P0 | Replace hardcoded color classes with canonical tokens on critical pages. | `web/**` components/templates for `Лента/Правила/Профиль` | No unsupported hardcoded color usage on target surfaces; contrast remains stable. | State-by-state pass on text/cards/buttons (desktop/mobile, Chrome/Edge). | M | Hidden variants/states missed. | Revert per-page commits; re-apply incrementally. |
| 4 | `Part of #126: Add contrast stabilization gate and baseline checks` | P0 | Formalize pass/fail contrast checks and baseline pairs for key surfaces. | `docs/` checklist/gate doc, optional scripts/config | Contrast gate documented and executed at least once for all key surfaces. | Run checklist matrix: desktop/mobile × Chrome/Edge. | S | Subjective interpretation without clear thresholds. | Keep previous palette and tighten gate definitions before retry. |
| 5 | `Part of #126: Unify button and tab states` | P1 | Standardize visual and accessibility behavior for component states. | `web/components/**`, style files, possibly shared UI utilities | `default/hover/active/disabled/loading` consistent and token-driven for buttons/tabs. | Mouse/keyboard/touch checks in Chrome/Edge desktop/mobile. | M | State regressions in edge interaction paths. | Component-level revert without touching token foundation. |
| 6 | `Part of #126: Introduce visual regression checklist runbook` | P1 | Establish repeatable regression procedure and expected evidence format. | `docs/visual-regression-checklist.md`, optional PR template notes | Checklist contains steps, expected outcomes, evidence requirements, and scope boundaries. | Dry-run checklist and attach one completed sample report. | S | Checklist too generic to catch real issues. | Iterate checklist version; no runtime impact. |
| 7 | `Part of #126: Resolve findings from regression run` | P1 | Fix all critical findings from runbook execution in epic scope. | `web/**` targeted fixes, docs references | No open critical contrast/state findings for `Лента/Правила/Профиль`. | Re-run checklist matrix and compare with prior baseline. | M | Scope creep into redesign. | Reject non-scope items into separate issues. |
| 8 | `Part of #126: Publish Theme Contract v1` | P2 | Document authoritative contract for tokens, states, and review expectations. | `docs/theme-contract.md` (or agreed equivalent), cross-links | Contract includes allowed tokens, state matrix, anti-patterns, and verification mapping. | Doc review + sample PR conformance check. | S | Drift between docs and implementation reality. | Version contract and patch quickly on mismatch. |
| 9 | `Part of #126: Enforce UI PR protocol with Theme Contract and checklist` | P2 | Embed governance into PR process for ongoing compliance. | `.github/pull_request_template.md`, `docs/contributing.md` | UI PR template requires contract link, checklist evidence, and epic linkage rules. | Validate by composing test PR description against template. | S | Formal compliance without real checks. | Refine required fields; reinforce reviewer checklist. |

---

## D) Recommended first PR (P0 start)

**Recommended first implementation PR:**
`Part of #126: Theme token inventory and drift report`

### Why this is first
- Lowest implementation risk.
- Produces definitive migration backlog for P0.
- Prevents random refactors and rework across pages/components.

### Success criteria for first PR
1. Inventory includes all detected hardcoded/non-canonical color usage on `Лента/Правила/Профиль`.
2. Each finding includes suggested canonical token replacement.
3. Findings are priority-tagged (`critical/high/normal`) for migration sequencing.
4. Baseline verification note exists for desktop/mobile in Chrome/Edge.
5. PR body uses `Part of #126` and explicitly confirms in-scope boundaries.

---

## E) #126 status/progress protocol for all future subtasks

For every subtask PR:
1. **Linkage rule**
   - Intermediate PRs: `Part of #126`.
   - Final closure PR: `Closes #126` only after all epic AC/DoD gates are satisfied.
2. **Issue #126 update**
   - Update checklist item status (`todo → in progress → done`).
   - Post status comment with:
     - PR link,
     - commit SHA,
     - implemented scope,
     - verification summary (desktop/mobile, Chrome/Edge),
     - risks/deferred items.
3. **Handoff marker**
   - End each status comment with `Next: <subtask title>` and owner.
4. **Scope control**
   - Any redesign/Tailwind CLI/API-business logic request is rejected from current PR and either deferred or split into a separate issue per guardrails.

Phase 1 ends with this consolidated roadmap. Phase 2 (implementation) starts only after explicit confirmation.
