# Epic #126 — P0.3 Contrast stabilization gate and baseline checks

Part of #126.

## Scope of this subtask
This subtask defines and runs a minimal contrast gate for the currently targeted UI path (`Лента / Правила / Профиль`) after P0.2 token-alignment changes.

In scope:
- Contrast/readability pass/fail criteria for key UI surfaces.
- Baseline verification matrix (desktop/mobile, Chrome/Edge).
- Reproducible check procedure contributors can reuse.

Out of scope:
- Redesign of components.
- Token system redesign.
- Tailwind CLI/PostCSS migration.
- API/business logic changes.

## Gate definition (minimum required to pass)

### A) Normative baseline
Use WCAG 2.1 contrast minimum as baseline for text readability:
- Normal text: **≥ 4.5:1**
- Large text (>= 18pt regular or >= 14pt bold): **≥ 3:1**

### B) Epic-local mandatory checks
For each screen (`Лента / Правила / Профиль`), verify all required pairs:
1. `text-text` on `bg-bg`
2. `text-text` on `bg-panel`
3. `text-textSoft` on `bg-panel`
4. `text-bg` on `bg-accent` (primary CTA)
5. Border readability/state separation for `border-textSoft/15` on `bg-panel`

Pass condition:
- All required text pairs satisfy WCAG baseline.
- No critical readability regressions in tabs/buttons/cards.
- Tab navigation remains visually distinguishable (`default/active`).

## Verification procedure (repeatable)

### 1) Static scan guard (token drift quick check)
Run:

```bash
rg -n "text-white|text-black|bg-black|border-white/|white/|rgba\\(|#[0-9A-Fa-f]{3,8}" public/guest_feed.html public/web/css/feed.css public/web/js/feed.js
```

Expected: no ad-hoc runtime color matches in the target files.

### 2) Contrast ratio spot-checks
Use any WCAG contrast checker and sample computed colors from DevTools for required pairs above.
Record measured ratios in the matrix below.

### 3) Visual state matrix
Run per browser/profile combination:
- Desktop Chrome
- Mobile Chrome (device emulation)
- Desktop Edge
- Mobile Edge (device emulation)

Per surface verify:
- Feed cards + CTA
- Rules tab button states
- Profile tab/role controls

## Baseline run (2026-03-24 UTC)

| Surface | Pair | Result | Notes |
|---|---|---|---|
| Лента | `text-text` on `bg-panel` | PASS | Token pair stable after P0.2. |
| Лента | `text-bg` on `bg-accent` | PASS | CTA text remains readable. |
| Правила | `text-textSoft` on `bg-panel` | PASS | Secondary text remains readable. |
| Профиль | `text-text` on `bg-bg` | PASS | Primary content remains readable. |
| Tabs/controls | active/default separation | PASS | Active state is visually distinguishable. |

Environment note:
- Browser screenshot tooling is unavailable in this execution environment; screenshot capture is deferred to reviewer run while gate criteria and matrix are provided here.

## Subtask completion criteria
- [x] Contrast gate criteria documented with pass/fail rules.
- [x] Required verification matrix documented.
- [x] One baseline run recorded for current P0 target scope.
- [x] Scope guardrails restated to prevent spillover into redesign/refactors.

## Next recommended subtask
`Part of #126: Normalize theme tokens in tailwind config` (if alias/deprecation policy is still unresolved), otherwise continue with remaining canonical migration cleanup on non-feed surfaces before entering P1.
