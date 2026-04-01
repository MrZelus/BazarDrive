# Driver Status Cleanup and Mapping Plan

Этот документ фиксирует следующий шаг после первичной инвентаризации статусов в driver domain:

**для каждого найденного расхождения решить, что чистим в persisted/runtime layer, а что временно держим через централизованный mapping.**

---

## 1. Основание

Документ опирается на уже добавленные repo-backed материалы:

- `docs/issues/driver_db_backend_audit_plan.md`
- `docs/issues/driver_persisted_status_alignment_plan.md`
- `docs/issues/driver_status_mapping_inventory.md`

Их вывод в коротком виде:

- canonical contract layer уже существует;
- repository/runtime layer местами ещё живёт на legacy-ish values;
- самый заметный конфликт сейчас в order status naming;
- waybill/trip sheet пока смешан с `driver_documents.status`.

---

## 2. Цель

Сформировать **практическое решение по каждому mismatch** до HTTP wiring и до frontend gating.

Итогом должно стать:

- список статусов, которые нужно cleanup-нуть в persisted/runtime layer;
- список статусов, которые допустимо временно адаптировать через centralized mapping;
- ограничение области mapping, чтобы он не расползался по API/UI;
- понятный follow-up для backend и HTTP слоя.

---

## 3. Правило принятия решения

### Cleanup выбирать по умолчанию

Cleanup предпочтителен, если:

- legacy value локальный и понятный;
- canonical replacement очевиден;
- cleanup упростит repository, backend, API и frontend;
- риск миграции ограничен.

### Mapping допустим только как узкий переходный мост

Centralized mapping допустим, если:

- persisted shape сложно менять прямо сейчас;
- есть backward compatibility reasons;
- mapping можно сосредоточить в одном месте;
- mapping не течёт напрямую во frontend/UI logic.

### Плохой вариант

Плохой вариант — когда mapping дублируется:

- в repository;
- в services;
- в HTTP adapters;
- во frontend.

Так делать нельзя.

---

## 4. Mismatch-by-mismatch decisions

## 4.1. `completed` vs `done`

### Текущее состояние

- runtime/order journal использует `completed`;
- canonical contract использует `done`.

### Рекомендация

**Cleanup preferred.**

### Почему

- смысл совпадает почти один к одному;
- `done` уже зафиксирован в canonical enums и service contracts;
- это прямой rename без сложной смысловой неоднозначности.

### План

- [ ] найти все write paths, которые пишут `completed`;
- [ ] перевести новые записи на `done` или canonical `OrderStatus.DONE.value`;
- [ ] решить, нужен ли one-time migration/update для historical rows;
- [ ] не допускать появления новых `completed` rows после cleanup.

### Допустимый временный mapping

Если migration не делается сразу:

- centralized read mapping: `completed -> done`

Но только временно и только в одном backend mapping layer.

---

## 4.2. `assigned` vs `created`

### Текущее состояние

- runtime/order journal использует `assigned`;
- canonical contract не содержит `assigned`, но содержит `created`.

### Проблема

Смысл неочевиден:

- `assigned` может означать внутреннее событие выдачи заказа водителю;
- `created` — canonical open order state до принятия;
- эти статусы не обязательно идентичны.

### Рекомендация

**Сначала semantic audit, потом решение.**

### Возможные варианты

#### Вариант A. `assigned` на самом деле заменяет `created`
Тогда:

- cleanup to `created`
- убрать `assigned` из persisted truth

#### Вариант B. `assigned` — внутреннее техническое событие, а не canonical order status
Тогда:

- не использовать `assigned` как внешний order status
- либо держать его как internal event only
- либо вынести в event/history поле, а не в canonical status interpretation

#### Вариант C. `assigned` реально нужен как отдельный runtime event
Тогда:

- не подменять им canonical `order_status`
- сделать явное разделение:
  - persisted history event: `assigned`
  - canonical current order status: `created` или иное корректное состояние

### План

- [ ] найти все места, где пишется/читается `assigned`;
- [ ] определить бизнес-смысл `assigned`;
- [ ] решить, это status или event;
- [ ] если это event, не пропускать его наружу как canonical `order_status`.

---

## 4.3. `driver_documents.status` mixing document and waybill lifecycle

### Текущее состояние

В одном поле `driver_documents.status` живут:

- обычные document review states (`uploaded`, `checking`, `approved`, `rejected`);
- waybill flow (`open`, `closed`);
- потенциально позже `expired`.

### Проблема

Это смешивает два домена:

- document verification lifecycle;
- trip sheet lifecycle.

### Рекомендация

**Не делать большой schema split прямо сейчас, а ввести centralized adapter mapping для waybill/trip-sheet interpretation.**

### Почему

- обычные document statuses уже близки к canonical contract;
- waybill уже технически хранится в `driver_documents`;
- большой schema split сейчас может разрастись сильнее, чем нужно до API stabilization.

### План

- [ ] оставить `driver_documents` как persisted source for waybill for now;
- [ ] сделать явный mapping rule:
  - `driver_documents(type='waybill', status='open') -> TripSheetStatus.OPEN`
  - `driver_documents(type='waybill', status='closed') -> TripSheetStatus.CLOSED`
  - absence of required row -> `TripSheetStatus.MISSING`
- [ ] отдельно решить, как вычислять `TripSheetStatus.REQUIRES_CLOSING`.

### Ограничение

Этот mapping должен жить в одном backend layer, а не в UI.

---

## 4.4. `requires_closing` gap

### Текущее состояние

Canonical trip sheet contract требует:

- `missing`
- `open`
- `requires_closing`
- `closed`

Но `requires_closing` пока не подтверждён как persisted value.

### Рекомендация

**Treat as derived until proven persisted.**

### Почему

- уже есть waybill close flow;
- уже есть close payload fields;
- возможно, `requires_closing` логически вычисляется после окончания смены или после наличия незаполненного close block.

### План

- [ ] найти shift-end / close-required conditions;
- [ ] определить derived rule для `requires_closing`;
- [ ] не добавлять новое persisted status поле без необходимости;
- [ ] если позже появится явная нужда, вернуться к schema change отдельно.

---

## 4.5. `expired` for driver documents

### Текущее состояние

Canonical document contract включает `expired`, но в текущих открытых write/read paths он ещё не подтверждён как реально записываемый статус.

### Рекомендация

**Schema and write-path confirmation first.**

### План

- [ ] найти, пишется ли `expired` где-либо реально;
- [ ] если нет, определить, должен ли он быть persisted или derived by date check;
- [ ] если expiry logic нужна для readiness, зафиксировать единый backend rule.

---

## 5. Centralized mapping layer requirements

Если mapping всё же нужен, он должен соответствовать правилам ниже.

### 5.1. One place only

Mapping должен жить в одном backend module/service.

### 5.2. Never leak ambiguity to frontend

Frontend не должен знать про:

- `completed`
- `assigned`
- другие legacy persisted values

Frontend должен получать только canonical fields.

### 5.3. Explicit tests

На mapping layer нужны явные tests:

- `completed -> done`
- `waybill open -> TripSheetStatus.OPEN`
- `waybill closed -> TripSheetStatus.CLOSED`
- `missing waybill -> TripSheetStatus.MISSING`
- `assigned` handled according to chosen semantic decision

---

## 6. Cleanup/mapping action table

| Mismatch | Recommended action | Priority |
| --- | --- | --- |
| `completed` vs `done` | cleanup preferred | high |
| `assigned` vs `created` | semantic audit first, then cleanup or event split | high |
| mixed waybill/document status field | centralized backend adapter | high |
| missing `requires_closing` state | derived rule first | high |
| unconfirmed `expired` write path | confirm then choose persisted vs derived | medium |
| unconfirmed shift persistence | schema discovery first | medium |
| unclear canonical profile persisted source | schema discovery first | medium |

---

## 7. Practical execution order

### Phase 1. Quick wins

- [ ] normalize `completed -> done` write paths;
- [ ] define temporary centralized read mapping if cleanup is staged;
- [ ] add explicit waybill -> trip sheet adapter rules.

### Phase 2. Ambiguous cases

- [ ] resolve business meaning of `assigned`;
- [ ] resolve `requires_closing` derivation;
- [ ] confirm `expired` behavior.

### Phase 3. Re-check backend layer

- [ ] re-check `driver_status_service` against new rules;
- [ ] re-check `driver_permissions_service` inputs;
- [ ] re-check runtime operation responses.

### Phase 4. Only then continue ladder

1. status cleanup/mapping
2. backend service re-check
3. HTTP wiring
4. API contract activation
5. frontend gating
6. E2E

---

## 8. Acceptance criteria

- [ ] для каждого major mismatch принято явное решение: cleanup или mapping;
- [ ] `completed` strategy decided;
- [ ] `assigned` semantics decided;
- [ ] waybill/trip-sheet adapter rule described;
- [ ] `requires_closing` handling described;
- [ ] mapping layer, если нужен, ограничен одним backend place;
- [ ] после этого можно переходить к реальному backend implementation step перед HTTP wiring.
