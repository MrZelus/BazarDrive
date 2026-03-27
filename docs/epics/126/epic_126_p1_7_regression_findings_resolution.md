# Epic #126 — P1.7 Regression findings resolution (Feed/Rules/Profile)

## Scope
- **Part of #126**: close critical findings from the visual-regression pass for `Лента / Правила / Профиль`.
- **In this PR:** only contrast/state fixes tied directly to interactive controls.
- **Out of scope:** redesign, new token system design, Tailwind CLI/PostCSS migration, API/business logic.

## Findings addressed

| ID | Surface | Finding from regression pass | Resolution |
|---|---|---|---|
| P1.7-F01 | Tabs / role chips / profile sub-tabs | `:focus-visible` looked too close to `:hover`, weak keyboard focus discoverability. | Added explicit focus ring + stronger border/background deltas for `.tab-btn`, `.profile-menu-btn`, `.role-btn`. |
| P1.7-F02 | Disabled interactive states | Disabled controls relied mostly on opacity (`0.56`), reducing readability on dark surfaces. | Raised disabled opacity to `0.72` and set explicit token-aligned disabled text/background/border values. |

## Files changed
- `public/web/css/feed.css`

## Definition of done for P1.7 in this slice
1. Keyboard focus on tab/profile/role controls is visually distinct from hover state.
2. Disabled controls remain visually clear on dark UI while preserving disabled affordance.
3. No scope expansion beyond interaction/contrast findings for feed surfaces.

## Verification steps
1. Open `public/guest_feed.html` and validate in `Chrome` and `Edge`.
2. Validate matrix for `desktop` + `mobile emulation`.
3. For each screen (`Лента`, `Правила`, `Профиль`):
   - Tab through controls and confirm visible focus ring.
   - Toggle/observe disabled buttons and confirm readable text and boundaries.
4. Run `pytest -q tests/test_feed_docs_bundle.py`.

## Rollback note
- Revert only `public/web/css/feed.css` in this commit to return to pre-P1.7 state model if regressions are detected.
