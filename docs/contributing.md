# Contributing Guide (UI Foundation #126)

This project uses a scope-first contribution protocol for Epic **#126** (UI Foundation — theme and contrast system hardening).

## 1) Required linkage for Epic #126

- Use `Part of #126` for all intermediate PRs.
- Use `Closes #126` only in the final closure PR, and only when all Epic acceptance criteria and DoD gates are satisfied.

## 2) UI PR requirements (merge-blocking for #126 scope)

For any PR touching UI surfaces (`Лента / Правила / Профиль`):

1. **Theme Contract conformance**
   - Follow `docs/theme-contract.md`.
   - Use canonical theme tokens.
   - Do not introduce drift patterns (`white/*`, `text-white`, `text-black`, `bg-black`, raw `#hex`, raw `rgba(...)`) unless explicitly approved.

2. **State consistency**
   - Validate `default / hover / active / disabled / loading` where applicable.
   - Ensure keyboard focus remains visible (`:focus-visible`) and loading/disabled states remain readable.

3. **Visual regression evidence**
   - Run the regression matrix (desktop/mobile × Chrome/Edge).
   - Attach evidence via report and screenshots (or note environment limitation).

## 3) Scope guardrails

In Epic #126 PRs, reject or split out:
- Full redesign requests,
- Tailwind CLI/PostCSS migration,
- API/business-logic changes.

If required, open a separate issue and keep current PR in scope.

## 4) Status update protocol for #126

After opening/updating each subtask PR:

1. Update checklist state in #126 (`todo → in progress → done`).
2. Post a status comment to #126 with:
   - PR link,
   - commit SHA,
   - implemented scope,
   - verification summary (desktop/mobile, Chrome/Edge),
   - deferred items/risks.
3. End with `Next: <subtask title>`.
