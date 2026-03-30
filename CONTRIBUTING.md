# Contributing to BazarDrive

This file is the canonical repository entrypoint for contribution guidance.

The full contribution guide lives here:
- [docs/contributing.md](docs/contributing.md)

## Quick start

- Read the full guide in `docs/contributing.md` before making non-trivial changes.
- Keep changes in scope and avoid mixing unrelated refactors, UI redesign, API changes, and docs rewrites in one PR.
- Prefer canonical entrypoints for local runs:
  - `run_api.py`
  - `run_bot.py`
- Do not rename already applied migrations.
- Update docs when changing user flows, API contracts, permissions, moderation, or architecture-significant behavior.

## Before opening a PR

- Make sure the changed flow works locally.
- Run relevant tests or smoke checks.
- Document what changed, why it changed, and how it was verified.
- Link the PR to the related issue or epic.

## Community health structure

BazarDrive keeps the extended contributor protocol in `docs/contributing.md` and exposes this root-level `CONTRIBUTING.md` as the standard GitHub community health entrypoint.

If these files diverge, update both intentionally or use the repository workflow checks to restore consistency.
