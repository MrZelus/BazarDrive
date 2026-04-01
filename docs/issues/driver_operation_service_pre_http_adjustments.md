# Driver Operation Service Pre-HTTP Adjustments

Этот документ фиксирует **самый узкий оставшийся backend blocker перед переходом к HTTP wiring**:

**привести `app/services/driver_operation_service.py` в состояние, где outward runtime semantics больше не расходятся с canonical driver contract.**

---

## 1. Почему именно этот файл сейчас главный блокер

После service re-check стало видно, что три из четырёх ключевых backend services уже достаточно близки к canonical driver contract:

- `driver_status_service.py` — в целом OK
- `driver_permissions_service.py` — mostly OK
- `driver_notifications_service.py` — OK

Но `driver_operation_service.py` остаётся смешанным слоем:

- часть полей уже canonical
- часть runtime/persistence semantics ещё legacy-ish

Именно отсюда сейчас течёт последний заметный drift в сторону будущего HTTP contract.

---

## 2. Main problems in the current file

На текущем шаге в `app/services/driver_operation_service.py` остаются такие проблемы:

### 2.1. `completed` vs `done`

В одном и том же service-layer completion path одновременно существуют:

- legacy runtime/journal `completed`
- canonical `order_status = done`

Это создаёт прямое расхождение между:

- persisted/runtime meaning
- outward response meaning

### 2.2. `assigned` leaks outward as runtime `status`

`assign_order(...)` сейчас возвращает outward `status = "assigned"`.

Пока semantic decision по `assigned` не закрыт, это опасно для будущего HTTP слоя:

- API может случайно протащить ambiguous status наружу
- frontend later может принять internal semantics за canonical state

### 2.3. Runtime `status` vs canonical `order_status`

В operation layer пока нет жёсткой гарантии, что outward `status` и outward canonical fields не расходятся по смыслу.

Для pre-HTTP readiness это слишком хрупко.

---

## 3. Goal

Сделать так, чтобы `driver_operation_service.py`:

- не плодил новый status drift;
- не отдавал двусмысленный outward `status` там, где уже нужен canonical смысл;
- был достаточно чистым backend source для HTTP normalization/adapters.

---

## 4. Required adjustments

## 4.1. Apply `completed -> done`

Нужно завершить rollout, уже описанный в отдельных prep-docs.

### Required outcome

- новые completion writes используют `done`
- runtime completion response не использует `completed`
- canonical `order_status = done` и runtime `status` не расходятся

### Minimal change-set

- `ORDER_STATUSES`
- `_record_order_status_transition(...)`
- `complete_order(...)`
- runtime success payload for completion

---

## 4.2. Decide outward meaning of `status`

Нужно принять явное правило:

### Option A
Outward `status` in operation responses is allowed to remain transitional/legacy-like.

### Option B
Outward `status` in operation responses must become canonical whenever a canonical field already exists.

### Recommended direction

**Prefer Option B** for pre-HTTP stability.

Почему:

- HTTP adapters later become simpler
- меньше риска, что HTTP payload accidentally mixes two status languages
- меньше шансов, что frontend/UI later consumes the wrong field

Если canonical `order_status` already exists, then outward `status` should ideally not contradict it.

---

## 4.3. Contain `assigned`

До финального semantic decision по `assigned` нужно как минимум:

- не делать его implicit canonical outward truth
- не использовать его как внешний current order state для future HTTP contract

### Minimal safe rule

Пока `assigned` не разобран до конца:

- treat it as internal/runtime-only marker
- do not let future HTTP normalization expose it as the canonical main order status

Это не обязательно означает немедленный кодовый рефактор в этом файле на этом шаге.
Но это означает, что file-level behavior must not leave this ambiguous for later HTTP wiring.

---

## 5. Recommended practical sequence inside this file

### Step 1
Применить `completed -> done`

### Step 2
Проверить, не осталось ли outward response path, где `status` конфликтует с canonical `order_status`

### Step 3
Пометить/ограничить `assigned` so it is not treated as canonical external order state

### Step 4
Только после этого считать operation layer pre-HTTP ready

---

## 6. What should be true after adjustments

После этих правок `driver_operation_service.py` должен удовлетворять таким условиям:

- [ ] completion flow no longer emits `completed` for new runtime/persistence writes
- [ ] outward completion response no longer says `status = completed`
- [ ] canonical `order_status` and outward `status` are not semantically contradictory
- [ ] `assigned` is contained enough not to pollute HTTP canonical contract
- [ ] operation layer can be safely wrapped by HTTP adapters without reintroducing status ambiguity

---

## 7. What this step does **not** require yet

На этом шаге не обязательно делать:

- historical migration of old `completed` rows
- final resolution of all `assigned` business semantics in one commit
- big schema refactor
- waybill/trip-sheet refactor inside operation service

Это именно **narrow pre-HTTP hardening step**.

---

## 8. Acceptance criteria

- [ ] `driver_operation_service.py` больше не имеет явного `completed` / `done` drift
- [ ] outward runtime semantics не конфликтуют с canonical fields
- [ ] `assigned` не рассматривается молча как canonical external status
- [ ] после этого operation layer перестаёт быть главным blocker перед HTTP

---

## 9. Follow-up after this file is stabilized

После stabilizing `driver_operation_service.py` логичный следующий шаг:

1. finalize one backend source for waybill → `TripSheetStatus`
2. re-check pre-HTTP checklist once more
3. move into HTTP wiring
4. activate API contract tests
5. then only later proceed toward frontend gating

Этот файл сейчас как последний зубец шестерни: пока он цепляется криво, HTTP layer будет дрожать. Когда он выровнен, дальше уже можно входить в wiring намного увереннее.
