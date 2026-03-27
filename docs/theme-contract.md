# Theme Contract v1 (Epic #126)

Part of #126.

## 1) Scope and intent

This contract defines the **authoritative theme usage rules** for Epic #126 UI surfaces (`Лента`, `Правила`, `Профиль`) and PRs that touch them.

In scope:
- canonical theme tokens,
- contrast/readability expectations,
- component state matrix (`default/hover/active/disabled/loading`),
- verification evidence for desktop/mobile in Chrome/Edge.

Out of scope for this contract rollout:
- full redesign,
- Tailwind CLI/PostCSS migration,
- API/business logic changes.

---

## 2) Canonical token set (source of truth)

Token source of truth is `public/web/js/tailwind-config.js`.

Allowed semantic tokens:
- `bg`
- `panel`
- `panelSoft`
- `text`
- `textSoft`
- `accent`
- `success`
- `warning`

### Mandatory token rules
1. Use semantic tokens for UI surfaces, text, and control states.
2. Do not introduce new raw `#hex`, `rgba(...)`, or ad-hoc utility colors in Epic #126 surfaces.
3. Do not re-introduce high-risk drift patterns: `white/*`, `text-white`, `text-black`, `bg-black` for runtime UI surfaces when a semantic token exists.
4. Any exception must be documented in the PR with rationale and a follow-up item.

---

## 3) Contrast baseline (merge-blocking for #126 scope)

1. Standard text and button/tab labels should meet **4.5:1** contrast against effective backgrounds.
2. Large text can use **3:1** only when it truly qualifies as large text.
3. Active/focus/disabled/loading states must remain understandable and readable; state cues should not rely on low-contrast color shift alone.
4. `panelSoft` is not a contrast exception: readable foreground is still required.

---

## 4) Component state matrix (minimum required behavior)

Applies to button/tab-like controls used in `Лента/Правила/Профиль`.

- `default`: readable foreground/background, clear border or fill definition.
- `hover`: visible emphasis change without reducing readability.
- `active`: persistent selected/pressed indication, distinct from hover.
- `disabled`: clearly non-interactive, but label remains legible.
- `loading`: communicates busy state (`aria-busy`/disabled sync) while preserving control context.

### State consistency rules
1. State behavior must be consistent for equivalent control families.
2. Keyboard focus (`:focus-visible`) must be visually distinct from default and hover.
3. Loading and disabled must not create ambiguous “broken” appearance.

---

## 5) Anti-patterns (do not merge)

1. New hardcoded colors on epic surfaces when canonical token exists.
2. Text or control labels with low readability on `bg/panel/panelSoft`.
3. Tab/button states where hover/active/focus are visually indistinguishable.
4. Disabled state implemented primarily via excessive opacity that harms legibility.

---

## 6) Verification mapping (required PR evidence)

For any PR that touches themed UI in scope, include:

1. **Scope note**: what surface/components changed and why it is in #126 scope.
2. **State check**: `default/hover/active/disabled/loading` verification for impacted controls.
3. **Matrix check**: desktop/mobile in Chrome/Edge.
4. **Contrast note**: confirm readability for changed text/control pairs.
5. **Drift check**: confirm no new high-risk ad-hoc color patterns introduced.

Suggested verification commands:
- `pytest -q tests/test_feed_docs_bundle.py`
- `rg -n "text-white|text-black|bg-black|border-white/|white/|#[0-9A-Fa-f]{3,8}|rgba\(" public/guest_feed.html public/web/css/feed.css public/web/js/feed.js public/web/js/tailwind-config.js`

---

## 7) PR governance mapping

- Intermediate PRs in this epic use `Part of #126`.
- Epic closure can use `Closes #126` only after all acceptance criteria and DoD gates are satisfied.
- If a change request falls outside contract scope (redesign, Tailwind pipeline migration, API/business logic), reject from current PR and split/defer per #126 guardrails.

---

## 8) Contract versioning

- This document is **Theme Contract v1**.
- Compatible clarifications can update v1.
- Any behavioral or policy-breaking changes require a version bump (v1.1/v2) and explicit migration note.
