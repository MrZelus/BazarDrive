#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="MrZelus/BazarDrive"
TMP_BODY="$(mktemp)"

cat > "$TMP_BODY" <<'MD'
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

PR_NUMBER="$(gh pr list -R "$REPO" --state open --limit 1 --json number -q '.[0].number')"
gh pr comment "$PR_NUMBER" -R "$REPO" --body-file "$TMP_BODY"

echo "Posted progress update to PR #$PR_NUMBER"
