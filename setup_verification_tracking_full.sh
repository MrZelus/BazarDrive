#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="MrZelus/BazarDrive"
ISSUE_TITLE="Verification workflow v1: states, transitions, moderation, audit"
FALLBACK_ISSUE="204"

TMP_BASE="${TMPDIR:-$PREFIX/tmp}"
mkdir -p "$TMP_BASE"

ISSUE_BODY_FILE="$(mktemp "$TMP_BASE/verification_issue.XXXXXX.md")"
PROGRESS_FILE="$(mktemp "$TMP_BASE/progress_comment.XXXXXX.md")"

gh auth status >/dev/null

set_label () {
  local name="$1"
  local color="$2"
  local desc="$3"

  if gh label list -R "$REPO" --json name --jq '.[].name' | grep -Fxq "$name"; then
    echo "✅ label exists: $name"
  else
    gh label create "$name" -R "$REPO" --color "$color" --description "$desc"
    echo "✅ label created: $name"
  fi
}

# 1) Ensure labels
set_label "backend"      "0052CC" "Backend/domain changes"
set_label "frontend"     "C2E0C6" "UI/frontend changes"
set_label "api"          "0E8A16" "API/backend contract changes"
set_label "verification" "1D76DB" "Verification flow and status lifecycle"
set_label "trust"        "5319E7" "Trust badge/rules and related logic"
set_label "process"      "FBCA04" "Process/documentation/coordination work"

# 2) Find existing issue by exact title
EXISTING_ISSUE_NUMBER="$(
  gh issue list -R "$REPO" --state all --limit 200 --json number,title --jq \
  ".[] | select(.title == \"$ISSUE_TITLE\") | .number" | head -n1 || true
)"

# 3) Create issue if missing
if [ -z "${EXISTING_ISSUE_NUMBER:-}" ]; then
  cat > "$ISSUE_BODY_FILE" <<'MD'
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
1. State model: `unverified`, `pending_verification`, `verified`, `rejected`, (optional) `expired`
2. State transitions: submit/approve/reject/resubmit
3. API contract: `verification_state`, rejection reason, decision metadata, history
4. UI behavior: badges/actions for all states, CTA for resubmission from rejected
5. Audit & observability: actor, timestamp, reason, logs/metrics

## Acceptance Criteria
- [ ] State machine enforced server-side
- [ ] Approve/reject endpoints with reason
- [ ] UI parity for all states
- [ ] API + smoke/integration tests for transitions
- [ ] Backward compatibility for legacy payloads

## Out of scope
- New KYC providers
- Major UI redesign
- Legal policy drafting
MD

  CREATED_URL="$(
    gh issue create -R "$REPO" \
      --title "$ISSUE_TITLE" \
      --label "backend" --label "frontend" --label "api" \
      --label "verification" --label "trust" --label "process" \
      --body-file "$ISSUE_BODY_FILE"
  )"

  TRACKING_ISSUE_NUMBER="${CREATED_URL##*/}"
  echo "✅ created issue #$TRACKING_ISSUE_NUMBER"
else
  TRACKING_ISSUE_NUMBER="$EXISTING_ISSUE_NUMBER"
  echo "✅ reusing issue #$TRACKING_ISSUE_NUMBER"
fi

# 4) Build progress comment
cat > "$PROGRESS_FILE" <<MD
### Progress update (auto)

- [x] API/domain state-machine baseline
- [x] UI trust/verification mapping alignment
- [ ] Moderation approve/reject endpoints
- [ ] Rejection reason + resubmission UX
- [ ] Full transition smoke/integration coverage
- [ ] Artifact formalization in PR body/comments

**Linked tasks:** #172 #204 #BAZ-62
**Tracking issue:** #$TRACKING_ISSUE_NUMBER
**Current focus:** moderation endpoints + rejection flow
**ETA to completion:** ~15–25%
MD

# 5) Comment in open PR; fallback to issue
PR_NUMBER="$(gh pr list -R "$REPO" --state open --limit 1 --json number --jq '.[0].number')"

if [ -n "${PR_NUMBER:-}" ] && [ "$PR_NUMBER" != "null" ]; then
  gh pr comment "$PR_NUMBER" -R "$REPO" --body-file "$PROGRESS_FILE"
  echo "✅ posted to PR #$PR_NUMBER"
else
  TARGET_ISSUE="${TRACKING_ISSUE_NUMBER:-$FALLBACK_ISSUE}"
  gh issue comment "$TARGET_ISSUE" -R "$REPO" --body-file "$PROGRESS_FILE"
  echo "✅ no open PR; posted to issue #$TARGET_ISSUE"
fi
