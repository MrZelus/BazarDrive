#!/usr/bin/env bash
set -euo pipefail

# Termux-ready bootstrap script that:
# 1) Ensures labels exist
# 2) Creates (or reuses) milestone Driver Readiness MVP
# 3) Creates Epic/Sub-epic/MVP issues (if missing)
# 4) Assigns all issues to the milestone
# 5) Rewrites issue bodies with Parent/Children/Related links
# 6) Posts one summary comment in the Epic (idempotent via marker)

DEFAULT_REPO="MrZelus/BazarDrive"
REPO="${1:-${REPO:-$DEFAULT_REPO}}"
MILESTONE_TITLE="Driver Readiness MVP"
MILESTONE_DESC="MVP scope for driver onboarding, readiness, documents, and business identity."
MILESTONE_DUE="2026-05-31T23:59:59Z"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Не найдено: $1" >&2
    exit 1
  }
}

need_cmd gh
need_cmd mktemp

echo "==> Проверка авторизации GitHub"
if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI не авторизован. Выполните: gh auth login" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

create_label_if_missing() {
  local name="$1"
  local color="$2"
  local desc="$3"

  if gh label list --repo "$REPO" --limit 200 --json name --jq '.[].name' | grep -Fxq "$name"; then
    echo "Label exists: $name"
  else
    echo "Creating label: $name"
    gh label create "$name" --repo "$REPO" --color "$color" --description "$desc"
  fi
}

milestone_number_by_title() {
  local title="$1"
  gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title == \"$title\") | .number" | head -n 1
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
    gh api "repos/$REPO/milestones" --method POST -f title="$title" -f description="$desc" -f due_on="$due_on" >/dev/null
  fi
}

issue_number_by_title() {
  local title="$1"
  gh issue list \
    --repo "$REPO" \
    --state all \
    --limit 200 \
    --search "in:title \"$title\"" \
    --json number,title \
    --jq "map(select(.title == \"$title\")) | .[0].number // \"\""
}

issue_exists() {
  local title="$1"
  [[ -n "$(issue_number_by_title "$title")" ]]
}

create_issue_if_missing() {
  local title="$1"
  local labels_csv="$2"
  local body_file="$3"

  if issue_exists "$title"; then
    echo "Issue exists: $title (#$(issue_number_by_title "$title"))"
    return 0
  fi

  local args=()
  local labels
  IFS=',' read -r -a labels <<< "$labels_csv"
  local label
  for label in "${labels[@]}"; do
    args+=(--label "$label")
  done

  echo "Creating issue: $title"
  gh issue create --repo "$REPO" --title "$title" "${args[@]}" --body-file "$body_file" >/dev/null
}

assign_issue_to_milestone() {
  local issue_number="$1"
  local milestone_title="$2"

  echo "Assigning issue #$issue_number to milestone '$milestone_title'"
  gh issue edit "$issue_number" --repo "$REPO" --milestone "$milestone_title" >/dev/null
}

update_issue_body() {
  local number="$1"
  local body_file="$2"

  echo "Updating issue #$number"
  gh issue edit "$number" --repo "$REPO" --body-file "$body_file" >/dev/null
}

comment_exists_with_marker() {
  local issue_number="$1"
  local marker="$2"

  gh issue view "$issue_number" --repo "$REPO" --json comments --jq '.comments[].body' | grep -Fq "$marker"
}

post_comment_if_missing() {
  local issue_number="$1"
  local comment_file="$2"
  local marker="$3"

  if comment_exists_with_marker "$issue_number" "$marker"; then
    echo "Epic summary comment already exists on #$issue_number"
  else
    echo "Posting summary comment to #$issue_number"
    gh issue comment "$issue_number" --repo "$REPO" --body-file "$comment_file" >/dev/null
  fi
}

echo "==> Создание лейблов"
create_label_if_missing "epic" "5319E7" "Top-level epic"
create_label_if_missing "mvp" "B60205" "Minimum viable scope"
create_label_if_missing "frontend" "1D76DB" "Frontend work"
create_label_if_missing "backend" "0E8A16" "Backend work"
create_label_if_missing "ux" "FBCA04" "UX and product flow"
create_label_if_missing "api" "0052CC" "API and contracts"
create_label_if_missing "documents" "C5DEF5" "Documents and compliance"
create_label_if_missing "driver" "D4C5F9" "Driver-related functionality"
create_label_if_missing "readiness" "F9D0C4" "Readiness and blocking logic"
create_label_if_missing "orders" "BFDADC" "Orders workflow"
create_label_if_missing "design-system" "FEF2C0" "Design system and UI consistency"
create_label_if_missing "analytics" "006B75" "Metrics and observability"
create_label_if_missing "backoffice" "E4E669" "Admin and review tooling"

echo "==> Создание milestone"
create_milestone_if_missing "$MILESTONE_TITLE" "$MILESTONE_DESC" "$MILESTONE_DUE"
MILESTONE_NUM="$(milestone_number_by_title "$MILESTONE_TITLE")"
if [[ -z "$MILESTONE_NUM" ]]; then
  echo "Ошибка: не удалось определить milestone '$MILESTONE_TITLE'" >&2
  exit 1
fi
echo "Milestone: #$MILESTONE_NUM"

echo "==> Шаг 1. Базовые issue"

cat > "$TMP_DIR/epic_driver_readiness_initial.md" <<'EOF1'
## Epic: Driver Readiness Platform

### Goal
Bring a driver from first entry to `Ready for orders` through profile completion, document upload, readiness validation, and compliance checks.

### Why
The current driver experience needs a clearer path from incomplete profile to operational readiness. The platform should make it obvious:
- whether the driver is allowed to work
- what is missing
- what the next action is
- how documents and business identity affect readiness

### Scope
- driver profile and onboarding
- readiness summary
- blocking reasons
- driver documents
- active waybill priority
- Taxi / IP business identity
- going online prerequisites
- frontend/backend contract sync
EOF1

cat > "$TMP_DIR/subepic_driver_onboarding_initial.md" <<'EOF1'
## Sub-epic: Driver Profile and Onboarding

### Goal
Build the mobile-first driver profile flow from role selection to readiness summary.

### Scope
- role selection
- basic profile
- driver-specific fields
- hero summary block
- readiness status card
- progress / checklist
- next-step CTA
- empty / loading / error states
EOF1

cat > "$TMP_DIR/subepic_driver_documents_initial.md" <<'EOF1'
## Sub-epic: Driver Documents and Compliance

### Goal
Turn driver documents into a full compliance lifecycle, not just a file list.

### Scope
- upload and reupload
- pending / approved / rejected states
- review comments
- expiry tracking
- active waybill priority
- required documents visibility
- compliance-related blocking reasons
EOF1

cat > "$TMP_DIR/subepic_readiness_contracts_initial.md" <<'EOF1'
## Sub-epic: Readiness Contracts and Validation

### Goal
Define a stable server-side contract for driver readiness and blocking reasons.

### Scope
- readiness summary API
- blocking reasons schema
- progress counters
- allowed actions
- next-step guidance
- validation rules
- contract tests
EOF1

cat > "$TMP_DIR/issue_hero_initial.md" <<'EOF1'
## Goal
Create a strong hero summary and status block for the driver profile screen.

### Tasks
- add hero-card with display name / role / business type / tax regime / progress
- add readiness status-card with status, reason, and next step
- keep one main CTA in the visible viewport
EOF1

cat > "$TMP_DIR/issue_checklist_initial.md" <<'EOF1'
## Goal
Show required profile fields as a checklist and navigate users directly to missing sections.

### Tasks
- add checklist for required fields
- mark complete vs missing items
- deep-link missing items to the correct section
- sync checklist with server readiness summary
EOF1

cat > "$TMP_DIR/issue_documents_initial.md" <<'EOF1'
## Goal
Redesign the documents section so active operational documents are prioritized.

### Tasks
- surface active waybill first
- group docs by state: required / pending / approved / archive
- show status, expiry, and review comment
- support reupload flow
EOF1

cat > "$TMP_DIR/issue_readiness_api_initial.md" <<'EOF1'
## Goal
Provide a backend API for readiness summary and actionable blocking reasons.

### Tasks
- implement readiness summary response
- implement blocking reasons schema
- return progress counters
- return next_step and allowed_actions
- cover with contract tests
EOF1

cat > "$TMP_DIR/issue_document_enums_initial.md" <<'EOF1'
## Goal
Unify document enums and lifecycle rules across the system.

### Tasks
- define DocumentType enum
- define DocumentStatus enum
- support review_comment and expires_at
- enforce single active waybill
- support rejected -> reupload flow
EOF1

cat > "$TMP_DIR/issue_taxi_ip_initial.md" <<'EOF1'
## Goal
Add the Taxi / IP section as part of readiness-critical profile data.

### Tasks
- add business type, INN, OGRNIP, tax regime, region, vehicle
- validate identifiers
- link section to readiness pipeline
EOF1

cat > "$TMP_DIR/issue_states_initial.md" <<'EOF1'
## Goal
Replace raw technical states with reusable user-friendly UI states.

### Tasks
- remove raw messages like `Failed to fetch`
- add loading skeletons
- add empty states with next-step CTA
- add retry state
- add pending review state
EOF1

cat > "$TMP_DIR/issue_tests_initial.md" <<'EOF1'
## Goal
Protect the new driver onboarding and readiness flow with tests.

### Tasks
- smoke test empty profile
- smoke test partial profile
- smoke test ready profile
- smoke test error state
- contract test readiness summary
- contract test blocking reasons
- contract test document lifecycle
- test active waybill uniqueness
EOF1

create_issue_if_missing "[EPIC][MVP] Driver Readiness Platform" "epic,mvp,driver,readiness" "$TMP_DIR/epic_driver_readiness_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Profile and Onboarding" "epic,mvp,driver,ux,frontend" "$TMP_DIR/subepic_driver_onboarding_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Documents and Compliance" "epic,mvp,driver,documents,backend,frontend" "$TMP_DIR/subepic_driver_documents_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Readiness Contracts and Validation" "epic,mvp,api,backend,readiness" "$TMP_DIR/subepic_readiness_contracts_initial.md"
create_issue_if_missing "[MVP] Refactor driver profile hero and readiness summary" "mvp,frontend,ux,driver,readiness" "$TMP_DIR/issue_hero_initial.md"
create_issue_if_missing "[MVP] Implement driver checklist with blocking navigation" "mvp,frontend,ux,driver" "$TMP_DIR/issue_checklist_initial.md"
create_issue_if_missing "[MVP] Rework documents section with active waybill priority" "mvp,frontend,backend,documents,driver" "$TMP_DIR/issue_documents_initial.md"
create_issue_if_missing "[MVP] Add readiness summary API and blocking reasons contract" "mvp,backend,api,readiness" "$TMP_DIR/issue_readiness_api_initial.md"
create_issue_if_missing "[MVP] Normalize driver document lifecycle enums" "mvp,backend,api,documents" "$TMP_DIR/issue_document_enums_initial.md"
create_issue_if_missing "[MVP] Implement Taxi / IP business profile section" "mvp,frontend,backend,api,driver" "$TMP_DIR/issue_taxi_ip_initial.md"
create_issue_if_missing "[MVP] Add human-friendly empty, loading, pending, and error states" "mvp,frontend,ux,design-system" "$TMP_DIR/issue_states_initial.md"
create_issue_if_missing "[MVP] Cover driver onboarding with smoke and contract tests" "mvp,backend,frontend,api" "$TMP_DIR/issue_tests_initial.md"

echo "==> Шаг 2. Номера issue"

EPIC_NUM="$(issue_number_by_title "[EPIC][MVP] Driver Readiness Platform")"
SUB_ONBOARDING_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Driver Profile and Onboarding")"
SUB_DOCUMENTS_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Driver Documents and Compliance")"
SUB_READINESS_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Readiness Contracts and Validation")"
ISSUE_HERO_NUM="$(issue_number_by_title "[MVP] Refactor driver profile hero and readiness summary")"
ISSUE_CHECKLIST_NUM="$(issue_number_by_title "[MVP] Implement driver checklist with blocking navigation")"
ISSUE_DOCUMENTS_NUM="$(issue_number_by_title "[MVP] Rework documents section with active waybill priority")"
ISSUE_READINESS_API_NUM="$(issue_number_by_title "[MVP] Add readiness summary API and blocking reasons contract")"
ISSUE_ENUMS_NUM="$(issue_number_by_title "[MVP] Normalize driver document lifecycle enums")"
ISSUE_TAXI_IP_NUM="$(issue_number_by_title "[MVP] Implement Taxi / IP business profile section")"
ISSUE_STATES_NUM="$(issue_number_by_title "[MVP] Add human-friendly empty, loading, pending, and error states")"
ISSUE_TESTS_NUM="$(issue_number_by_title "[MVP] Cover driver onboarding with smoke and contract tests")"

for n in "$EPIC_NUM" "$SUB_ONBOARDING_NUM" "$SUB_DOCUMENTS_NUM" "$SUB_READINESS_NUM" "$ISSUE_HERO_NUM" "$ISSUE_CHECKLIST_NUM" "$ISSUE_DOCUMENTS_NUM" "$ISSUE_READINESS_API_NUM" "$ISSUE_ENUMS_NUM" "$ISSUE_TAXI_IP_NUM" "$ISSUE_STATES_NUM" "$ISSUE_TESTS_NUM"; do
  if [[ -z "$n" ]]; then
    echo "Ошибка: не удалось определить номера всех issue. Проверьте совпадение заголовков." >&2
    exit 1
  fi
done

echo "==> Шаг 3. Назначение milestone"
for num in "$EPIC_NUM" "$SUB_ONBOARDING_NUM" "$SUB_DOCUMENTS_NUM" "$SUB_READINESS_NUM" "$ISSUE_HERO_NUM" "$ISSUE_CHECKLIST_NUM" "$ISSUE_DOCUMENTS_NUM" "$ISSUE_READINESS_API_NUM" "$ISSUE_ENUMS_NUM" "$ISSUE_TAXI_IP_NUM" "$ISSUE_STATES_NUM" "$ISSUE_TESTS_NUM"; do
  assign_issue_to_milestone "$num" "$MILESTONE_TITLE"
done

echo "==> Шаг 4. Финальные body"

cat > "$TMP_DIR/epic_driver_readiness_final.md" <<EOF2
## Epic: Driver Readiness Platform

### Milestone
- $MILESTONE_TITLE

### Goal
Bring a driver from first entry to \`Ready for orders\` through profile completion, document upload, readiness validation, and compliance checks.

### Why
The current driver experience needs a clearer path from incomplete profile to operational readiness. The platform should make it obvious:
- whether the driver is allowed to work
- what is missing
- what the next action is
- how documents and business identity affect readiness

### Scope
- driver profile and onboarding
- readiness summary
- blocking reasons
- driver documents
- active waybill priority
- Taxi / IP business identity
- going online prerequisites
- frontend/backend contract sync

### Children
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance
- #$SUB_READINESS_NUM Readiness Contracts and Validation
- #$ISSUE_TAXI_IP_NUM Implement Taxi / IP business profile section

### MVP delivery path
1. #$ISSUE_READINESS_API_NUM Readiness summary API
2. #$ISSUE_HERO_NUM Hero and readiness summary UI
3. #$ISSUE_CHECKLIST_NUM Checklist with blocking navigation
4. #$ISSUE_DOCUMENTS_NUM Documents section and active waybill priority
5. #$ISSUE_ENUMS_NUM Document lifecycle enums
6. #$ISSUE_TAXI_IP_NUM Taxi / IP business profile section
7. #$ISSUE_STATES_NUM Human-friendly states
8. #$ISSUE_TESTS_NUM Smoke and contract tests

### Success criteria
- driver can complete onboarding end-to-end on mobile
- readiness is computed consistently on the server
- missing profile fields and documents are visible and actionable
- active waybill is treated as a first-class operational document
- user can move from incomplete profile to \`Ready for orders\` without ambiguity
EOF2

cat > "$TMP_DIR/subepic_driver_onboarding_final.md" <<EOF2
## Sub-epic: Driver Profile and Onboarding

### Parent
- #$EPIC_NUM Driver Readiness Platform

### Milestone
- $MILESTONE_TITLE

### Goal
Build the mobile-first driver profile flow from role selection to readiness summary.

### Scope
- role selection
- basic profile
- driver-specific fields
- hero summary block
- readiness status card
- progress / checklist
- next-step CTA
- empty / loading / error states

### Children
- #$ISSUE_HERO_NUM Refactor driver profile hero and readiness summary
- #$ISSUE_CHECKLIST_NUM Implement driver checklist with blocking navigation
- #$ISSUE_STATES_NUM Add human-friendly empty, loading, pending, and error states
EOF2

cat > "$TMP_DIR/subepic_driver_documents_final.md" <<EOF2
## Sub-epic: Driver Documents and Compliance

### Parent
- #$EPIC_NUM Driver Readiness Platform

### Milestone
- $MILESTONE_TITLE

### Goal
Turn driver documents into a full compliance lifecycle, not just a file list.

### Scope
- upload and reupload
- pending / approved / rejected states
- review comments
- expiry tracking
- active waybill priority
- required documents visibility
- compliance-related blocking reasons

### Children
- #$ISSUE_DOCUMENTS_NUM Rework documents section with active waybill priority
- #$ISSUE_ENUMS_NUM Normalize driver document lifecycle enums
- #$ISSUE_TESTS_NUM Cover driver onboarding with smoke and contract tests

### Related
- #$SUB_READINESS_NUM Readiness Contracts and Validation
EOF2

cat > "$TMP_DIR/subepic_readiness_contracts_final.md" <<EOF2
## Sub-epic: Readiness Contracts and Validation

### Parent
- #$EPIC_NUM Driver Readiness Platform

### Milestone
- $MILESTONE_TITLE

### Goal
Define a stable server-side contract for driver readiness and blocking reasons.

### Scope
- readiness summary API
- blocking reasons schema
- progress counters
- allowed actions
- next-step guidance
- validation rules
- contract tests

### Children
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
- #$ISSUE_TAXI_IP_NUM Implement Taxi / IP business profile section
- #$ISSUE_TESTS_NUM Cover driver onboarding with smoke and contract tests
EOF2

cat > "$TMP_DIR/issue_hero_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Milestone
- $MILESTONE_TITLE

## Goal
Create a strong hero summary and status block for the driver profile screen.

### Related
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
EOF2

cat > "$TMP_DIR/issue_checklist_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Milestone
- $MILESTONE_TITLE

## Goal
Show required profile fields as a checklist and navigate users directly to missing sections.

### Related
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
EOF2

cat > "$TMP_DIR/issue_documents_final.md" <<EOF2
## Parent
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

## Milestone
- $MILESTONE_TITLE

## Goal
Redesign the documents section so active operational documents are prioritized.

### Related
- #$ISSUE_ENUMS_NUM Normalize driver document lifecycle enums
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
EOF2

cat > "$TMP_DIR/issue_readiness_api_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation

## Milestone
- $MILESTONE_TITLE

## Goal
Provide a backend API for readiness summary and actionable blocking reasons.

### Used by
- #$ISSUE_HERO_NUM Hero and readiness summary UI
- #$ISSUE_CHECKLIST_NUM Checklist with blocking navigation
- #$ISSUE_DOCUMENTS_NUM Documents section and active waybill priority
EOF2

cat > "$TMP_DIR/issue_document_enums_final.md" <<EOF2
## Parent
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

## Milestone
- $MILESTONE_TITLE

## Goal
Unify document enums and lifecycle rules across the system.
EOF2

cat > "$TMP_DIR/issue_taxi_ip_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation
- #$EPIC_NUM Driver Readiness Platform

## Milestone
- $MILESTONE_TITLE

## Goal
Add the Taxi / IP section as part of readiness-critical profile data.
EOF2

cat > "$TMP_DIR/issue_states_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Milestone
- $MILESTONE_TITLE

## Goal
Replace raw technical states with reusable user-friendly UI states.
EOF2

cat > "$TMP_DIR/issue_tests_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

## Milestone
- $MILESTONE_TITLE

## Goal
Protect the new driver onboarding and readiness flow with tests.
EOF2

update_issue_body "$EPIC_NUM" "$TMP_DIR/epic_driver_readiness_final.md"
update_issue_body "$SUB_ONBOARDING_NUM" "$TMP_DIR/subepic_driver_onboarding_final.md"
update_issue_body "$SUB_DOCUMENTS_NUM" "$TMP_DIR/subepic_driver_documents_final.md"
update_issue_body "$SUB_READINESS_NUM" "$TMP_DIR/subepic_readiness_contracts_final.md"
update_issue_body "$ISSUE_HERO_NUM" "$TMP_DIR/issue_hero_final.md"
update_issue_body "$ISSUE_CHECKLIST_NUM" "$TMP_DIR/issue_checklist_final.md"
update_issue_body "$ISSUE_DOCUMENTS_NUM" "$TMP_DIR/issue_documents_final.md"
update_issue_body "$ISSUE_READINESS_API_NUM" "$TMP_DIR/issue_readiness_api_final.md"
update_issue_body "$ISSUE_ENUMS_NUM" "$TMP_DIR/issue_document_enums_final.md"
update_issue_body "$ISSUE_TAXI_IP_NUM" "$TMP_DIR/issue_taxi_ip_final.md"
update_issue_body "$ISSUE_STATES_NUM" "$TMP_DIR/issue_states_final.md"
update_issue_body "$ISSUE_TESTS_NUM" "$TMP_DIR/issue_tests_final.md"

echo "==> Шаг 5. Сводный комментарий в Epic"
EPIC_COMMENT_MARKER="<!-- driver-readiness-mvp-summary -->"

cat > "$TMP_DIR/epic_summary_comment.md" <<EOF2
$EPIC_COMMENT_MARKER

## Driver Readiness MVP summary

### Milestone
- **$MILESTONE_TITLE**

### Created hierarchy
| Type | Issue | Link |
|---|---|---|
| Epic | #$EPIC_NUM Driver Readiness Platform | https://github.com/$REPO/issues/$EPIC_NUM |
| Sub-epic | #$SUB_ONBOARDING_NUM Driver Profile and Onboarding | https://github.com/$REPO/issues/$SUB_ONBOARDING_NUM |
| Sub-epic | #$SUB_DOCUMENTS_NUM Driver Documents and Compliance | https://github.com/$REPO/issues/$SUB_DOCUMENTS_NUM |
| Sub-epic | #$SUB_READINESS_NUM Readiness Contracts and Validation | https://github.com/$REPO/issues/$SUB_READINESS_NUM |

### MVP issues
| # | Title | Area |
|---|---|---|
| #$ISSUE_HERO_NUM | Refactor driver profile hero and readiness summary | frontend / ux |
| #$ISSUE_CHECKLIST_NUM | Implement driver checklist with blocking navigation | frontend / ux |
| #$ISSUE_DOCUMENTS_NUM | Rework documents section with active waybill priority | frontend / backend / documents |
| #$ISSUE_READINESS_API_NUM | Add readiness summary API and blocking reasons contract | backend / api |
| #$ISSUE_ENUMS_NUM | Normalize driver document lifecycle enums | backend / api / documents |
| #$ISSUE_TAXI_IP_NUM | Implement Taxi / IP business profile section | frontend / backend / api |
| #$ISSUE_STATES_NUM | Add human-friendly empty, loading, pending, and error states | frontend / ux / design-system |
| #$ISSUE_TESTS_NUM | Cover driver onboarding with smoke and contract tests | frontend / backend / api |

### Recommended implementation order
1. #$ISSUE_READINESS_API_NUM
2. #$ISSUE_HERO_NUM
3. #$ISSUE_CHECKLIST_NUM
4. #$ISSUE_DOCUMENTS_NUM
5. #$ISSUE_ENUMS_NUM
6. #$ISSUE_TAXI_IP_NUM
7. #$ISSUE_STATES_NUM
8. #$ISSUE_TESTS_NUM

### Notes
- All issues are attached to milestone **$MILESTONE_TITLE**.
- Parent/child relationships are represented through linked issue bodies.
EOF2

post_comment_if_missing "$EPIC_NUM" "$TMP_DIR/epic_summary_comment.md" "$EPIC_COMMENT_MARKER"

echo
echo "Готово."
echo "Milestone: https://github.com/$REPO/milestone/$MILESTONE_NUM"
echo "Epic: https://github.com/$REPO/issues/$EPIC_NUM"
echo "Все issues: https://github.com/$REPO/issues"
