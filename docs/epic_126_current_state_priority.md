# Epic #126 — Current-state analysis and priority breakdown

## A) Current state: confirmed / partially complete / missing

### Confirmed
- **Theme token baseline exists** in `web/js/tailwind-config.js` with a centralized palette (`bg`, `panel`, `panelSoft`, `text`, `textSoft`, `accent`, `success`, `warning`).
- **Initial foundation from #121 exists** (baseline diagnostics + partial contrast/state fixes), so this epic does **not** start from zero.

### Partially complete
- **System-level adoption is incomplete**: tokens are defined, but there is no proof yet that all key UI surfaces (`Лента / Правила / Профиль`) consistently consume only the tokenized set.
- **State consistency is partial**: some contrast/state issues were fixed in #121, but no explicit, enforced `default/hover/active/disabled/loading` matrix is visible as a stable contract.
- **Regression practice is not yet institutionalized**: baseline checks exist, but a repeatable visual process for desktop/mobile + Chrome/Edge still needs formalization.

### Missing
- **Formal Theme Contract** in docs that is used as a merge criterion for new UI PRs.
- **Operational quality gate** tying token usage + state matrix + regression evidence into one stable workflow.

---

## B) Priority list (P0 → P2) with rationale

## P0 — Stabilize the source of truth and remove drift

**Objective**
- Convert “tokens defined” into “tokens consistently used across critical screens and states”.

**Why P0**
- Current risk is not missing colors, but **usage drift** and mixed patterns. Without this, every next UI fix can reintroduce readability regressions.

**Likely files/areas affected**
- `web/js/tailwind-config.js` (token contract stays canonical).
- `web/js/**/*.js`, `web/css/**/*.css`, templates/views for `Лента / Правила / Профиль`.
- Focus checks around component states already touched by #121.

**Expected outcome**
- Critical surfaces are token-first and contrast-stable.
- Legacy/hardcoded color usage is either removed or explicitly tracked for follow-up.

---

## P1 — Make component states and regression checks reproducible

**Objective**
- Standardize visual behavior for `default/hover/active/disabled/loading` and define a repeatable verification process.

**Why P1**
- Once token usage is stabilized, the next instability source is inconsistent interaction states and ad-hoc testing.

**Likely files/areas affected**
- Interactive UI layer (buttons/tabs and shared state styles in `web/css/*`, `web/js/*`, templates).
- Regression artifacts/checklists in `docs/` (desktop/mobile × Chrome/Edge).

**Expected outcome**
- Components behave predictably across screens and browsers.
- Team has a single regression checklist used before merge.

---

## P2 — Institutionalize via documentation and PR discipline

**Objective**
- Encode the rules so future PRs follow them automatically.

**Why P2**
- Documentation amplifies and preserves P0/P1 outcomes but should reflect already-validated implementation.

**Likely files/areas affected**
- `docs/` (Theme Contract + examples + anti-patterns).
- PR process docs/templates (if present) to require contract/checklist references.

**Expected outcome**
- Theme and state consistency becomes an engineering standard, not tribal knowledge.

---

## C) Recommended first implementation step

**First step (strict scope):**
- Run a **token-usage consistency pass on critical surfaces** (`Лента / Правила / Профиль`) and produce a short drift report: where token classes are used vs where legacy/hardcoded values remain.

**Why first**
- It directly converts the current “partially complete” state into actionable deltas, de-risks P1 state work, and avoids broad redesign.

**Done criteria for this first step**
- Each critical surface has a verified status: `token-consistent` / `needs migration`.
- Remaining gaps are prioritized and mapped to P0 follow-up PRs.
