#!/usr/bin/env bash
set -euo pipefail

REPO="MrZelus/BazarDrive"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Не найдено: $1"
    exit 1
  }
}

need_cmd gh
need_cmd python
need_cmd grep
need_cmd awk
need_cmd mktemp

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Проверка GitHub auth"
gh auth status >/dev/null

issue_number_by_title() {
  local title="$1"
  local raw
  raw="$(gh issue list --repo "$REPO" --state all --limit 300 --search "in:title \"$title\"" --json number,title 2>/dev/null || true)"
  if [[ -z "${raw:-}" ]]; then
    return 0
  fi

  RAW_JSON="$raw" TARGET_TITLE="$title" python - <<'PY'
import json, os

raw = os.environ.get("RAW_JSON", "")
title = os.environ.get("TARGET_TITLE", "")

try:
    items = json.loads(raw)
except Exception:
    items = []

for item in items:
    if item.get("title") == title:
        print(item.get("number"))
        break
PY
}

issue_exists() {
  local title="$1"
  [[ -n "$(issue_number_by_title "$title" || true)" ]]
}

milestone_number_by_title() {
  local title="$1"
  local raw
  raw="$(gh api --paginate "repos/$REPO/milestones?state=all&per_page=100" 2>/dev/null || true)"
  if [[ -z "${raw:-}" ]]; then
    return 0
  fi

  RAW_JSON="$raw" TARGET_TITLE="$title" python - <<'PY'
import json, os

raw = os.environ.get("RAW_JSON", "")
title = os.environ.get("TARGET_TITLE", "")

try:
    items = json.loads(raw)
except Exception:
    items = []

for item in items:
    if item.get("title") == title:
        print(item.get("number"))
        break
PY
}

create_milestone_if_missing() {
  local title="$1"
  local desc="$2"
  local due_on="$3"

  local number
  number="$(milestone_number_by_title "$title" || true)"
  if [[ -n "${number:-}" ]]; then
    echo "Milestone exists: $title (#$number)"
  else
    echo "Creating milestone: $title"
    gh api "repos/$REPO/milestones" \
      --method POST \
      -f title="$title" \
      -f description="$desc" \
      -f due_on="$due_on" >/dev/null
  fi
}

assign_issue_to_milestone() {
  local issue_number="$1"
  local milestone_number="$2"
  gh api "repos/$REPO/issues/$issue_number" \
    --method PATCH \
    -f milestone="$milestone_number" >/dev/null
}

create_label_if_missing() {
  local name="$1"
  local color="$2"
  local desc="$3"

  if gh label list --repo "$REPO" --limit 300 | awk '{print $1}' | grep -Fxq "$name"; then
    echo "Label exists: $name"
  else
    echo "Creating label: $name"
    gh label create "$name" \
      --repo "$REPO" \
      --color "$color" \
      --description "$desc"
  fi
}

create_issue_if_missing() {
  local title="$1"
  local labels_csv="$2"
  local body_file="$3"

  if issue_exists "$title"; then
    echo "Issue exists: $title (#$(issue_number_by_title "$title"))"
  else
    echo "Creating issue: $title"
    local args=()
    IFS=',' read -r -a labels <<< "$labels_csv"
    for label in "${labels[@]}"; do
      args+=(--label "$label")
    done

    gh issue create \
      --repo "$REPO" \
      --title "$title" \
      "${args[@]}" \
      --body-file "$body_file" >/dev/null
  fi
}

update_issue_body() {
  local number="$1"
  local body_file="$2"
  gh issue edit "$number" --repo "$REPO" --body-file "$body_file" >/dev/null
}

comment_exists_with_marker() {
  local issue_number="$1"
  local marker="$2"
  gh issue view "$issue_number" --repo "$REPO" --comments | grep -Fq "$marker"
}

post_comment_if_missing() {
  local issue_number="$1"
  local comment_file="$2"
  local marker="$3"

  if comment_exists_with_marker "$issue_number" "$marker"; then
    echo "Summary comment already exists on #$issue_number"
  else
    echo "Posting summary comment to #$issue_number"
    gh issue comment "$issue_number" --repo "$REPO" --body-file "$comment_file" >/dev/null
  fi
}

print_issue_status() {
  local title="$1"
  local num
  num="$(issue_number_by_title "$title" || true)"
  if [[ -n "${num:-}" ]]; then
    echo "FOUND: $title (#$num)"
  else
    echo "MISS : $title"
  fi
}

echo
echo "==> Текущий статус ключевых epic"
print_issue_status "[EPIC][MVP] Driver Readiness Platform"
print_issue_status "[EPIC][MVP] Orders Marketplace Core"
print_issue_status "[EPIC][MVP] Feed Public Presence MVP"

echo
echo "==> Создание базовых label для Feed Public Presence"
create_label_if_missing "epic" "5319E7" "Top-level epic"
create_label_if_missing "mvp" "B60205" "Minimum viable scope"
create_label_if_missing "frontend" "1D76DB" "Frontend work"
create_label_if_missing "backend" "0E8A16" "Backend work"
create_label_if_missing "ux" "FBCA04" "UX and product flow"
create_label_if_missing "api" "0052CC" "API and contracts"
create_label_if_missing "feed" "BFDADC" "Feed and public presence"
create_label_if_missing "media" "C2E0C6" "Media attachments"
create_label_if_missing "moderation" "F9D0C4" "Moderation and publish checks"
create_label_if_missing "design-system" "FEF2C0" "Design system and UI consistency"

echo
echo "==> Feed Public Presence package"
FEED_EPIC_TITLE="[EPIC][MVP] Feed Public Presence MVP"
FEED_MILESTONE_TITLE="Feed Public Presence MVP"
FEED_MILESTONE_DESC="MVP scope for feed posting, post cards, moderation-aware publish flow, media attach, contracts, and feed shell UX."
FEED_MILESTONE_DUE="2026-06-30T23:59:59Z"

if issue_exists "$FEED_EPIC_TITLE"; then
  echo "Feed epic already exists (#$(issue_number_by_title "$FEED_EPIC_TITLE"))"
else
  echo "Feed epic missing. Creating full Feed Public Presence MVP package."

  create_milestone_if_missing "$FEED_MILESTONE_TITLE" "$FEED_MILESTONE_DESC" "$FEED_MILESTONE_DUE"
  FEED_MILESTONE_NUM="$(milestone_number_by_title "$FEED_MILESTONE_TITLE")"

  cat > "$TMP_DIR/epic_feed_initial.md" <<'EOF2'
## Epic: Feed Public Presence MVP

### Goal
Ship the missing MVP layer for public posting and feed presentation without duplicating existing publication profile and engagement epics.

### Why
The product already has publication-profile and engagement directions, but still needs a focused MVP shell for:
- post creation
- post rendering
- moderation-aware publish flow
- media attachment
- stable contracts for publish/read
- feed shell states

### Scope
- create post flow
- post card rendering
- approved/public feed stream
- moderation-aware publish states
- image attach for posts
- feed API contract sync
- loading / empty / error states

### Out of scope
- role matrix and publication profile UX
- reactions, comments, search, filters, pagination, infinite scroll
EOF2

  cat > "$TMP_DIR/sub_posting_initial.md" <<'EOF2'
## Sub-epic: Feed Posting

### Goal
Build the create-post flow for public feed publishing.

### Scope
- post composer
- text validation
- publish CTA
- confirmation / feedback
- moderation-aware submission states
EOF2

  cat > "$TMP_DIR/sub_stream_initial.md" <<'EOF2'
## Sub-epic: Post Cards and Feed Stream

### Goal
Build the feed shell that renders approved posts cleanly and predictably.

### Scope
- post card
- author / time / text layout
- media slot
- approved feed list
- empty and loading feed states
EOF2

  cat > "$TMP_DIR/sub_moderation_initial.md" <<'EOF2'
## Sub-epic: Publish Moderation Flow

### Goal
Make the publish flow robust when moderation, validation, or anti-spam rules affect posting.

### Scope
- moderation-aware messaging
- validation failures
- spam / retry feedback
- publish result states
EOF2

  cat > "$TMP_DIR/sub_contracts_initial.md" <<'EOF2'
## Sub-epic: Feed Publish and Read Contracts

### Goal
Stabilize frontend/backend contracts for create-post and feed-read operations.

### Scope
- create post request / response
- approved feed response
- media payload rules
- moderation result payload
- contract tests
EOF2

  cat > "$TMP_DIR/issue_composer_initial.md" <<'EOF2'
## Goal
Build the feed post composer and publish CTA flow.

### Tasks
- text input
- validation
- submit CTA
- success feedback
- reset after successful publish
EOF2

  cat > "$TMP_DIR/issue_cards_initial.md" <<'EOF2'
## Goal
Build feed post cards for approved posts.

### Tasks
- author label
- timestamp
- text content
- media slot
- safe text rendering
EOF2

  cat > "$TMP_DIR/issue_media_initial.md" <<'EOF2'
## Goal
Add one-image media attachment to feed publishing.

### Tasks
- file input
- client-side validation
- send image with post publish request
- preview / clear flow
EOF2

  cat > "$TMP_DIR/issue_mod_states_initial.md" <<'EOF2'
## Goal
Add human-friendly moderation-aware states to the publish flow.

### Tasks
- validation errors
- moderation feedback
- anti-spam / retry messaging
- publish pending / rejected / accepted copy
EOF2

  cat > "$TMP_DIR/issue_contracts_initial.md" <<'EOF2'
## Goal
Define and sync contracts for feed publish and approved feed read.

### Tasks
- create post contract
- approved feed response contract
- media field contract
- moderation result contract
- docs/test sync
EOF2

  cat > "$TMP_DIR/issue_shell_states_initial.md" <<'EOF2'
## Goal
Add clean loading, empty, and error states for the feed shell.

### Tasks
- loading skeleton
- no posts state
- retry state
- human-friendly fetch errors
EOF2

  cat > "$TMP_DIR/issue_tests_initial.md" <<'EOF2'
## Goal
Cover Feed Public Presence MVP with smoke and contract tests.

### Tasks
- publish text-only post test
- publish post with image test
- approved feed render test
- moderation/validation state test
- feed contract tests
EOF2

  create_issue_if_missing "[EPIC][MVP] Feed Public Presence MVP" "epic,mvp,feed" "$TMP_DIR/epic_feed_initial.md"
  create_issue_if_missing "[SUB-EPIC][MVP] Feed Posting" "epic,mvp,feed,frontend,ux" "$TMP_DIR/sub_posting_initial.md"
  create_issue_if_missing "[SUB-EPIC][MVP] Post Cards and Feed Stream" "epic,mvp,feed,frontend,ux" "$TMP_DIR/sub_stream_initial.md"
  create_issue_if_missing "[SUB-EPIC][MVP] Publish Moderation Flow" "epic,mvp,feed,moderation,ux" "$TMP_DIR/sub_moderation_initial.md"
  create_issue_if_missing "[SUB-EPIC][MVP] Feed Publish and Read Contracts" "epic,mvp,feed,backend,api" "$TMP_DIR/sub_contracts_initial.md"

  create_issue_if_missing "[MVP] Build feed post composer and publish CTA flow" "mvp,feed,frontend,ux" "$TMP_DIR/issue_composer_initial.md"
  create_issue_if_missing "[MVP] Build approved feed post cards with safe rendering" "mvp,feed,frontend,ux" "$TMP_DIR/issue_cards_initial.md"
  create_issue_if_missing "[MVP] Add one-image media attachment for feed posts" "mvp,feed,frontend,backend,media" "$TMP_DIR/issue_media_initial.md"
  create_issue_if_missing "[MVP] Add moderation-aware publish states and copy" "mvp,feed,moderation,frontend,ux" "$TMP_DIR/issue_mod_states_initial.md"
  create_issue_if_missing "[MVP] Define feed publish/read contracts and media payload rules" "mvp,feed,backend,api" "$TMP_DIR/issue_contracts_initial.md"
  create_issue_if_missing "[MVP] Add loading, empty, and error states for feed shell" "mvp,feed,frontend,ux,design-system" "$TMP_DIR/issue_shell_states_initial.md"
  create_issue_if_missing "[MVP] Cover feed public presence with smoke and contract tests" "mvp,feed,backend,frontend,api" "$TMP_DIR/issue_tests_initial.md"

  FEED_EPIC_NUM="$(issue_number_by_title "[EPIC][MVP] Feed Public Presence MVP")"
  SUB_POSTING_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Feed Posting")"
  SUB_STREAM_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Post Cards and Feed Stream")"
  SUB_MODERATION_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Publish Moderation Flow")"
  SUB_CONTRACTS_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Feed Publish and Read Contracts")"

  ISSUE_COMPOSER_NUM="$(issue_number_by_title "[MVP] Build feed post composer and publish CTA flow")"
  ISSUE_CARDS_NUM="$(issue_number_by_title "[MVP] Build approved feed post cards with safe rendering")"
  ISSUE_MEDIA_NUM="$(issue_number_by_title "[MVP] Add one-image media attachment for feed posts")"
  ISSUE_MOD_STATES_NUM="$(issue_number_by_title "[MVP] Add moderation-aware publish states and copy")"
  ISSUE_CONTRACTS_NUM="$(issue_number_by_title "[MVP] Define feed publish/read contracts and media payload rules")"
  ISSUE_SHELL_STATES_NUM="$(issue_number_by_title "[MVP] Add loading, empty, and error states for feed shell")"
  ISSUE_TESTS_NUM="$(issue_number_by_title "[MVP] Cover feed public presence with smoke and contract tests")"

  for num in \
    "$FEED_EPIC_NUM" \
    "$SUB_POSTING_NUM" \
    "$SUB_STREAM_NUM" \
    "$SUB_MODERATION_NUM" \
    "$SUB_CONTRACTS_NUM" \
    "$ISSUE_COMPOSER_NUM" \
    "$ISSUE_CARDS_NUM" \
    "$ISSUE_MEDIA_NUM" \
    "$ISSUE_MOD_STATES_NUM" \
    "$ISSUE_CONTRACTS_NUM" \
    "$ISSUE_SHELL_STATES_NUM" \
    "$ISSUE_TESTS_NUM"
  do
    assign_issue_to_milestone "$num" "$FEED_MILESTONE_NUM"
  done

  cat > "$TMP_DIR/epic_feed_final.md" <<EOF2
## Epic: Feed Public Presence MVP

### Milestone
- $FEED_MILESTONE_TITLE

### Goal
Ship the missing MVP layer for public posting and feed presentation without duplicating existing publication profile and engagement epics.

### Scope
- create post flow
- post card rendering
- approved/public feed stream
- moderation-aware publish states
- image attach for posts
- feed API contract sync
- loading / empty / error states

### Out of scope
- publication profile role matrix and role UX
- reactions, comments, search, filters, pagination, infinite scroll

### Children
- #$SUB_POSTING_NUM Feed Posting
- #$SUB_STREAM_NUM Post Cards and Feed Stream
- #$SUB_MODERATION_NUM Publish Moderation Flow
- #$SUB_CONTRACTS_NUM Feed Publish and Read Contracts

### MVP delivery path
1. #$ISSUE_CONTRACTS_NUM Feed publish/read contracts
2. #$ISSUE_COMPOSER_NUM Post composer and publish CTA
3. #$ISSUE_CARDS_NUM Approved feed post cards
4. #$ISSUE_MEDIA_NUM One-image media attachment
5. #$ISSUE_MOD_STATES_NUM Moderation-aware publish states
6. #$ISSUE_SHELL_STATES_NUM Feed shell states
7. #$ISSUE_TESTS_NUM Smoke and contract tests
EOF2

  update_issue_body "$FEED_EPIC_NUM" "$TMP_DIR/epic_feed_final.md"

  EPIC_COMMENT_MARKER="<!-- feed-public-presence-mvp-summary -->"
  cat > "$TMP_DIR/epic_comment.md" <<EOF2
$EPIC_COMMENT_MARKER

## Feed Public Presence MVP summary

### Milestone
- **$FEED_MILESTONE_TITLE**

### Created hierarchy
- Epic: #$FEED_EPIC_NUM
- Feed Posting: #$SUB_POSTING_NUM
- Post Cards and Feed Stream: #$SUB_STREAM_NUM
- Publish Moderation Flow: #$SUB_MODERATION_NUM
- Feed Publish and Read Contracts: #$SUB_CONTRACTS_NUM

### MVP issues
- #$ISSUE_COMPOSER_NUM post composer
- #$ISSUE_CARDS_NUM approved post cards
- #$ISSUE_MEDIA_NUM media attachment
- #$ISSUE_MOD_STATES_NUM moderation-aware states
- #$ISSUE_CONTRACTS_NUM contracts
- #$ISSUE_SHELL_STATES_NUM shell states
- #$ISSUE_TESTS_NUM tests

### Notes
- This package is intentionally separate from publication profile role UX and feed engagement work.
EOF2

  post_comment_if_missing "$FEED_EPIC_NUM" "$TMP_DIR/epic_comment.md" "$EPIC_COMMENT_MARKER"
fi

echo
echo "==> Итоговая сводка"
print_issue_status "[EPIC][MVP] Driver Readiness Platform"
print_issue_status "[EPIC][MVP] Orders Marketplace Core"
print_issue_status "[EPIC][MVP] Feed Public Presence MVP"

echo
echo "Milestones:"
echo "Driver Readiness MVP: https://github.com/$REPO/milestones"
echo "Orders Marketplace Core MVP: https://github.com/$REPO/milestones"
echo "Feed Public Presence MVP: https://github.com/$REPO/milestones"

echo
echo "Issues: https://github.com/$REPO/issues"
