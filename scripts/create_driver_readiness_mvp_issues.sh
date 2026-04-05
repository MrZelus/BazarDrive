#!/usr/bin/env bash
set -euo pipefail

# Termux-ready bootstrap script that:
# 1) Ensures labels exist
# 2) Creates Epic/Sub-epic/MVP issues (if missing)
# 3) Resolves issue numbers
# 4) Rewrites issue bodies with Parent/Children/Related links

DEFAULT_REPO="MrZelus/BazarDrive"
REPO="${1:-${REPO:-$DEFAULT_REPO}}"

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
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    "${args[@]}" \
    --body-file "$body_file" >/dev/null
}

update_issue_body() {
  local number="$1"
  local body_file="$2"

  echo "Updating issue #$number"
  gh issue edit "$number" --repo "$REPO" --body-file "$body_file" >/dev/null
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

echo "==> Шаг 1. Создание базовых issue без ссылок"

cat > "$TMP_DIR/epic_driver_readiness_initial.md" <<'MD'
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
MD

cat > "$TMP_DIR/subepic_driver_onboarding_initial.md" <<'MD'
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
MD

cat > "$TMP_DIR/subepic_driver_documents_initial.md" <<'MD'
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
MD

cat > "$TMP_DIR/subepic_readiness_contracts_initial.md" <<'MD'
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
MD

cat > "$TMP_DIR/issue_hero_initial.md" <<'MD'
## Goal
Create a strong hero summary and status block for the driver profile screen.

### Tasks
- add hero-card with display name / role / business type / tax regime / progress
- add readiness status-card with status, reason, and next step
- keep one main CTA in the visible viewport
MD

cat > "$TMP_DIR/issue_checklist_initial.md" <<'MD'
## Goal
Show required profile fields as a checklist and navigate users directly to missing sections.

### Tasks
- add checklist for required fields
- mark complete vs missing items
- deep-link missing items to the correct section
- sync checklist with server readiness summary
MD

cat > "$TMP_DIR/issue_documents_initial.md" <<'MD'
## Goal
Redesign the documents section so active operational documents are prioritized.

### Tasks
- surface active waybill first
- group docs by state: required / pending / approved / archive
- show status, expiry, and review comment
- support reupload flow
MD

cat > "$TMP_DIR/issue_readiness_api_initial.md" <<'MD'
## Goal
Provide a backend API for readiness summary and actionable blocking reasons.

### Tasks
- implement readiness summary response
- implement blocking reasons schema
- return progress counters
- return next_step and allowed_actions
- cover with contract tests
MD

cat > "$TMP_DIR/issue_document_enums_initial.md" <<'MD'
## Goal
Unify document enums and lifecycle rules across the system.

### Tasks
- define DocumentType enum
- define DocumentStatus enum
- support review_comment and expires_at
- enforce single active waybill
- support rejected -> reupload flow
MD

cat > "$TMP_DIR/issue_taxi_ip_initial.md" <<'MD'
## Goal
Add the Taxi / IP section as part of readiness-critical profile data.

### Tasks
- add business type, INN, OGRNIP, tax regime, region, vehicle
- validate identifiers
- link section to readiness pipeline
MD

cat > "$TMP_DIR/issue_states_initial.md" <<'MD'
## Goal
Replace raw technical states with reusable user-friendly UI states.

### Tasks
- remove raw messages like `Failed to fetch`
- add loading skeletons
- add empty states with next-step CTA
- add retry state
- add pending review state
MD

cat > "$TMP_DIR/issue_tests_initial.md" <<'MD'
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
MD

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

echo "==> Шаг 2. Получение номеров issue"

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

echo "Epic: #$EPIC_NUM"
echo "Sub-epic onboarding: #$SUB_ONBOARDING_NUM"
echo "Sub-epic documents: #$SUB_DOCUMENTS_NUM"
echo "Sub-epic readiness: #$SUB_READINESS_NUM"

echo "==> Шаг 3. Финальные body с parent/child связями"

cat > "$TMP_DIR/epic_driver_readiness_final.md" <<EOF2
## Epic: Driver Readiness Platform

### Goal
Bring a driver from first entry to \
`Ready for orders` through profile completion, document upload, readiness validation, and compliance checks.

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
6. #$ISSUE_STATES_NUM Human-friendly states
7. #$ISSUE_TESTS_NUM Smoke and contract tests

### Success criteria
- driver can complete onboarding end-to-end on mobile
- readiness is computed consistently on the server
- missing profile fields and documents are visible and actionable
- active waybill is treated as a first-class operational document
- user can move from incomplete profile to \
`Ready for orders` without ambiguity
EOF2

cat > "$TMP_DIR/subepic_driver_onboarding_final.md" <<EOF2
## Sub-epic: Driver Profile and Onboarding

### Parent
- #$EPIC_NUM Driver Readiness Platform

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

### Acceptance criteria
- driver understands readiness in 3–5 seconds
- profile progress is visible
- one primary CTA per screen
- blocked states always explain next step
EOF2

cat > "$TMP_DIR/subepic_driver_documents_final.md" <<EOF2
## Sub-epic: Driver Documents and Compliance

### Parent
- #$EPIC_NUM Driver Readiness Platform

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

### Acceptance criteria
- required missing docs are obvious
- active waybill is always surfaced first
- rejected docs can be reuploaded
- document statuses are consistent across frontend and backend
EOF2

cat > "$TMP_DIR/subepic_readiness_contracts_final.md" <<EOF2
## Sub-epic: Readiness Contracts and Validation

### Parent
- #$EPIC_NUM Driver Readiness Platform

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

### Suggested contract
- readiness_status
- progress_filled
- progress_total
- blocking_reasons[]
- next_step
- allowed_actions[]

### Blocking reason fields
- code
- message
- severity
- next_action
- target_screen

### Children
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
- #$ISSUE_TAXI_IP_NUM Implement Taxi / IP business profile section
- #$ISSUE_TESTS_NUM Cover driver onboarding with smoke and contract tests

### Related
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

### Acceptance criteria
- frontend does not compute final readiness on its own
- blocking reasons are structured and actionable
- contract tests protect API stability
EOF2

cat > "$TMP_DIR/issue_hero_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Goal
Create a strong hero summary and status block for the driver profile screen.

### Tasks
- add hero-card with:
  - display name / full name
  - role
  - business type
  - tax regime
  - progress x/y
- add readiness status-card with:
  - status
  - reason
  - next step
- keep one main CTA in the visible viewport

### Related
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract

### Acceptance criteria
- readiness is understandable at first glance
- next action is obvious
- multiple fragmented summary cards are removed
EOF2

cat > "$TMP_DIR/issue_checklist_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Goal
Show required profile fields as a checklist and navigate users directly to missing sections.

### Tasks
- add checklist for required fields
- mark complete vs missing items
- deep-link missing items to the correct section
- sync checklist with server readiness summary

### Related
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract

### Acceptance criteria
- missing fields are actionable
- clicking a missing item opens the correct section
- progress matches readiness data from backend
EOF2

cat > "$TMP_DIR/issue_documents_final.md" <<EOF2
## Parent
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

## Goal
Redesign the documents section so active operational documents are prioritized.

### Tasks
- surface active waybill first
- group docs by state:
  - required
  - pending
  - approved
  - archive
- show document status, expiry, and review comment
- support reupload flow

### Related
- #$ISSUE_ENUMS_NUM Normalize driver document lifecycle enums
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract

### Acceptance criteria
- active waybill is visually distinct
- required missing docs are obvious
- rejected docs can be reuploaded cleanly
EOF2

cat > "$TMP_DIR/issue_readiness_api_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation

## Goal
Provide a backend API for readiness summary and actionable blocking reasons.

### Tasks
- implement readiness summary response
- implement blocking reasons schema
- return progress counters
- return next_step and allowed_actions
- cover with contract tests

### Used by
- #$ISSUE_HERO_NUM Hero and readiness summary UI
- #$ISSUE_CHECKLIST_NUM Checklist with blocking navigation
- #$ISSUE_DOCUMENTS_NUM Documents section and active waybill priority

### Acceptance criteria
- frontend receives all readiness data from API
- blocking reasons are actionable
- readiness logic is centralized on the server
EOF2

cat > "$TMP_DIR/issue_document_enums_final.md" <<EOF2
## Parent
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

## Goal
Unify document enums and lifecycle rules across the system.

### Tasks
- define DocumentType enum
- define DocumentStatus enum
- support review_comment and expires_at
- enforce single active waybill
- support rejected -> reupload flow

### Related
- #$ISSUE_DOCUMENTS_NUM Rework documents section with active waybill priority
- #$ISSUE_TESTS_NUM Cover driver onboarding with smoke and contract tests

### Acceptance criteria
- frontend and backend use the same enums
- active waybill uniqueness is enforced
- lifecycle is predictable and testable
EOF2

cat > "$TMP_DIR/issue_taxi_ip_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation
- #$EPIC_NUM Driver Readiness Platform

## Goal
Add the Taxi / IP section as part of readiness-critical profile data.

### Tasks
- add section for:
  - business type
  - INN
  - OGRNIP
  - tax regime
  - region
  - vehicle
- validate identifiers
- link section to readiness pipeline

### Acceptance criteria
- section is separate and understandable
- invalid values are explained clearly
- missing fields can produce blocking reasons
EOF2

cat > "$TMP_DIR/issue_states_final.md" <<EOF2
## Parent
- #$SUB_ONBOARDING_NUM Driver Profile and Onboarding

## Goal
Replace raw technical states with reusable user-friendly UI states.

### Tasks
- remove raw messages like `Failed to fetch`
- add loading skeletons
- add empty states with next-step CTA
- add retry state
- add pending review state

### Acceptance criteria
- no raw technical errors are shown to end users
- main screen states are visually consistent
- every state suggests a useful next action when applicable
EOF2

cat > "$TMP_DIR/issue_tests_final.md" <<EOF2
## Parent
- #$SUB_READINESS_NUM Readiness Contracts and Validation
- #$SUB_DOCUMENTS_NUM Driver Documents and Compliance

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

### Related
- #$ISSUE_READINESS_API_NUM Add readiness summary API and blocking reasons contract
- #$ISSUE_ENUMS_NUM Normalize driver document lifecycle enums

### Acceptance criteria
- onboarding states are covered
- readiness contract is stable
- document lifecycle regressions are caught early
EOF2

echo "==> Шаг 4. Обновление body у issue"
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

echo
echo "Готово."
echo "Epic: https://github.com/$REPO/issues/$EPIC_NUM"
echo "Sub-epic onboarding: https://github.com/$REPO/issues/$SUB_ONBOARDING_NUM"
echo "Sub-epic documents: https://github.com/$REPO/issues/$SUB_DOCUMENTS_NUM"
echo "Sub-epic readiness: https://github.com/$REPO/issues/$SUB_READINESS_NUM"
echo "Все issues: https://github.com/$REPO/issues"
