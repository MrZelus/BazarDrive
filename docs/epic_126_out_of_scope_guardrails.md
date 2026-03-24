# Epic #126 — Out-of-scope guardrails

## A) Guardrails summary

Use out-of-scope items as delivery constraints to protect Epic #126 goals (theme-token consistency, component-state consistency, visual regression process, Theme Contract docs).

- **Reject in this epic PR** any changes that alter API contracts, backend behavior, or business rules. They do not improve UI foundation directly and add cross-team risk.
- **Defer in-epic** any broad UI redesign intent (new information architecture, new visual language, layout overhauls). Keep only targeted readability/contrast/state fixes tied to existing UX.
- **Split into separate issue** any Tailwind CLI/PostCSS migration work. It may be valuable later, but it is infrastructure scope and must not block P0/P1 UI stabilization.

**Prioritization & sequencing impact:**
1. Start with **P0 in-scope fixes** (token consistency on current screens) without waiting on tooling migration.
2. Continue with **P1 state consistency + visual regression checklist** on the existing stack.
3. Finalize **P2 Theme Contract docs** once implementation patterns are stable.
4. Route redesign/toolchain/API ideas out of the epic path to avoid scope creep and timeline slip.

---

## B) Rule table (item → handling policy)

| Out-of-scope item | Handling policy | Practical rule in review |
|---|---|---|
| Полный редизайн UI | **Defer until epic completion** | If PR changes IA/layout/style direction beyond contrast/state/token fixes, request trim and move redesign proposals to post-epic backlog. |
| Миграция на Tailwind CLI/PostCSS | **Split into separate issue** | If PR introduces build-pipeline migration files/config changes, stop and require a dedicated infra issue/PR chain. |
| Изменения API/бизнес-логики | **Reject in current PR** | If PR changes endpoints, payload contracts, domain rules, or backend behavior, reject as out-of-scope for #126. |

---

## C) Reviewer checklist — “Is this PR still in scope?”

- Does every change directly support tokens, component states, visual regression process, or Theme Contract docs?
- Are there **no** API/business-logic deltas in code or contracts?
- Are there **no** Tailwind CLI/PostCSS migration changes mixed into this PR?
- Is UI change limited to consistency/readability/state behavior (not a redesign)?
- If anything out-of-scope appears, is it explicitly tagged as **defer** or moved to a **separate issue**?

If any answer is “no”, mark PR as out-of-scope and request scope correction before approval.
