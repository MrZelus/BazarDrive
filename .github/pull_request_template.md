## Summary
- What changed and why (brief).

## Epic linkage
- [ ] This PR is in Epic #126 scope (theme tokens, contrast/readability, component states, regression process, Theme Contract docs).
- Required issue linkage:
  - Intermediate PRs: `Part of #126`
  - Final closure PR only when all epic criteria are met: `Closes #126`
- Link(s):

## Theme Contract compliance (required for UI PRs)
- [ ] Reviewed `docs/theme-contract.md` and aligned changes with allowed tokens/states.
- [ ] No ad-hoc color drift introduced (`white/*`, `text-white`, `text-black`, `bg-black`, raw `#hex`, raw `rgba(...)`) unless explicitly justified and approved.
- [ ] Component states covered where applicable: `default / hover / active / disabled / loading`.

## Visual regression checklist evidence (required for UI PRs)
Target surfaces: `Лента / Правила / Профиль`

- [ ] Desktop Chrome checked
- [ ] Desktop Edge checked
- [ ] Mobile Chrome (emulation/device) checked
- [ ] Mobile Edge (emulation/device) checked

Evidence links (screenshots/report):
- Before:
- After:
- Runbook/report:

## Verification
- Test plan:
- Commands run:
- Results:

## Scope control
- [ ] No redesign work
- [ ] No Tailwind CLI/PostCSS migration
- [ ] No API/business-logic changes
- [ ] Any out-of-scope requests were deferred or split into a separate issue

## Risks / rollback
- Risks:
- Rollback plan:
