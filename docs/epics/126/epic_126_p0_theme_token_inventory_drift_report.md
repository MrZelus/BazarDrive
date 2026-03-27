# Epic #126 — P0.1 Theme token inventory & drift report

Part of #126.

## Scope of this subtask
This PR is limited to inventory and drift analysis for theme/contrast usage on the current UI surfaces (`Лента / Правила / Профиль`). No runtime style refactor is included.

## Token source of truth (confirmed)
Defined in `web/js/tailwind-config.js`:
- `bg`
- `panel`
- `panelSoft`
- `text`
- `textSoft`
- `accent`
- `success`
- `warning`

## Inventory method
Commands used for the baseline scan:
- `rg -n "#[0-9a-fA-F]{3,8}|rgba?\(" web/css/feed.css web/js/feed.js guest_feed.html`
- `rg -n "(text|bg|border)-(white|black|gray|slate|zinc|neutral|stone|red|green|blue|yellow|amber|orange|lime|emerald|teal|cyan|sky|indigo|violet|purple|fuchsia|pink|rose)[^\s\"']*" guest_feed.html web/js/feed.js`

## Inventory summary

### 1) Tokenized usage already in place
- `guest_feed.html` broadly uses semantic tokens (`bg-bg`, `bg-panel`, `bg-panelSoft`, `text-text`, `text-textSoft`, `bg-accent`, `text-warning`, `text-success`).
- `web/js/feed.js` dynamic templates also mostly rely on semantic token utilities (`bg-panel`, `bg-panelSoft`, `text-text`, `text-textSoft`, `text-warning`, `text-success`, `text-accent`).

### 2) Drift: utility-level hardcoded colors (Tailwind palette shortcuts)
Detected outside semantic token set:
- `border-white/10`, `border-white/15`, `border-white/35`
- `text-white`, `text-black`
- `bg-black`

Primary concentration:
- `guest_feed.html`: borders and white text for action buttons/containers.
- `web/js/feed.js`: dynamic cards/comments/media and submit button text.

### 3) Drift: raw color values in custom CSS
`web/css/feed.css` contains direct `#hex` and `rgba(...)` values for interactive states:
- Tab states (`.tab-btn`, `.tab-btn.active`)
- Role/profile tab states (`.role-btn`, `.profile-menu-btn`)
- Notification variants (`.app-notification--info/success/error`)

This is the highest drift risk because these values bypass semantic token classes and can diverge from future token updates.

## High-risk priority map for subsequent P0 implementation PRs
1. **High** — `web/css/feed.css` state rules with raw color values (largest theme drift surface).
2. **High** — `web/js/feed.js` dynamic class strings using `white/black` utilities.
3. **Medium** — `guest_feed.html` static border/text color shortcuts (`white/*`, `text-white`).

## Suggested migration backlog (for next PRs, not part of this PR)
1. Define token-compatible state aliases for border/overlay variants used by tabs/roles/notifications.
2. Replace `white/black` utility shortcuts in dynamic templates with semantic token classes.
3. Replace static `border-white/*` and `text-white` usages with semantic token classes and state variants.
4. Re-run visual baseline checks on `Лента / Правила / Профиль` in desktop/mobile (Chrome/Edge).

## Baseline verification note
Inventory-only subtask completed; no runtime behavior or UI output changed in this PR.
