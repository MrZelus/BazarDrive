# Epic #126 — Acceptance Criteria Execution-Oriented Completion Framework

This framework converts the “Acceptance Criteria Epic” section into measurable execution checks for issue/PR tracking.

## A) Acceptance criteria matrix

| Criterion | Priority | Definition of done (practical) | Verification method | Completion artifact |
|---|---|---|---|---|
| 1) Theme tokens are centralized and used consistently. | **P0** | `public/web/js/tailwind-config.js` is the single source of truth for semantic theme tokens; `Feed/Rules/Profile` no longer introduce hardcoded color values or ad-hoc color classes outside approved token mapping. | Code scan of changed files for hardcoded hex/rgb/tailwind color literals; targeted UI smoke on `Feed/Rules/Profile` in desktop/mobile and Chrome/Edge to confirm no visual breakage after token normalization. | PR with token normalization + migration diff, plus token usage audit note (before/after findings). |
| 2) Text/button/card contrast is stable on Feed/Rules/Profile. | **P0** | Required text/surface and control/surface pairs on `Feed/Rules/Profile` meet the agreed minimum contrast baseline; no critical readability regressions remain open in epic scope. | Contrast checklist run for key pairs (text, button labels, card content) across desktop/mobile and Chrome/Edge; attach measured pass/fail log and screenshots for edge cases. | Contrast report/checklist document + PR evidence links (screenshots/results). |
| 3) Component states are visually consistent. | **P1** | Button/tab states `default/hover/active/disabled/loading` follow one shared state model (same token semantics, same state intent) across scoped screens/components. | State-matrix validation against implemented components; interaction checks via mouse/keyboard/touch on desktop/mobile Chrome/Edge; verify disabled/loading distinguishability. | State matrix artifact (doc/table) + PR implementing state unification with examples. |
| 4) A visual regression procedure exists. | **P1** | A repeatable regression procedure exists with environment matrix (desktop/mobile × Chrome/Edge), clear pass criteria, and required evidence capture format. | Dry-run the procedure end-to-end at least once after state/contrast updates; confirm reproducibility by another reviewer/agent using the same checklist. | `docs` runbook/checklist + one completed regression run report linked from PR/comment. |
| 5) Theme Contract is documented and used in new PRs. | **P2** | Theme Contract in `docs/` defines allowed tokens, prohibited patterns, state expectations, and PR compliance requirements; new UI PRs reference it and include checklist proof. | Review PR template/contribution guidance and sample follow-up PR descriptions for mandatory contract reference + regression section compliance. | `docs/theme-contract*.md` + updated PR template/contribution guidance + at least one compliant PR example. |

## B) Dependency order between criteria

Recommended dependency chain:

1. **AC1 (tokens centralized)** → baseline source of truth.  
2. **AC2 (contrast stable)** → only valid once token usage is normalized.  
3. **AC3 (state consistency)** → depends on stable token and contrast foundations.  
4. **AC4 (regression procedure)** → should be finalized after AC1–AC3 criteria are testable, then used to lock them in.  
5. **AC5 (Theme Contract adoption)** → institutionalizes outcomes from AC1–AC4.

Validation constraints:
- **AC2 is not considered valid if AC1 is incomplete** (contrast can be accidental without token discipline).
- **AC3 is not considered valid if AC1/AC2 are incomplete** (state colors/feedback remain unstable).
- **AC5 is weak/partial without AC4** (contract lacks enforceable verification loop).

## C) Recommended first implementation PR driver

**First PR should be driven by AC1 (P0): “Theme tokens centralized and consistently applied.”**

Why first:
- It creates the execution baseline for every other acceptance criterion.
- It minimizes rework risk in contrast/state follow-up PRs.
- It makes regression and contract checks objective instead of subjective.

Suggested first PR scope (practical):
- Token usage audit + drift list for `Feed/Rules/Profile`.
- Replace non-compliant color usage with approved semantic tokens.
- Add short verification note proving no immediate UI regression in desktop/mobile Chrome/Edge.
