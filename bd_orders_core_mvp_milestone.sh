#!/usr/bin/env bash
set -euo pipefail

REPO="MrZelus/BazarDrive"
MILESTONE_TITLE="Orders Marketplace Core MVP"
MILESTONE_DESC="MVP scope for passenger order creation, driver intake, order lifecycle, and active trip UX."
MILESTONE_DUE="2026-06-15T23:59:59Z"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Не найдено: $1"
    exit 1
  }
}

need_cmd gh
need_cmd mktemp
need_cmd sed
need_cmd grep
need_cmd awk
need_cmd python3

echo "==> Проверка авторизации GitHub"
gh auth status >/dev/null

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

create_label_if_missing() {
  local name="$1"
  local color="$2"
  local desc="$3"

  if gh label list --repo "$REPO" --limit 200 | awk '{print $1}' | grep -Fxq "$name"; then
    echo "Label exists: $name"
  else
    echo "Creating label: $name"
    gh label create "$name" \
      --repo "$REPO" \
      --color "$color" \
      --description "$desc"
  fi
}

issue_number_by_title() {
  local title="$1"
  gh issue list --repo "$REPO" --state all --limit 200 --search "in:title \"$title\"" --json number,title \
    | sed 's/},{/}\n{/g' \
    | grep -F "\"title\":\"$title\"" \
    | sed -n 's/.*"number":\([0-9][0-9]*\).*/\1/p' \
    | head -n1
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
  echo "Updating issue #$number"
  gh issue edit "$number" --repo "$REPO" --body-file "$body_file" >/dev/null
}

comment_exists_with_marker() {
  local issue_number="$1"
  local marker="$2"
  gh issue view "$issue_number" --repo "$REPO" --comments \
    | grep -Fq "$marker"
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

milestone_number_by_title() {
  local title="$1"
  local milestones_json
  milestones_json="$(gh api "repos/$REPO/milestones?state=all&per_page=100")"

  python3 - "$title" "$milestones_json" <<'PY'
import json, sys
title = sys.argv[1]
raw = sys.argv[2]
if not raw.strip():
    sys.exit(0)

items = json.loads(raw)
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
  echo "Assigning issue #$issue_number to milestone #$milestone_number"
  gh api "repos/$REPO/issues/$issue_number" \
    --method PATCH \
    -f milestone="$milestone_number" >/dev/null
}

echo "==> Создание лейблов"
create_label_if_missing "epic" "5319E7" "Top-level epic"
create_label_if_missing "mvp" "B60205" "Minimum viable scope"
create_label_if_missing "frontend" "1D76DB" "Frontend work"
create_label_if_missing "backend" "0E8A16" "Backend work"
create_label_if_missing "ux" "FBCA04" "UX and product flow"
create_label_if_missing "api" "0052CC" "API and contracts"
create_label_if_missing "orders" "BFDADC" "Orders workflow"
create_label_if_missing "driver" "D4C5F9" "Driver-related functionality"
create_label_if_missing "passenger" "F9D0C4" "Passenger-related functionality"
create_label_if_missing "dispatch" "C2E0C6" "Dispatch and trip coordination"
create_label_if_missing "design-system" "FEF2C0" "Design system and UI consistency"
create_label_if_missing "analytics" "006B75" "Metrics and observability"

echo "==> Создание milestone"
create_milestone_if_missing "$MILESTONE_TITLE" "$MILESTONE_DESC" "$MILESTONE_DUE"
MILESTONE_NUM="$(milestone_number_by_title "$MILESTONE_TITLE")"
echo "Milestone: #$MILESTONE_NUM"

echo "==> Шаг 1. Базовые issue"

cat > "$TMP_DIR/epic_orders_core_initial.md" <<'EOF2'
## Epic: Orders Marketplace Core

### Goal
Implement the core order flow for passengers and drivers, from order creation to active trip completion.

### Why
Orders are the heart of the marketplace. The system should clearly support:
- passenger order creation
- driver order intake
- status transitions
- active trip handling
- predictable lifecycle updates

### Scope
- passenger order creation
- driver order intake
- order lifecycle
- active trip UX
- status transitions
- server-side order rules
- mobile-first operational flow
EOF2

cat > "$TMP_DIR/subepic_passenger_order_creation_initial.md" <<'EOF2'
## Sub-epic: Passenger Order Creation

### Goal
Build the passenger flow for creating and submitting taxi orders.

### Scope
- pickup address
- destination
- comment
- ride time
- scheduled rides
- order confirmation
- order submission UX
EOF2

cat > "$TMP_DIR/subepic_driver_order_intake_initial.md" <<'EOF2'
## Sub-epic: Driver Order Intake

### Goal
Allow eligible drivers to view, understand, and accept available orders.

### Scope
- open orders list
- order card
- order details
- accept action
- eligibility checks
- anti-double-accept protection
EOF2

cat > "$TMP_DIR/subepic_order_lifecycle_initial.md" <<'EOF2'
## Sub-epic: Order Lifecycle

### Goal
Define a stable lifecycle for orders across backend and UI.

### Scope
- CREATED
- ACCEPTED
- ARRIVING
- ONTRIP
- DONE
- CANCELED
- EXPIRED
- transition rules
EOF2

cat > "$TMP_DIR/subepic_active_trip_ux_initial.md" <<'EOF2'
## Sub-epic: Active Trip UX

### Goal
Provide a focused operational screen for the active order.

### Scope
- active trip card
- route summary
- key trip actions
- current status
- next allowed action
- passenger/driver context
EOF2

cat > "$TMP_DIR/issue_passenger_order_form_initial.md" <<'EOF2'
## Goal
Build the passenger taxi order form and confirmation flow.

### Tasks
- pickup field
- destination field
- optional comment
- ride time
- scheduled ride option
- confirmation step
EOF2

cat > "$TMP_DIR/issue_driver_order_list_initial.md" <<'EOF2'
## Goal
Build the driver-facing list of open orders and order cards.

### Tasks
- open orders list
- card summary
- visibility rules
- refresh/update logic
- order detail open action
EOF2

cat > "$TMP_DIR/issue_driver_accept_order_initial.md" <<'EOF2'
## Goal
Implement driver order acceptance with race protection.

### Tasks
- accept order action
- server-side validation
- prevent double acceptance
- eligibility check before accept
- update order state after accept
EOF2

cat > "$TMP_DIR/issue_order_status_machine_initial.md" <<'EOF2'
## Goal
Implement the backend status machine for order lifecycle transitions.

### Tasks
- define statuses
- define allowed transitions
- reject invalid transitions
- persist transition history
- expose lifecycle state to frontend
EOF2

cat > "$TMP_DIR/issue_active_trip_card_initial.md" <<'EOF2'
## Goal
Build the active trip card for the driver with current status and next action.

### Tasks
- show route summary
- show passenger/order info
- show current status
- show next CTA
- support live state updates
EOF2

cat > "$TMP_DIR/issue_order_contracts_initial.md" <<'EOF2'
## Goal
Define API contracts for order creation, intake, and lifecycle updates.

### Tasks
- create order contract
- open orders contract
- accept order contract
- lifecycle status contract
- active trip summary contract
EOF2

cat > "$TMP_DIR/issue_orders_states_initial.md" <<'EOF2'
## Goal
Add clear loading, empty, error, and no-orders states for orders screens.

### Tasks
- passenger create-order states
- driver no-open-orders state
- loading skeletons
- retry states
- human-friendly messages
EOF2

cat > "$TMP_DIR/issue_orders_tests_initial.md" <<'EOF2'
## Goal
Cover Orders Marketplace Core MVP with smoke and contract tests.

### Tasks
- passenger order creation test
- driver open orders test
- accept order test
- lifecycle transition test
- active trip card test
- order contract tests
EOF2

create_issue_if_missing "[EPIC][MVP] Orders Marketplace Core" "epic,mvp,orders" "$TMP_DIR/epic_orders_core_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Passenger Order Creation" "epic,mvp,orders,passenger,ux,frontend" "$TMP_DIR/subepic_passenger_order_creation_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Driver Order Intake" "epic,mvp,orders,driver,frontend,backend" "$TMP_DIR/subepic_driver_order_intake_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Order Lifecycle" "epic,mvp,orders,backend,api" "$TMP_DIR/subepic_order_lifecycle_initial.md"
create_issue_if_missing "[SUB-EPIC][MVP] Active Trip UX" "epic,mvp,orders,driver,ux,frontend" "$TMP_DIR/subepic_active_trip_ux_initial.md"

create_issue_if_missing "[MVP] Implement passenger order form and confirmation flow" "mvp,orders,passenger,frontend,ux" "$TMP_DIR/issue_passenger_order_form_initial.md"
create_issue_if_missing "[MVP] Build driver open orders list and order cards" "mvp,orders,driver,frontend,ux" "$TMP_DIR/issue_driver_order_list_initial.md"
create_issue_if_missing "[MVP] Implement driver accept order flow with race protection" "mvp,orders,driver,backend,api" "$TMP_DIR/issue_driver_accept_order_initial.md"
create_issue_if_missing "[MVP] Implement order lifecycle state machine" "mvp,orders,backend,api" "$TMP_DIR/issue_order_status_machine_initial.md"
create_issue_if_missing "[MVP] Build active trip card with next-action UX" "mvp,orders,driver,frontend,ux" "$TMP_DIR/issue_active_trip_card_initial.md"
create_issue_if_missing "[MVP] Define orders API contracts and active trip summary" "mvp,orders,backend,api" "$TMP_DIR/issue_order_contracts_initial.md"
create_issue_if_missing "[MVP] Add human-friendly loading, empty, and error states for orders" "mvp,orders,frontend,ux,design-system" "$TMP_DIR/issue_orders_states_initial.md"
create_issue_if_missing "[MVP] Cover orders core with smoke and contract tests" "mvp,orders,backend,frontend,api" "$TMP_DIR/issue_orders_tests_initial.md"

echo "==> Шаг 2. Номера issue"

EPIC_NUM="$(issue_number_by_title "[EPIC][MVP] Orders Marketplace Core")"

SUB_PASSENGER_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Passenger Order Creation")"
SUB_DRIVER_INTAKE_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Driver Order Intake")"
SUB_LIFECYCLE_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Order Lifecycle")"
SUB_ACTIVE_TRIP_NUM="$(issue_number_by_title "[SUB-EPIC][MVP] Active Trip UX")"

ISSUE_PASSENGER_FORM_NUM="$(issue_number_by_title "[MVP] Implement passenger order form and confirmation flow")"
ISSUE_DRIVER_LIST_NUM="$(issue_number_by_title "[MVP] Build driver open orders list and order cards")"
ISSUE_ACCEPT_NUM="$(issue_number_by_title "[MVP] Implement driver accept order flow with race protection")"
ISSUE_STATUS_MACHINE_NUM="$(issue_number_by_title "[MVP] Implement order lifecycle state machine")"
ISSUE_ACTIVE_TRIP_CARD_NUM="$(issue_number_by_title "[MVP] Build active trip card with next-action UX")"
ISSUE_CONTRACTS_NUM="$(issue_number_by_title "[MVP] Define orders API contracts and active trip summary")"
ISSUE_STATES_NUM="$(issue_number_by_title "[MVP] Add human-friendly loading, empty, and error states for orders")"
ISSUE_TESTS_NUM="$(issue_number_by_title "[MVP] Cover orders core with smoke and contract tests")"

echo "==> Шаг 3. Назначение milestone"

for num in \
  "$EPIC_NUM" \
  "$SUB_PASSENGER_NUM" \
  "$SUB_DRIVER_INTAKE_NUM" \
  "$SUB_LIFECYCLE_NUM" \
  "$SUB_ACTIVE_TRIP_NUM" \
  "$ISSUE_PASSENGER_FORM_NUM" \
  "$ISSUE_DRIVER_LIST_NUM" \
  "$ISSUE_ACCEPT_NUM" \
  "$ISSUE_STATUS_MACHINE_NUM" \
  "$ISSUE_ACTIVE_TRIP_CARD_NUM" \
  "$ISSUE_CONTRACTS_NUM" \
  "$ISSUE_STATES_NUM" \
  "$ISSUE_TESTS_NUM"
do
  assign_issue_to_milestone "$num" "$MILESTONE_NUM"
done

echo "==> Шаг 4. Финальные body"

cat > "$TMP_DIR/epic_orders_core_final.md" <<EOF2
## Epic: Orders Marketplace Core

### Milestone
- $MILESTONE_TITLE

### Goal
Implement the core order flow for passengers and drivers, from order creation to active trip completion.

### Why
Orders are the heart of the marketplace. The system should clearly support:
- passenger order creation
- driver order intake
- status transitions
- active trip handling
- predictable lifecycle updates

### Scope
- passenger order creation
- driver order intake
- order lifecycle
- active trip UX
- status transitions
- server-side order rules
- mobile-first operational flow

### Children
- #$SUB_PASSENGER_NUM Passenger Order Creation
- #$SUB_DRIVER_INTAKE_NUM Driver Order Intake
- #$SUB_LIFECYCLE_NUM Order Lifecycle
- #$SUB_ACTIVE_TRIP_NUM Active Trip UX

### MVP delivery path
1. #$ISSUE_CONTRACTS_NUM Orders API contracts and active trip summary
2. #$ISSUE_PASSENGER_FORM_NUM Passenger order form and confirmation flow
3. #$ISSUE_DRIVER_LIST_NUM Driver open orders list and cards
4. #$ISSUE_ACCEPT_NUM Driver accept order flow with race protection
5. #$ISSUE_STATUS_MACHINE_NUM Order lifecycle state machine
6. #$ISSUE_ACTIVE_TRIP_CARD_NUM Active trip card with next-action UX
7. #$ISSUE_STATES_NUM Human-friendly states for orders
8. #$ISSUE_TESTS_NUM Smoke and contract tests

### Success criteria
- passenger can create an order on mobile
- eligible driver can see and accept open orders
- lifecycle transitions are consistent across backend and UI
- active trip UX exposes current status and next action clearly
EOF2

cat > "$TMP_DIR/subepic_passenger_order_creation_final.md" <<EOF2
## Sub-epic: Passenger Order Creation

### Parent
- #$EPIC_NUM Orders Marketplace Core

### Milestone
- $MILESTONE_TITLE

### Goal
Build the passenger flow for creating and submitting taxi orders.

### Scope
- pickup address
- destination
- comment
- ride time
- scheduled rides
- confirmation step

### Children
- #$ISSUE_PASSENGER_FORM_NUM Implement passenger order form and confirmation flow
- #$ISSUE_STATES_NUM Add human-friendly loading, empty, and error states for orders
EOF2

cat > "$TMP_DIR/subepic_driver_order_intake_final.md" <<EOF2
## Sub-epic: Driver Order Intake

### Parent
- #$EPIC_NUM Orders Marketplace Core

### Milestone
- $MILESTONE_TITLE

### Goal
Allow eligible drivers to view, understand, and accept available orders.

### Scope
- open orders list
- order card
- order details
- accept action
- eligibility checks
- anti-double-accept protection

### Children
- #$ISSUE_DRIVER_LIST_NUM Build driver open orders list and order cards
- #$ISSUE_ACCEPT_NUM Implement driver accept order flow with race protection

### Related
- #$SUB_LIFECYCLE_NUM Order Lifecycle
EOF2

cat > "$TMP_DIR/subepic_order_lifecycle_final.md" <<EOF2
## Sub-epic: Order Lifecycle

### Parent
- #$EPIC_NUM Orders Marketplace Core

### Milestone
- $MILESTONE_TITLE

### Goal
Define a stable lifecycle for orders across backend and UI.

### Scope
- CREATED
- ACCEPTED
- ARRIVING
- ONTRIP
- DONE
- CANCELED
- EXPIRED
- transition rules

### Children
- #$ISSUE_STATUS_MACHINE_NUM Implement order lifecycle state machine
- #$ISSUE_CONTRACTS_NUM Define orders API contracts and active trip summary
- #$ISSUE_TESTS_NUM Cover orders core with smoke and contract tests
EOF2

cat > "$TMP_DIR/subepic_active_trip_ux_final.md" <<EOF2
## Sub-epic: Active Trip UX

### Parent
- #$EPIC_NUM Orders Marketplace Core

### Milestone
- $MILESTONE_TITLE

### Goal
Provide a focused operational screen for the active order.

### Scope
- active trip card
- route summary
- key trip actions
- current status
- next allowed action

### Children
- #$ISSUE_ACTIVE_TRIP_CARD_NUM Build active trip card with next-action UX
- #$ISSUE_STATES_NUM Add human-friendly loading, empty, and error states for orders

### Related
- #$SUB_LIFECYCLE_NUM Order Lifecycle
EOF2

cat > "$TMP_DIR/issue_passenger_form_final.md" <<EOF2
## Parent
- #$SUB_PASSENGER_NUM Passenger Order Creation

## Milestone
- $MILESTONE_TITLE

## Goal
Build the passenger taxi order form and confirmation flow.

### Related
- #$ISSUE_CONTRACTS_NUM Define orders API contracts and active trip summary
EOF2

cat > "$TMP_DIR/issue_driver_list_final.md" <<EOF2
## Parent
- #$SUB_DRIVER_INTAKE_NUM Driver Order Intake

## Milestone
- $MILESTONE_TITLE

## Goal
Build the driver-facing list of open orders and order cards.

### Related
- #$ISSUE_CONTRACTS_NUM Define orders API contracts and active trip summary
EOF2

cat > "$TMP_DIR/issue_accept_final.md" <<EOF2
## Parent
- #$SUB_DRIVER_INTAKE_NUM Driver Order Intake

## Milestone
- $MILESTONE_TITLE

## Goal
Implement driver order acceptance with race protection.

### Related
- #$ISSUE_STATUS_MACHINE_NUM Implement order lifecycle state machine
- #$ISSUE_CONTRACTS_NUM Define orders API contracts and active trip summary
EOF2

cat > "$TMP_DIR/issue_status_machine_final.md" <<EOF2
## Parent
- #$SUB_LIFECYCLE_NUM Order Lifecycle

## Milestone
- $MILESTONE_TITLE

## Goal
Implement the backend status machine for order lifecycle transitions.
EOF2

cat > "$TMP_DIR/issue_active_trip_card_final.md" <<EOF2
## Parent
- #$SUB_ACTIVE_TRIP_NUM Active Trip UX

## Milestone
- $MILESTONE_TITLE

## Goal
Build the active trip card for the driver with current status and next action.

### Related
- #$ISSUE_STATUS_MACHINE_NUM Implement order lifecycle state machine
EOF2

cat > "$TMP_DIR/issue_contracts_final.md" <<EOF2
## Parent
- #$SUB_LIFECYCLE_NUM Order Lifecycle

## Milestone
- $MILESTONE_TITLE

## Goal
Define API contracts for order creation, intake, and lifecycle updates.

### Used by
- #$ISSUE_PASSENGER_FORM_NUM Passenger order form and confirmation flow
- #$ISSUE_DRIVER_LIST_NUM Driver open orders list and order cards
- #$ISSUE_ACCEPT_NUM Driver accept order flow with race protection
- #$ISSUE_ACTIVE_TRIP_CARD_NUM Active trip card with next-action UX
EOF2

cat > "$TMP_DIR/issue_orders_states_final.md" <<EOF2
## Parent
- #$SUB_PASSENGER_NUM Passenger Order Creation
- #$SUB_ACTIVE_TRIP_NUM Active Trip UX

## Milestone
- $MILESTONE_TITLE

## Goal
Add clear loading, empty, error, and no-orders states for orders screens.
EOF2

cat > "$TMP_DIR/issue_orders_tests_final.md" <<EOF2
## Parent
- #$SUB_LIFECYCLE_NUM Order Lifecycle

## Milestone
- $MILESTONE_TITLE

## Goal
Cover Orders Marketplace Core MVP with smoke and contract tests.

### Related
- #$ISSUE_CONTRACTS_NUM Define orders API contracts and active trip summary
- #$ISSUE_STATUS_MACHINE_NUM Implement order lifecycle state machine
EOF2

update_issue_body "$EPIC_NUM" "$TMP_DIR/epic_orders_core_final.md"
update_issue_body "$SUB_PASSENGER_NUM" "$TMP_DIR/subepic_passenger_order_creation_final.md"
update_issue_body "$SUB_DRIVER_INTAKE_NUM" "$TMP_DIR/subepic_driver_order_intake_final.md"
update_issue_body "$SUB_LIFECYCLE_NUM" "$TMP_DIR/subepic_order_lifecycle_final.md"
update_issue_body "$SUB_ACTIVE_TRIP_NUM" "$TMP_DIR/subepic_active_trip_ux_final.md"
update_issue_body "$ISSUE_PASSENGER_FORM_NUM" "$TMP_DIR/issue_passenger_form_final.md"
update_issue_body "$ISSUE_DRIVER_LIST_NUM" "$TMP_DIR/issue_driver_list_final.md"
update_issue_body "$ISSUE_ACCEPT_NUM" "$TMP_DIR/issue_accept_final.md"
update_issue_body "$ISSUE_STATUS_MACHINE_NUM" "$TMP_DIR/issue_status_machine_final.md"
update_issue_body "$ISSUE_ACTIVE_TRIP_CARD_NUM" "$TMP_DIR/issue_active_trip_card_final.md"
update_issue_body "$ISSUE_CONTRACTS_NUM" "$TMP_DIR/issue_contracts_final.md"
update_issue_body "$ISSUE_STATES_NUM" "$TMP_DIR/issue_orders_states_final.md"
update_issue_body "$ISSUE_TESTS_NUM" "$TMP_DIR/issue_orders_tests_final.md"

echo "==> Шаг 5. Сводный комментарий в Epic"

EPIC_COMMENT_MARKER="<!-- orders-core-mvp-summary -->"

cat > "$TMP_DIR/epic_summary_comment.md" <<EOF2
$EPIC_COMMENT_MARKER

## Orders Marketplace Core MVP summary

### Milestone
- **$MILESTONE_TITLE**

### Created hierarchy
| Type | Issue | Link |
|---|---|---|
| Epic | #$EPIC_NUM Orders Marketplace Core | https://github.com/$REPO/issues/$EPIC_NUM |
| Sub-epic | #$SUB_PASSENGER_NUM Passenger Order Creation | https://github.com/$REPO/issues/$SUB_PASSENGER_NUM |
| Sub-epic | #$SUB_DRIVER_INTAKE_NUM Driver Order Intake | https://github.com/$REPO/issues/$SUB_DRIVER_INTAKE_NUM |
| Sub-epic | #$SUB_LIFECYCLE_NUM Order Lifecycle | https://github.com/$REPO/issues/$SUB_LIFECYCLE_NUM |
| Sub-epic | #$SUB_ACTIVE_TRIP_NUM Active Trip UX | https://github.com/$REPO/issues/$SUB_ACTIVE_TRIP_NUM |

### MVP issues
| # | Title | Area |
|---|---|---|
| #$ISSUE_PASSENGER_FORM_NUM | Implement passenger order form and confirmation flow | passenger / frontend / ux |
| #$ISSUE_DRIVER_LIST_NUM | Build driver open orders list and order cards | driver / frontend / ux |
| #$ISSUE_ACCEPT_NUM | Implement driver accept order flow with race protection | driver / backend / api |
| #$ISSUE_STATUS_MACHINE_NUM | Implement order lifecycle state machine | backend / api |
| #$ISSUE_ACTIVE_TRIP_CARD_NUM | Build active trip card with next-action UX | driver / frontend / ux |
| #$ISSUE_CONTRACTS_NUM | Define orders API contracts and active trip summary | backend / api |
| #$ISSUE_STATES_NUM | Add human-friendly loading, empty, and error states for orders | frontend / ux |
| #$ISSUE_TESTS_NUM | Cover orders core with smoke and contract tests | backend / frontend / api |

### Recommended implementation order
1. #$ISSUE_CONTRACTS_NUM
2. #$ISSUE_PASSENGER_FORM_NUM
3. #$ISSUE_DRIVER_LIST_NUM
4. #$ISSUE_ACCEPT_NUM
5. #$ISSUE_STATUS_MACHINE_NUM
6. #$ISSUE_ACTIVE_TRIP_CARD_NUM
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
