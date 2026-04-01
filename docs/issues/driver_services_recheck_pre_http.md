# Driver Backend Services Re-check Before HTTP

Этот документ фиксирует **следующий обязательный backend step перед переходом к HTTP wiring**:

**перепроверить ключевые driver services против уже зафиксированных status-alignment решений и canonical contract.**

---

## 1. Почему это сейчас главный блокер

На pre-HTTP checklist уже видно, что главный NO-GO блокер сейчас не в docs и не в общей концепции, а в том, что backend services ещё не перепроверены как единый truth path после накопившихся решений вокруг:

- canonical statuses
- `completed -> done`
- `assigned` semantics
- waybill → trip-sheet mapping
- read/write discipline

Если этот re-check не сделать, HTTP wiring может стать не интеграцией, а транспортировкой ещё неустойчивой backend truth наружу.

---

## 2. Цель

Подтвердить, что service layer:

- не противоречит canonical contract;
- не течёт legacy assumptions в будущий HTTP слой;
- опирается на уже описанные status rules;
- может служить устойчивым backend source перед HTTP normalization.

---

## 3. Scope

### Входит

- re-check `app/services/driver_status_service.py`
- re-check `app/services/driver_permissions_service.py`
- re-check `app/services/driver_notifications_service.py`
- re-check `app/services/driver_operation_service.py`
- фиксация найденных расхождений между service logic и prepared status decisions

### Не входит

- сам HTTP wiring
- frontend changes
- большой schema refactor
- migration historical rows

---

## 4. Service-by-service checklist

## 4.1. `app/services/driver_status_service.py`

Проверить:

- [ ] transition maps всё ещё согласованы с canonical contract
- [ ] eligibility computation не использует уже опровергнутые assumptions
- [ ] profile/documents/trip-sheet/shift/order transitions не конфликтуют с inventory and cleanup plans
- [ ] trip-sheet logic готова принять waybill → trip-sheet adapter source
- [ ] service не предполагает несуществующих persisted statuses как факт

Ключевой вопрос:

- можно ли использовать этот service как truth layer после того, как waybill adapter будет зафиксирован?

---

## 4.2. `app/services/driver_permissions_service.py`

Проверить:

- [ ] `can_go_online()` согласован с updated readiness expectations
- [ ] `can_accept_order()` не предполагает двусмысленный order state path
- [ ] blocked/not-eligible logic не течёт через legacy status assumptions
- [ ] service не зависит от `assigned` как внешнего canonical order status
- [ ] ownership checks по-прежнему согласованы с expected runtime semantics

Ключевой вопрос:

- не зашит ли в permission decisions какой-то status assumption, который потом сломает HTTP/API contract?

---

## 4.3. `app/services/driver_notifications_service.py`

Проверить:

- [ ] notification planning строится от canonical events/status meanings
- [ ] service не зависит от legacy `completed`
- [ ] order-related notifications останутся корректны после `done` alignment
- [ ] service не требует знания `assigned` как canonical external status
- [ ] dedupe/event planning не конфликтует с ожидаемыми canonical payloads later

Ключевой вопрос:

- может ли notification layer уже безопасно жить поверх cleaned canonical order/shift/trip-sheet semantics?

---

## 4.4. `app/services/driver_operation_service.py`

Проверить:

- [ ] `completed -> done` patch path описан и/или применён
- [ ] runtime `status` values не расходятся с canonical `order_status` там, где это уже ожидается
- [ ] `assigned` не течёт в places, где later HTTP should expose only canonical order state
- [ ] operation responses already look compatible with future HTTP normalization
- [ ] service does not create new legacy drift while other cleanup steps are underway

Ключевой вопрос:

- можно ли после service re-check считать operation layer достаточно стабильным для HTTP adapters and wiring?

---

## 5. Re-check output format

По итогам этого шага нужен короткий backend verdict в формате:

### Service status summary

- `driver_status_service.py`: OK / needs adjustment
- `driver_permissions_service.py`: OK / needs adjustment
- `driver_notifications_service.py`: OK / needs adjustment
- `driver_operation_service.py`: OK / needs adjustment

### Adjustment list

Для каждого файла:

1. что именно ещё противоречит pre-HTTP readiness
2. нужен ли кодовый patch или достаточно semantic note
3. блокирует ли это HTTP прямо сейчас

---

## 6. GO / NO-GO rule after this re-check

### GO to HTTP if

- все четыре service areas либо `OK`, либо имеют только неблокирующие замечания
- no service leaks unresolved legacy status semantics into future HTTP contract
- operation layer responses already align with expected canonical fields closely enough

### NO-GO to HTTP if

- хотя бы один service layer still depends on unresolved `assigned` semantics critically
- `driver_operation_service.py` продолжает плодить очевидный status drift
- trip-sheet source remains too ambiguous for `driver_status_service.py`
- permissions logic depends on unstable order/trip-sheet assumptions

---

## 7. Acceptance criteria

- [ ] все четыре ключевых backend services перепроверены
- [ ] по каждому сервису есть status summary: OK / needs adjustment
- [ ] найденные блокеры перечислены явно
- [ ] после этого можно честно принять решение: пора в HTTP или ещё один backend step нужен до него

---

## 8. Follow-up

Если после этого шага services mostly OK:

1. apply HTTP wiring
2. activate API contract tests
3. inspect failures as contract issues, not as hidden backend semantics fog
4. only then move to frontend gating

Если после этого шага services not ready:

1. закрыть точечные backend adjustments
2. потом вернуться к HTTP

Это и есть последний технический контрольный шлюз перед HTTP layer.
