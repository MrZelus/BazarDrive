#!/usr/bin/env bash
set -euo pipefail

# Termux-friendly script to bootstrap labels and initial MVP issues.
# Usage:
#   ./scripts/create_driver_readiness_mvp_issues.sh [owner/repo]
# If repo is omitted, the current gh context repository is used.

REPO_ARG="${1:-}"
if [[ -n "$REPO_ARG" ]]; then
  GH_REPO_ARGS=(--repo "$REPO_ARG")
else
  GH_REPO_ARGS=()
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' is not installed." >&2
    exit 1
  fi
}

require_cmd gh

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

ensure_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  if gh label list "${GH_REPO_ARGS[@]}" --limit 200 --search "$name" --json name --jq '.[].name' | grep -Fxq "$name"; then
    echo "Label exists: $name"
  else
    gh label create "$name" "${GH_REPO_ARGS[@]}" --color "$color" --description "$description"
    echo "Created label: $name"
  fi
}

create_issue() {
  local title="$1"
  local labels_csv="$2"
  local body_file="$3"

  IFS=',' read -r -a labels <<<"$labels_csv"
  local label_args=()
  for label in "${labels[@]}"; do
    label_args+=(--label "$label")
  done

  gh issue create "${GH_REPO_ARGS[@]}" --title "$title" "${label_args[@]}" --body-file "$body_file"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

# --- Labels ---
ensure_label "epic" "5319E7" "Top-level epic"
ensure_label "mvp" "B60205" "Minimum viable scope"
ensure_label "frontend" "1D76DB" "Frontend work"
ensure_label "backend" "0E8A16" "Backend work"
ensure_label "ux" "FBCA04" "UX and product flow"
ensure_label "api" "0052CC" "API and contracts"
ensure_label "documents" "C5DEF5" "Documents and compliance"
ensure_label "driver" "D4C5F9" "Driver-related functionality"
ensure_label "readiness" "F9D0C4" "Readiness and blocking logic"
ensure_label "orders" "BFDADC" "Orders workflow"
ensure_label "design-system" "FEF2C0" "Design system and UI consistency"
ensure_label "analytics" "006B75" "Metrics and observability"
ensure_label "backoffice" "E4E669" "Admin and review tooling"

# --- Issue bodies (recommended MVP 8) ---
cat >"$tmp_dir/epic_driver_readiness.md" <<'MD'
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

cat >"$tmp_dir/subepic_driver_onboarding.md" <<'MD'
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

cat >"$tmp_dir/subepic_driver_documents.md" <<'MD'
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

cat >"$tmp_dir/subepic_readiness_contracts.md" <<'MD'
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

cat >"$tmp_dir/mvp_hero_readiness.md" <<'MD'
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

cat >"$tmp_dir/mvp_checklist.md" <<'MD'
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

cat >"$tmp_dir/mvp_documents_waybill.md" <<'MD'
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

cat >"$tmp_dir/mvp_readiness_api.md" <<'MD'
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

# --- Create issues ---
create_issue "[EPIC][MVP] Driver Readiness Platform" "epic,mvp,driver,readiness" "$tmp_dir/epic_driver_readiness.md"
create_issue "[SUB-EPIC][MVP] Driver Profile and Onboarding" "epic,mvp,driver,ux,frontend" "$tmp_dir/subepic_driver_onboarding.md"
create_issue "[SUB-EPIC][MVP] Driver Documents and Compliance" "epic,mvp,driver,documents,backend,frontend" "$tmp_dir/subepic_driver_documents.md"
create_issue "[SUB-EPIC][MVP] Readiness Contracts and Validation" "epic,mvp,api,backend,readiness" "$tmp_dir/subepic_readiness_contracts.md"
create_issue "[MVP] Refactor driver profile hero and readiness summary" "mvp,frontend,ux,driver,readiness" "$tmp_dir/mvp_hero_readiness.md"
create_issue "[MVP] Implement driver checklist with blocking navigation" "mvp,frontend,ux,driver" "$tmp_dir/mvp_checklist.md"
create_issue "[MVP] Rework documents section with active waybill priority" "mvp,frontend,backend,documents,driver" "$tmp_dir/mvp_documents_waybill.md"
create_issue "[MVP] Add readiness summary API and blocking reasons contract" "mvp,backend,api,readiness" "$tmp_dir/mvp_readiness_api.md"

echo "Done. Labels ensured and 8 MVP issues created."
