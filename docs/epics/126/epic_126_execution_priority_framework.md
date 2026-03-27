# Epic #126 — Execution priority framework ("Приоритетный план")

## Scope lock (Epic #126 only)
This framework is strictly limited to:
- Theme token centralization and consistent usage,
- Component state consistency (`default/hover/active/disabled/loading`) + a11y improvements,
- Visual regression process/checklist (desktop/mobile, Chrome/Edge),
- Theme Contract documentation.

Out of scope remains unchanged: full redesign, Tailwind CLI/PostCSS migration, API/business-logic changes.

---

## A) Priority table (priority → goal → rationale)

| Priority | Goal (objective) | Why this priority | Prerequisites | Expected output | Risks if postponed |
|---|---|---|---|---|---|
| **P0** | Централизовать токены темы и устранить рассинхрон применения. | Это фундамент для всех следующих шагов: без единого источника truth для токенов нельзя стабильно унифицировать состояния и валидировать регрессии. | Confirm current token set in `public/web/js/tailwind-config.js`; inventory of drift/hardcoded usage on key screens (`Лента/Правила/Профиль`). | Key surfaces migrated to token-based styles; drift list minimized and tracked. | P1 работы становятся хрупкими, появляется двойная работа и новые визуальные расхождения. |
| **P1** | Унифицировать состояния кнопок/табов + a11y-доработки. | После P0 можно строить единый state-model поверх стабильных токенов и снять инцидентный характер исправлений. | P0 token baseline merged; agreed state matrix (`default/hover/active/disabled/loading`) and a11y checks. | Consistent button/tab states across in-scope surfaces; keyboard/focus/disabled/loading behavior aligned. | Продолжится несогласованность интерактивных состояний; дефекты доступности будут воспроизводиться точечно. |
| **P1** | Ввести визуальные регрессии и чеклист проверки. | Этот поток должен идти сразу после (или параллельно финализации) state-unification, чтобы закрепить новый baseline и ловить откаты. | Stable token/state baseline (P0 + core P1); agreed matrix: desktop/mobile × Chrome/Edge. | Repeatable regression checklist + first formal run report. | Каждая следующая UI-правка повышает риск незамеченных откатов контраста/состояний. |
| **P2** | Задокументировать Theme Contract. | Документация должна фиксировать уже подтвержденную практику (P0/P1), иначе быстро устаревает. | Finalized token rules + state matrix + regression protocol. | `docs/` contract with allowed tokens, state rules, do/don't, verification expectations for future PRs. | Команда возвращается к ad-hoc решениям, onboarding замедляется, review становится субъективным. |

---

## B) Dependency order / sequence

Dependency chain:

1. **P0 token centralization** →
2. **P1 state unification + a11y** →
3. **P1 visual regression checklist/run** →
4. **P2 Theme Contract docs**

Why this order is correct:
- P0 establishes a stable style foundation.
- P1(state) depends on that foundation.
- P1(regression) validates the stabilized behavior and prevents rollback.
- P2 documents only what is already proven in implementation and checks.

---

## C) Parallelizable vs sequential work

### Must stay sequential
1. **P0 → P1(state)** must be sequential: state standardization before token consistency causes rework.
2. **P1(state) → P1(regression first run)** must be sequential for the first authoritative run.
3. **P1 outputs → P2 docs finalization** should be sequential to avoid stale contract text.

### Can run in parallel (after dependencies are met)
1. During late P1, **regression checklist authoring** and **final state polish** can overlap.
2. During P1 validation, **Theme Contract draft** can start in parallel as draft-only (not final/approved until regression baseline is confirmed).
3. Cross-browser/device regression execution can be split among contributors in parallel once one checklist version is frozen.

---

## D) Immediate first PR recommendation

**PR title:** `Part of #126: Enforce theme token consistency and remove drift on Feed/Rules/Profile`

**Why first:**
- Highest dependency weight for all remaining items.
- Lowest ambiguity: measurable via token usage + visual smoke checks.
- De-risks both state unification and regression formalization.

**Minimum PR deliverables:**
1. Remove/replace hardcoded color drift on `Лента/Правила/Профиль` with approved tokens.
2. Leave a short drift остаток-list (if any) as explicit follow-up.
3. Attach verification summary for desktop/mobile and Chrome/Edge.
