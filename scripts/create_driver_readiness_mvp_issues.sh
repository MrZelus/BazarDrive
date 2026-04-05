#!/usr/bin/env bash
set -euo pipefail

# Termux-ready bootstrap for Driver Readiness planning artifacts.
# Creates labels and MVP issues in GitHub repository.
#
# Usage:
#   ./scripts/create_driver_readiness_mvp_issues.sh
#   ./scripts/create_driver_readiness_mvp_issues.sh owner/repo
#
# Defaults to MrZelus/BazarDrive if repo argument is not provided.

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
    gh label create "$name" \
      --repo "$REPO" \
      --color "$color" \
      --description "$desc"
  fi
}

issue_exists() {
  local title="$1"
  gh issue list \
    --repo "$REPO" \
    --state all \
    --search "in:title \"$title\"" \
    --limit 100 \
    --json title \
    --jq '.[].title' | grep -Fxq "$title"
}

create_issue_if_missing() {
  local title="$1"
  local labels_csv="$2"
  local body_file="$3"

  if issue_exists "$title"; then
    echo "Issue exists: $title"
    return 0
  fi

  IFS=',' read -r -a labels <<<"$labels_csv"
  local label_args=()
  local label
  for label in "${labels[@]}"; do
    label_args+=(--label "$label")
  done

  echo "Creating issue: $title"
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    "${label_args[@]}" \
    --body-file "$body_file"
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

echo "==> Запись markdown-файлов"

cat > "$TMP_DIR/epic_driver_readiness.md" <<'MD'
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

### Sub-epics
- Driver Profile and Onboarding
- Driver Documents and Compliance
- Taxi / IP Business Identity
- Driver Availability and Going Online
- Readiness Contracts and Validation

### Success criteria
- driver can complete onboarding end-to-end on mobile
- readiness is computed consistently on the server
- missing profile fields and documents are visible and actionable
- active waybill is treated as a first-class operational document
- user can move from incomplete profile to `Ready for orders` without ambiguity
MD

cat > "$TMP_DIR/subepic_driver_onboarding.md" <<'MD'
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

### Deliverables
- mobile driver profile layout
- hero-card with progress and main CTA
- status-card with readiness and next step
- checklist of required fields
- onboarding screen flow
- human-friendly UI states

### Acceptance criteria
- driver understands readiness in 3–5 seconds
- profile progress is visible
- one primary CTA per screen
- blocked states always explain next step
MD

cat > "$TMP_DIR/subepic_driver_documents.md" <<'MD'
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

### Deliverables
- document section redesign
- grouped document states
- active waybill priority-card
- review lifecycle contract
- expiry handling
- rejection and resubmission flow

### Acceptance criteria
- required missing docs are obvious
- active waybill is always surfaced first
- rejected docs can be reuploaded
- document statuses are consistent across frontend and backend
MD

cat > "$TMP_DIR/subepic_taxi_ip.md" <<'MD'
## Sub-epic: Taxi / IP Business Identity

### Goal
Represent the driver’s legal and business identity as a first-class readiness input.

### Scope
- business type
- INN
- OGRNIP
- tax regime
- region
- vehicle data
- legal eligibility linkage

### Deliverables
- business profile section
- API contract for business identity
- validation rules
- readiness integration

### Acceptance criteria
- required business fields are explicit
- invalid legal identifiers are validated clearly
- missing business info can block readiness when required
MD

cat > "$TMP_DIR/subepic_driver_availability.md" <<'MD'
## Sub-epic: Driver Availability and Going Online

### Goal
Ensure that only eligible drivers can go online and receive orders.

### Scope
- go online / go offline
- readiness prerequisites
- active shift state
- active waybill dependency
- online eligibility checks

### Deliverables
- online eligibility rules
- readiness gate before going online
- driver availability states
- UI messaging for blocked online attempts

### Acceptance criteria
- driver cannot go online while blocked
- readiness and availability are consistent
- missing prerequisites are clearly explained
MD

cat > "$TMP_DIR/subepic_readiness_contracts.md" <<'MD'
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

### Acceptance criteria
- frontend does not compute final readiness on its own
- blocking reasons are structured and actionable
- contract tests protect API stability
MD

cat > "$TMP_DIR/issue_hero_readiness.md" <<'MD'
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

### Acceptance criteria
- readiness is understandable at first glance
- next action is obvious
- multiple fragmented summary cards are removed
MD

cat > "$TMP_DIR/issue_checklist_navigation.md" <<'MD'
## Goal
Show required profile fields as a checklist and navigate users directly to missing sections.

### Tasks
- add checklist for required fields
- mark complete vs missing items
- deep-link missing items to the correct section
- sync checklist with server readiness summary

### Acceptance criteria
- missing fields are actionable
- clicking a missing item opens the correct section
- progress matches readiness data from backend
MD

cat > "$TMP_DIR/issue_documents_waybill.md" <<'MD'
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

### Acceptance criteria
- active waybill is visually distinct
- required missing docs are obvious
- rejected docs can be reuploaded cleanly
MD

cat > "$TMP_DIR/issue_readiness_api.md" <<'MD'
## Goal
Provide a backend API for readiness summary and actionable blocking reasons.

### Tasks
- implement readiness summary response
- implement blocking reasons schema
- return progress counters
- return next_step and allowed_actions
- cover with contract tests

### Acceptance criteria
- frontend receives all readiness data from API
- blocking reasons are actionable
- readiness logic is centralized on the server
MD

cat > "$TMP_DIR/issue_document_enums.md" <<'MD'
## Goal
Unify document enums and lifecycle rules across the system.

### Tasks
- define DocumentType enum
- define DocumentStatus enum
- support review_comment and expires_at
- enforce single active waybill
- support rejected -> reupload flow

### Acceptance criteria
- frontend and backend use the same enums
- active waybill uniqueness is enforced
- lifecycle is predictable and testable
MD

cat > "$TMP_DIR/issue_taxi_ip.md" <<'MD'
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
MD

cat > "$TMP_DIR/issue_states.md" <<'MD'
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
MD

cat > "$TMP_DIR/issue_tests.md" <<'MD'
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

### Acceptance criteria
- onboarding states are covered
- readiness contract is stable
- document lifecycle regressions are caught early
MD

echo "==> Создание Epic / Sub-epic / MVP issues"
create_issue_if_missing "[EPIC][MVP] Driver Readiness Platform" "epic,mvp,driver,readiness" "$TMP_DIR/epic_driver_readiness.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Profile and Onboarding" "epic,mvp,driver,ux,frontend" "$TMP_DIR/subepic_driver_onboarding.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Documents and Compliance" "epic,mvp,driver,documents,backend,frontend" "$TMP_DIR/subepic_driver_documents.md"
create_issue_if_missing "[SUB-EPIC][MVP] Taxi / IP Business Identity" "epic,mvp,driver,backend,api" "$TMP_DIR/subepic_taxi_ip.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Availability and Going Online" "epic,mvp,driver,orders,backend" "$TMP_DIR/subepic_driver_availability.md"
create_issue_if_missing "[SUB-EPIC][MVP] Readiness Contracts and Validation" "epic,mvp,api,backend,readiness" "$TMP_DIR/subepic_readiness_contracts.md"
create_issue_if_missing "[MVP] Refactor driver profile hero and readiness summary" "mvp,frontend,ux,driver,readiness" "$TMP_DIR/issue_hero_readiness.md"
create_issue_if_missing "[MVP] Implement driver checklist with blocking navigation" "mvp,frontend,ux,driver" "$TMP_DIR/issue_checklist_navigation.md"
create_issue_if_missing "[MVP] Rework documents section with active waybill priority" "mvp,frontend,backend,documents,driver" "$TMP_DIR/issue_documents_waybill.md"
create_issue_if_missing "[MVP] Add readiness summary API and blocking reasons contract" "mvp,backend,api,readiness" "$TMP_DIR/issue_readiness_api.md"
create_issue_if_missing "[MVP] Normalize driver document lifecycle enums" "mvp,backend,api,documents" "$TMP_DIR/issue_document_enums.md"
create_issue_if_missing "[MVP] Implement Taxi / IP business profile section" "mvp,frontend,backend,api,driver" "$TMP_DIR/issue_taxi_ip.md"
create_issue_if_missing "[MVP] Add human-friendly empty, loading, pending, and error states" "mvp,frontend,ux,design-system" "$TMP_DIR/issue_states.md"
create_issue_if_missing "[MVP] Cover driver onboarding with smoke and contract tests" "mvp,backend,frontend,api" "$TMP_DIR/issue_tests.md"

echo
echo "Готово."
echo "Проверьте созданные issues:"
echo "https://github.com/$REPO/issues"
