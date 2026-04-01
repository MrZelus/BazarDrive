# Driver Persisted Status Alignment Plan

Этот документ фиксирует следующий узкий технический шаг для driver domain в BazarDrive:

**выровнять реальные persisted status values в БД и repository/runtime слоях с canonical driver contract.**

---

## 1. Почему это нужно сейчас

В проекте уже есть canonical driver contract layer:

- `app/models/driver_enums.py`
- `app/services/driver_status_service.py`
- `app/services/driver_permissions_service.py`
- `app/services/driver_notifications_service.py`
- HTTP contract helpers/adapters
- wiring plan для `app/api/http_handlers.py`

Но runtime/repository слой всё ещё использует legacy-ish статусы в отдельных местах.

Самый заметный пример:

- canonical order contract: `created`, `accepted`, `arriving`, `ontrip`, `done`, `canceled`
- runtime journal statuses: `assigned`, `accepted`, `completed`, `canceled`

Это создаёт разрыв между:

- docs and backend contracts;
- persisted DB truth;
- API contract expectations;
- будущим frontend gating.

---

## 2. Цель

Добиться, чтобы persisted layer и runtime driver flow не противоречили canonical contract.

Итогом должно быть одно из двух:

### Вариант A
Persisted values сами становятся canonical.

### Вариант B
Остаются legacy persisted values, но появляется **явный и ограниченный mapping layer** между DB/runtime и canonical API/backend contract.

Предпочтителен вариант A, если он не требует чрезмерно дорогой миграции.

---

## 3. Scope

### Входит

- audit persisted statuses в driver-related таблицах;
- audit repository functions, которые пишут и читают status values;
- mapping между DB values и canonical enums;
- решение по cleanup vs adapter mapping;
- подготовка backend follow-up перед HTTP wiring.

### Не входит

- frontend UI gating;
- E2E сценарии;
- новые UX docs;
- массовый рефактор unrelated feed/guest domain.

---

## 4. Canonical contract to align with

### Order status

Canonical values:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### Trip sheet status

Canonical values:

- `missing`
- `open`
- `requires_closing`
- `closed`

### Document status

Canonical values:

- `missing`
- `uploaded`
- `checking`
- `approved`
- `rejected`
- `expired`

### Shift status

Canonical values:

- `offline`
- `ready`
- `online`
- `busy`
- `ending`
- `closed`

### Profile status

Canonical values:

- `draft`
- `incomplete`
- `pending_verification`
- `approved`
- `rejected`
- `blocked`

---

## 5. Known mismatch to investigate first

### 5.1. Order journal status mismatch

Проверить и устранить расхождение между:

- canonical order contract (`created`, `accepted`, `arriving`, `ontrip`, `done`, `canceled`)
- runtime/order journal statuses (`assigned`, `accepted`, `completed`, `canceled`)

Нужно ответить на вопросы:

- где в persisted layer живёт `created`;
- чем сейчас заменён `created`;
- чем сейчас заменён `done` (`completed` vs `done`);
- где должны храниться `arriving` и `ontrip`;
- допустим ли `assigned` как internal/runtime-only status;
- должен ли `assigned` вообще попадать в persisted truth.

---

## 6. Tables and repository paths to audit

Проверить реальные DB tables / repository paths, связанные с driver domain.

### 6.1. `order_journal_records`

Проверить:

- [ ] какие значения реально пишутся в `order_status`;
- [ ] есть ли legacy rows со `assigned`/`completed`;
- [ ] нужен ли migration/update path для historical rows;
- [ ] должен ли journal хранить canonical statuses или history-friendly internal statuses.

### 6.2. `driver_documents`

Проверить:

- [ ] какие значения реально используются в `status`;
- [ ] как в одном поле живут document statuses и waybill flow;
- [ ] не конфликтует ли `closed` как waybill status с общим document contract;
- [ ] нужен ли явный adapter между `driver_documents` и `TripSheetStatus`.

### 6.3. `driver_compliance_profiles`

Проверить:

- [ ] какие compliance/status fields реально участвуют в readiness;
- [ ] как profile approval/blocking маппится к canonical profile status;
- [ ] нет ли параллельных competing status sources.

### 6.4. `vehicle_compliance`

Проверить:

- [ ] можно ли из persisted vehicle compliance построить `has_valid_vehicle`;
- [ ] какие statuses/expiry fields реально определяют readiness;
- [ ] нет ли неоднозначности между vehicle status и driver eligibility.

### 6.5. Waybill-related repository functions

Проверить:

- `get_active_waybill()`
- `close_driver_waybill()`
- create/update paths для `type = 'waybill'`

Нужно ответить:

- [ ] где живёт `open`;
- [ ] где живёт `requires_closing`;
- [ ] как вычислять `missing`;
- [ ] не нужен ли отдельный derived trip sheet adapter.

---

## 7. Repository/runtime audit checklist

Проверить `app/db/repository.py` и runtime services на предмет прямой записи/чтения legacy statuses.

### 7.1. Write paths

Найти все места, где status values записываются в БД:

- [ ] order journal writes;
- [ ] driver documents create/update;
- [ ] waybill close/open flow;
- [ ] compliance/profile status updates.

Для каждого write path проверить:

- [ ] пишет canonical value или legacy value;
- [ ] нужен migration fix или runtime mapping;
- [ ] есть ли риск появления новых non-canonical rows.

### 7.2. Read paths

Найти все места, где status values читаются и интерпретируются:

- [ ] eligibility computation;
- [ ] permissions checks;
- [ ] operation services;
- [ ] HTTP payload formation;
- [ ] frontend-facing repository functions.

Для каждого read path проверить:

- [ ] умеет ли он читать только canonical values;
- [ ] есть ли скрытое ожидание legacy values;
- [ ] нет ли двусмысленной логики по `completed` vs `done`, `assigned` vs `created`.

---

## 8. Decision framework: cleanup or mapping

По итогам аудита принять решение по каждому mismatch.

### 8.1. Cleanup preferred when

Выбирать cleanup/migration, если:

- mismatch локальный и понятный;
- legacy values немногочисленны;
- canonical replacement очевиден;
- cleanup упростит future API/frontend logic.

Примеры:

- `completed` -> `done`
- прямое сохранение canonical order statuses в journal

### 8.2. Mapping allowed when

Выбирать adapter mapping, если:

- legacy value нужен для backward compatibility;
- persisted shape сложно менять прямо сейчас;
- можно чётко ограничить mapping в одном месте;
- mapping не течёт во frontend/API напрямую.

Важно:

mapping не должен расползаться по нескольким слоям.
Если он нужен, он должен жить централизованно и быть явно протестирован.

---

## 9. Expected output of the audit

После аудита должен появиться короткий результат в одном из форматов.

### Формат A. No blocking schema mismatch

- persisted layer признан совместимым;
- runtime adjustments минимальны;
- можно переходить к HTTP wiring.

### Формат B. Blocking mismatch list

Список вида:

1. таблица / поле;
2. текущее persisted значение;
3. canonical target;
4. recommended fix:
   - migration
   - repository cleanup
   - runtime adapter mapping
5. влияние на API/frontend.

---

## 10. Follow-up after alignment

После завершения persisted status alignment следующий шаг:

### 10.1. HTTP wiring

Применить mechanical wiring по:

- `docs/issues/driver_http_handlers_wiring_plan.md`

### 10.2. Activate API contract tests

Снять skip и активировать:

- `tests/test_driver_api_go_online_http_contract.py`
- `tests/test_driver_api_accept_order_http_contract.py`
- `tests/test_driver_api_shift_http_contract.py`
- при необходимости добавить `tests/test_driver_api_order_transition_http_contract.py`

### 10.3. Only then frontend gating

Когда API уже отдаёт устойчивые canonical fields:

- `error.code`
- `event_name`
- `shift_status`
- `order_status`
- `trip_sheet_status`

только тогда идти в:

- UI gating tests;
- CTA rules;
- blocker banners;
- action visibility.

---

## 11. Acceptance criteria

- [ ] найдено, где именно persisted layer расходится с canonical contract;
- [ ] составлена таблица `DB value -> canonical value` для driver domain;
- [ ] order journal statuses проверены и решение принято;
- [ ] waybill/trip-sheet mapping проверен и решение принято;
- [ ] repository write paths проверены;
- [ ] repository read paths проверены;
- [ ] определено, где нужен cleanup, а где допустим centralized mapping;
- [ ] после этого можно безопасно переходить к HTTP wiring и API contract activation.

---

## 12. Practical priority

Правильный ближайший порядок такой:

1. **Persisted status audit**
2. **Cleanup or centralized mapping**
3. **Backend service re-check**
4. **HTTP wiring**
5. **API contract activation**
6. **Frontend gating**
7. **E2E**

Это убирает разрыв между repository truth и canonical driver contract до того, как UI начнёт зависеть от этих данных.
