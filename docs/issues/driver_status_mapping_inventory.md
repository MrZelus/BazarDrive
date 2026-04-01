# Driver Status Mapping Inventory

Этот документ фиксирует **первую инвентаризацию соответствия между persisted DB/runtime values и canonical driver contract**.

Документ не претендует на финальную схему. Его задача — быстро показать:

- где совпадение уже есть;
- где есть явный конфликт;
- где данных пока недостаточно;
- что нужно добрать перед HTTP wiring и frontend gating.

---

## 1. Источники для инвентаризации

На текущем шаге инвентаризация основана на:

- `app/models/driver_enums.py`
- `app/services/driver_status_service.py`
- `app/services/driver_operation_service.py`
- `app/db/repository.py`
- `app/db/migrator.py`
- `migrations/001_init.sql`

Важно:

- driver domain таблицы уже используются через `app/db/repository.py`;
- полный набор migration SQL по driver-таблицам ещё нужно добрать отдельно;
- поэтому ниже есть поля со статусом **unknown / needs schema check**.

---

## 2. Canonical reference

### Order status

Canonical contract:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### Trip sheet status

Canonical contract:

- `missing`
- `open`
- `requires_closing`
- `closed`

### Document status

Canonical contract:

- `missing`
- `uploaded`
- `checking`
- `approved`
- `rejected`
- `expired`

### Shift status

Canonical contract:

- `offline`
- `ready`
- `online`
- `busy`
- `ending`
- `closed`

### Profile status

Canonical contract:

- `draft`
- `incomplete`
- `pending_verification`
- `approved`
- `rejected`
- `blocked`

---

## 3. Order status inventory

### 3.1. What canonical layer expects

Backend contract expects order states:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### 3.2. What runtime layer currently writes

`app/services/driver_operation_service.py` currently uses runtime journal statuses:

- `assigned`
- `accepted`
- `completed`
- `canceled`

These values are written into `order_journal_records.order_status` through repository writes.

### 3.3. Initial mapping table

| Persisted / runtime value | Canonical target | Status |
| --- | --- | --- |
| `accepted` | `accepted` | exact match |
| `canceled` | `canceled` | exact match |
| `completed` | `done` | mismatch |
| `assigned` | `created` ? | ambiguous |
| `created` | `created` | not yet confirmed in persisted layer |
| `arriving` | `arriving` | not yet confirmed in persisted layer |
| `ontrip` | `ontrip` | not yet confirmed in persisted layer |

### 3.4. Findings

- `completed -> done` is a likely direct rename/mapping case.
- `assigned` is ambiguous:
  - it may be an internal pre-accept state;
  - it may currently substitute for `created`;
  - it may not belong in canonical persisted truth at all.
- `arriving` and `ontrip` exist in canonical contract but are not yet confirmed in runtime persistence.

### 3.5. Required follow-up

- [ ] inspect all repository write paths that touch order status;
- [ ] inspect whether any other table stores order state besides journal;
- [ ] decide whether `assigned` stays internal-only or is migrated/mapped;
- [ ] decide whether `completed` is migrated to `done` or centrally adapted.

---

## 4. Driver documents status inventory

### 4.1. What canonical layer expects

Canonical document states:

- `missing`
- `uploaded`
- `checking`
- `approved`
- `rejected`
- `expired`

### 4.2. What repository layer currently exposes

`driver_documents.status` is currently used in repository functions and visibly supports:

- `uploaded`
- `checking`
- `approved`
- `rejected`
- `closed` (for waybill close flow)
- `open` (via active waybill lookup)

### 4.3. Initial mapping table

| Persisted value in `driver_documents.status` | Canonical target | Status |
| --- | --- | --- |
| `uploaded` | `uploaded` | exact match |
| `checking` | `checking` | exact match |
| `approved` | `approved` | exact match |
| `rejected` | `rejected` | exact match |
| `expired` | `expired` | not yet confirmed in live write/read paths |
| `open` | `TripSheetStatus.OPEN` when `type='waybill'` | derived / mixed-domain |
| `closed` | `TripSheetStatus.CLOSED` when `type='waybill'` | derived / mixed-domain |
| `missing` | `missing` | derived, not persisted row |

### 4.4. Findings

- `driver_documents` mixes two concerns:
  - ordinary document review lifecycle;
  - waybill / trip sheet lifecycle.
- For ordinary docs, the contract mostly aligns already.
- For waybill, the same `status` field is acting as trip-sheet state carrier.
- `missing` appears to be derived from absence of required row, not a persisted value.

### 4.5. Required follow-up

- [ ] confirm whether any non-waybill document can ever get `open` / `closed`;
- [ ] confirm whether `expired` is actually written anywhere or only planned;
- [ ] define explicit adapter rule: `driver_documents(type='waybill') -> TripSheetStatus`;
- [ ] decide whether `requires_closing` is persisted anywhere or must be derived.

---

## 5. Trip sheet / waybill status inventory

### 5.1. What canonical layer expects

Canonical trip sheet states:

- `missing`
- `open`
- `requires_closing`
- `closed`

### 5.2. What repository layer currently shows

Waybill appears to be stored as:

- row in `driver_documents`
- with `type = 'waybill'`
- active waybill lookup expects `status = 'open'`
- close flow writes `status = 'closed'`

### 5.3. Initial mapping table

| DB reality | Canonical target | Status |
| --- | --- | --- |
| no active waybill row | `missing` | derived |
| `driver_documents(type='waybill', status='open')` | `open` | exact-ish via adapter |
| `driver_documents(type='waybill', status='closed')` | `closed` | exact-ish via adapter |
| unresolved close-needed condition | `requires_closing` | not yet confirmed |

### 5.4. Findings

- `missing`, `open`, and `closed` look mappable already.
- `requires_closing` is the key gap.
- It is still unclear whether `requires_closing`:
  - exists in persisted form;
  - should be derived from shift-end logic;
  - should be introduced explicitly later.

### 5.5. Required follow-up

- [ ] inspect repository/migration layer for any field related to close-required state;
- [ ] inspect shift-end flow for implied trip-sheet state;
- [ ] decide whether `requires_closing` is persisted or computed.

---

## 6. Shift status inventory

### 6.1. What canonical layer expects

Canonical shift states:

- `offline`
- `ready`
- `online`
- `busy`
- `ending`
- `closed`

### 6.2. What runtime layer currently confirms

Runtime service confirms at least:

- `online` is returned by `go_online()`;
- canonical shift status values exist in enums and status service;
- persisted storage for shift status is not yet confirmed from currently opened schema files.

### 6.3. Initial mapping table

| Value | Canonical target | Status |
| --- | --- | --- |
| `online` | `online` | confirmed in runtime response |
| `offline` | `offline` | contract only, persisted source not yet confirmed |
| `ready` | `ready` | contract only, persisted source not yet confirmed |
| `busy` | `busy` | contract only, persisted source not yet confirmed |
| `ending` | `ending` | contract only, persisted source not yet confirmed |
| `closed` | `closed` | contract only, persisted source not yet confirmed |

### 6.4. Findings

- shift contract exists in code;
- persisted source of truth for shift state is still not confirmed in opened schema files;
- shift may currently be runtime/service-driven rather than durably stored.

### 6.5. Required follow-up

- [ ] find actual shift persistence path;
- [ ] inspect migrations for shift-related table/column;
- [ ] determine whether shift state is persisted, derived, or partially ephemeral.

---

## 7. Profile status inventory

### 7.1. What canonical layer expects

Canonical profile states:

- `draft`
- `incomplete`
- `pending_verification`
- `approved`
- `rejected`
- `blocked`

### 7.2. What repository layer currently confirms

Repository layer clearly exposes driver-related profile/compliance tables, but the exact persisted field that maps directly to canonical profile status is not yet confirmed from the opened schema files.

There are likely relevant fields across:

- `driver_compliance_profiles`
- legal/compliance status fields
- compliance checks

### 7.3. Initial mapping table

| DB/runtime value | Canonical target | Status |
| --- | --- | --- |
| `approved` | `approved` | likely but needs schema check |
| `blocked` | `blocked` | likely via compliance/block reason, needs schema check |
| `pending_verification` | `pending_verification` | not yet confirmed |
| `rejected` | `rejected` | not yet confirmed |
| `draft` | `draft` | not yet confirmed |
| `incomplete` | `incomplete` | not yet confirmed |

### 7.4. Findings

- profile status is still the least grounded persisted mapping in the currently opened files;
- readiness logic probably depends on a blend of compliance/profile facts rather than one clean status column;
- this area needs schema-level confirmation before frontend gating.

### 7.5. Required follow-up

- [ ] inspect actual profile table schema;
- [ ] identify single source of truth or define derived profile status mapping;
- [ ] confirm blocked/approved/rejected transitions in persisted layer.

---

## 8. Vehicle and compliance readiness inventory

These are not canonical statuses in the same sense as order/trip-sheet/document statuses, but they feed eligibility.

### Confirmed repository-backed facts

Repository already has tables/functions around:

- `vehicle_compliance`
- `driver_compliance_profiles`
- `driver_legal_profile`
- `compliance_checks`

### Current interpretation

| DB/runtime fact | Canonical consumer | Status |
| --- | --- | --- |
| vehicle compliance validity | `has_valid_vehicle` | concept confirmed, exact mapping needs schema check |
| required documents validity | `has_required_documents` | concept confirmed, exact rule needs tightening |
| active/open waybill | `trip_sheet_ok` | partially confirmed |
| compliance blockers | `hard_blockers` | concept confirmed, exact mapping needs schema check |

### Required follow-up

- [ ] identify exact fields that define valid vehicle;
- [ ] identify exact fields that define hard blocker;
- [ ] map compliance/profile DB facts to `compute_eligibility()` inputs explicitly.

---

## 9. Priority mismatch list

### High priority

1. `completed` vs `done`
2. `assigned` vs `created` or internal-only state
3. waybill status mixed into `driver_documents.status`
4. missing confirmation for `requires_closing`

### Medium priority

5. exact persisted source for shift status
6. exact persisted source for canonical profile status
7. confirmation of real `expired` write path for documents

---

## 10. Recommended next steps

### Step 1. Finish schema discovery

Need to inspect remaining migration SQL / schema definitions for:

- `driver_documents`
- `order_journal_records`
- `driver_compliance_profiles`
- `vehicle_compliance`
- any shift-related table or column

### Step 2. Decide cleanup vs mapping

Per mismatch:

- `completed` -> likely cleanup to `done`
- `assigned` -> either remove from persisted truth or map centrally
- `waybill` -> explicit adapter from `driver_documents` to `TripSheetStatus`

### Step 3. Only then continue the ladder

1. persisted status alignment
2. backend service re-check
3. HTTP wiring
4. API contract activation
5. frontend gating
6. E2E

---

## 11. Acceptance criteria for this inventory phase

- [ ] first DB/runtime to canonical mapping inventory exists in repo;
- [ ] confirmed matches are separated from ambiguous mappings;
- [ ] blocking mismatches are explicitly listed;
- [ ] next schema discovery targets are named;
- [ ] this inventory can be used as input for persisted status cleanup/mapping work.
