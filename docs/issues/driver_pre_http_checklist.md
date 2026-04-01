# Driver Checklist Before Transition to HTTP

Этот документ фиксирует **чек-лист готовности перед переходом к HTTP wiring** для driver domain в BazarDrive.

Цель чек-листа — не пустить проект в HTTP layer раньше, чем backend truth-base станет достаточно устойчивой.

---

## 1. Status contract readiness

- [ ] canonical driver statuses уже зафиксированы и не требуют срочной переработки
- [ ] `completed -> done` как минимум описан и понятен как rollout-step
- [ ] read-side риск по legacy `completed` просмотрен
- [ ] `assigned` вынесен в отдельный semantic audit и не считается молча canonical status
- [ ] порядок `created -> accepted -> arriving -> ontrip -> done -> canceled` остаётся целевым canonical ladder

---

## 2. Persisted/runtime alignment

- [ ] есть инвентаризация `DB/runtime value -> canonical value`
- [ ] major mismatches перечислены явно
- [ ] для каждого mismatch понятно, это cleanup или centralized mapping
- [ ] waybill persistence в `driver_documents` распознана как смешанный persisted слой
- [ ] нет неучтённых legacy values, которые могут внезапно утечь в HTTP payload

---

## 3. Waybill / trip-sheet readiness

- [ ] есть явный план adapter-layer между waybill persistence и `TripSheetStatus`
- [ ] правила для `missing` описаны
- [ ] правила для `open` описаны
- [ ] правила для `closed` описаны
- [ ] по `requires_closing` есть хотя бы audit path и provisional rule
- [ ] trip-sheet semantics не размазаны между UI и backend

---

## 4. Backend services re-check

Перед HTTP layer нужно ещё раз сверить backend services с зафиксированными статусными решениями.

- [ ] `app/services/driver_status_service.py` не противоречит принятым статусным rules
- [ ] `app/services/driver_permissions_service.py` не завязан на неразрешённые legacy assumptions
- [ ] `app/services/driver_notifications_service.py` использует canonical event/status logic
- [ ] `app/services/driver_operation_service.py` не возвращает наружу двусмысленные status values там, где уже ожидается canonical meaning
- [ ] backend still has one clear truth path from repository facts to service-level interpretation

---

## 5. Read/write discipline

- [ ] write paths не создают новые строки с уже признанными legacy values без явного переходного смысла
- [ ] read paths не зависят молча от старых string literals
- [ ] если compatibility mapping нужен, он централизован в одном backend place
- [ ] frontend не должен знать про compatibility mapping

---

## 6. HTTP contract prerequisites

Переход к HTTP разумен только если backend уже знает, что именно он хочет говорить наружу.

- [ ] понятно, какие canonical поля должны вернуться из driver HTTP endpoints
- [ ] `error.code` считается обязательной частью driver error contract
- [ ] `event_name` уже стабилен для ключевых actions
- [ ] `shift_status` стабилен для go-online / shift flows
- [ ] `order_status` стабилен для order flows
- [ ] `trip_sheet_status` имеет понятный backend source

---

## 7. Narrow scope discipline

Перед переходом к HTTP нужно удержать узкий scope.

- [ ] не запланирован параллельный frontend refactor
- [ ] не делается большой schema split в той же волне
- [ ] не смешиваются status cleanup, UI logic и HTTP wiring в один giant step
- [ ] переход к HTTP остаётся mechanical integration step, а не новым исследованием

---

## 8. Tests readiness

- [ ] backend contract docs уже имеют test-driven follow-up path
- [ ] API contract scaffold tests уже подготовлены или описаны
- [ ] понятно, какие tests должны активироваться после wiring
- [ ] HTTP tests не начнут валиться только потому, что backend semantics ещё не определены

---

## 9. Minimal go/no-go rule

### GO to HTTP if

- status semantics достаточно очищены
- major mismatches уже разложены
- waybill/trip-sheet mapping понятен
- backend services переосмыслены под canonical rules
- есть ясность, какие canonical fields HTTP должен отдавать

### NO-GO to HTTP if

- `assigned` всё ещё плавает между status/event без решения
- `completed/done` конфликт не разобран даже как rollout
- `trip_sheet_status` не имеет устойчивого backend source
- legacy persisted values всё ещё могут утекать наружу бесконтрольно

---

## 10. Expected next step after this checklist

Если чек-лист в основном закрыт, следующий шаг:

1. re-check backend services against resolved status rules
2. apply HTTP wiring from the prepared wiring plan
3. activate API contract tests
4. only then move toward frontend gating

---

## 11. Acceptance criteria

- [ ] есть repo-backed checklist перед переходом к HTTP
- [ ] checklist покрывает status semantics, persistence alignment, waybill mapping, backend services, and test readiness
- [ ] по нему можно принять честное решение: уже идём в HTTP или ещё рано
