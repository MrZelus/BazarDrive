#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="MrZelus/BazarDrive"
TRACKING_ISSUE_NUMBER="204"   # если хочешь фолбэк-комменты в существующую задачу

echo "==> Проверка авторизации gh"
gh auth status >/dev/null

echo "==> Создаю issue body"
cat > /tmp/verification_workflow_issue.md <<'MD'
## Context
Post-#172/#204 hardening covered status normalization and UI trust mapping.
Need full verification workflow (business process), not only status rendering.

## Linked work
- Related: #172
- Related: #204
- Related: #BAZ-62

## Goal
Implement end-to-end verification workflow v1 with clear state machine, moderation actions, rejection reasons, and audit trail.

## Scope
1. State model:
   - `unverified`
   - `pending_verification`
   - `verified`
   - `rejected`
   - (optional) `expired`
2. State transitions:
   - user submit -> pending
   - moderator approve -> verified
   - moderator reject -> rejected (+reason)
   - resubmit flow from rejected
3. API contract:
   - explicit `verification_state`
   - rejection_reason / decision metadata
   - history endpoint (or embedded timeline)
4. UI behavior:
   - badges/text/actions per state
   - rejected state CTA for resubmission
5. Audit & observability:
   - who changed state, when, why
   - structured logs + basic metrics

## Acceptance Criteria
- [ ] State machine documented and enforced server-side.
- [ ] Moderation endpoints support approve/reject with reason.
- [ ] UI reflects all states and actions consistently.
- [ ] Tests: API + smoke/integration for transitions.
- [ ] Backward compatibility: old payloads still normalized safely.

## Implementation plan
### Phase 1 (API/domain)
- Add canonical state constants and transition guard.
- Add moderation decision model (reason, actor, timestamp).
- Add/update endpoints and response schema.

### Phase 2 (UI)
- Extend trust/verification rendering for `rejected` (+reason).
- Add resubmission UX.
- Keep current badge taxonomy unless separately approved.

### Phase 3 (Quality)
- Extend smoke tests for full transition path.
- Add regression checks for fallback normalization.
- Add artifacts section in PR description.

## Out of scope
- New KYC provider integrations
- Major redesign of profile UI
- Legal policy drafting
MD

echo "==> Создаю tracking issue (если не нужна — закомментируй блок)"
gh issue create -R "$REPO" \
  --title "Verification workflow v1: states, transitions, moderation, audit" \
  --label "backend" \
  --label "frontend" \
  --label "api" \
  --label "verification" \
  --label "trust" \
  --label "process" \
  --body-file /tmp/verification_workflow_issue.md || true

echo "==> Создаю progress-comment.md"
cat > progress-comment.md <<'MD'
### Progress update (auto)

- [x] API/domain state-machine baseline
- [x] UI trust/verification mapping alignment
- [ ] Moderation approve/reject endpoints
- [ ] Rejection reason + resubmission UX
- [ ] Full transition smoke/integration coverage
- [ ] Artifact formalization in PR body/comments

**Linked tasks:** #172 #204 #BAZ-62
**Current focus:** moderation endpoints + rejection flow
**ETA to completion:** ~15–25%
MD

echo "==> Пытаюсь найти открытый PR"
PR_NUMBER="$(gh pr list -R "$REPO" --state open --limit 1 --json number --jq '.[0].number')"

if [ -n "${PR_NUMBER:-}" ] && [ "$PR_NUMBER" != "null" ]; then
  gh pr comment "$PR_NUMBER" -R "$REPO" --body-file progress-comment.md
  echo "✅ Posted progress update to PR #$PR_NUMBER"
else
  gh issue comment "$TRACKING_ISSUE_NUMBER" -R "$REPO" --body-file progress-comment.md
  echo "✅ No open PR; posted update to issue #$TRACKING_ISSUE_NUMBER"
fi

echo "==> Готово"
