# Epic #126 — References to Implementation Guidance

## A) Reference → practical rule mapping

### 1) WCAG 2.1 — Contrast (Minimum) → baseline contrast gates

**Execution influence on #126 priorities**
- Treat contrast conformance as a **P0 quality gate** for token centralization and usage cleanup, because downstream state consistency and checklist validity depend on readable base colors.

**Practical rules derived for this epic**
- Body text and button/tab labels must meet at least **4.5:1** contrast against their effective background.
- Large text (for headings or prominent labels) may use **3:1** only when it truly qualifies as large text in implementation.
- Non-text UI cues that carry meaning (e.g., selected tab indicator, active chip fill, focus ring where used as meaning carrier) should not be the sole low-contrast signal; pair with a clear visible state treatment.
- “Soft” surfaces (`panelSoft`) still require compliant foreground text; token naming cannot be used as a justification for low readability.

**Mapping to #126 work areas**
- **Theme tokens:** define and lock approved foreground/background token pairs with expected minimum contrast targets.
- **Button/tab states:** enforce readable label contrast in `default/hover/active/disabled/loading` states.
- **Regression checklist:** add explicit contrast checks per key pair on `Лента/Правила/Профиль`.
- **Theme Contract docs:** document required contrast thresholds and approved token pair matrix.

---

### 2) Material 3 — Buttons Accessibility → component/state behavior contract

**Execution influence on #126 priorities**
- Treat button and tab state accessibility as **P1**, immediately after P0 token/contrast stabilization, because components inherit token quality but add interaction-state risk.

**Practical rules derived for this epic**
- Button/tab states must be distinguishable across `default/hover/active/disabled/loading` without relying on color alone.
- Disabled state must remain legible while clearly non-interactive; avoid reducing contrast so far that labels become hard to read.
- Focus/active states must provide a clear visual cue suitable for keyboard and pointer navigation paths.
- Loading states must preserve structure/label intent (or provide equivalent affordance), not collapse into ambiguous low-contrast placeholders.

**Mapping to #126 work areas**
- **Theme tokens:** define state tokens (or token usage rules) for interactive components.
- **Button/tab states:** implement a shared state matrix applied across button and tab variants.
- **Regression checklist:** include interaction-state walkthrough (mouse + keyboard + mobile tap) in Chrome/Edge.
- **Theme Contract docs:** include state Do/Don’t examples and minimum accessibility expectations.

## B) Which rules are P0 baseline vs P1/P2 guidance

## P0 — Mandatory baseline rules (must block merge if violated)
1. All primary text on `bg/panel/panelSoft` combinations in scope screens meets minimum readable contrast (normally 4.5:1).
2. Button/tab text labels in all implemented states remain readable against state backgrounds.
3. Token usage on `Лента/Правила/Профиль` uses centralized theme tokens (no new ad-hoc hardcoded color exceptions).
4. Regression checklist contains explicit pass/fail contrast checks for text and component labels.

## P1 — Strong implementation guidance (should be completed in epic execution)
1. Full state matrix consistency for `default/hover/active/disabled/loading` across button/tab families.
2. Distinct interaction cues for focus/active/disabled/loading beyond subtle color shifts.
3. Cross-browser/state verification run (desktop/mobile, Chrome/Edge) recorded for each PR touching themed components.

## P2 — Advisory hardening (valuable, non-blocking for early PRs)
1. Expanded Theme Contract examples (good vs bad patterns for contrast/state).
2. Optional linting/check scripts to flag likely token or contrast drift before review.
3. Extended component coverage beyond initial epic surfaces once P0/P1 are stable.

## C) Short “how to use these references during PR review” checklist

1. **Token scope check (P0):** Does the PR use approved theme tokens and avoid ad-hoc color additions?
2. **Contrast check (P0):** Are text and control labels readable on actual backgrounds in changed screens/states?
3. **State check (P1):** For changed buttons/tabs, are `default/hover/active/disabled/loading` visually distinct and consistent?
4. **Interaction check (P1):** Do focus/active/disabled/loading behaviors remain understandable in keyboard, pointer, and mobile tap flows?
5. **Evidence check (P0/P1):** Does the PR include regression notes for desktop/mobile in Chrome/Edge and reference Theme Contract rules?
6. **Scope guardrail check:** If PR introduces redesign, Tailwind pipeline migration, or API/business logic changes, split/reject per #126 guardrails.
