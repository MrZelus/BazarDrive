# Driver Backend Services Re-check Plan

Этот документ фиксирует **главный blocker-step перед переходом к HTTP wiring** для driver domain:

**повторно сверить backend services с уже зафиксированными статусными решениями, cleanup/mapping планами и pre-HTTP checklist.**

---

## 1. Почему это сейчас главный blocker

По pre-HTTP checklist уже видно, что главный NO-GO блок перед HTTP сейчас не в документах и не в UI, а в том, что backend services ещё не были повторно проверены against resolved status rules.

То есть у проекта уже есть:

- canonical docs contracts
- persisted/runtime mapping inventory
- cleanup/mapping plans
- `completed -> done` rollout step
- `assigned` semantic audit path
- waybill → trip-sheet adapter plan
- pre-HTTP checklist with current NO-GO snapshot

Но до тех пор, пока service layer не будет повторно сверена с этим набором решений, HTTP wiring рискует стать слоем, который поверх старой правды приклеивает новые payloads.

---

## 2. Цель

Проверить, что ключевые backend services:

- не противоречат canonical status logic;
- не живут на неучтённых legacy assumptions;
- могут безопасно стать source for HTTP payload normalization;
- готовы к следующему шагу: mechanical HTTP wiring + API contract activation.

---

## 3. Scope

### Входит

- re-check `app/services/driver_status_service.py`
- re-check `app/services/driver_permissions_service.py`
- re-check `app/services/driver_notifications_service.py`
- re-check `app/services/driver_operation_service.py`
- cross-check service assumptions against:
  - canonical enums
  - persisted/runtime mapping docs
  - `completed -> done` plan
  - `assigned` audit path
  - waybill/trip-sheet adapter plan

### Не входит

- direct HTTP wiring in this PR
- frontend changes
- large schema redesign
- mass migration work

---

## 4. Services to re-check

## 4.1. `app/services/driver_status_service.py`

### What to verify

- [ ] transition maps всё ещё совпадают с canonical docs
- [ ] service не зависит от несуществующих persisted meanings
- [ ] `compute_eligibility()` опирается на понятные backend facts
- [ ] `profile_not_approved`, `required_documents_missing_or_invalid`, `trip_sheet_not_ready` and blockers still make sense under the latest status decisions
- [ ] trip-sheet assumptions не противоречат waybill adapter direction

### Main question

Может ли `driver_status_service` быть устойчивым canonical interpreter после waybill/trip-sheet adapter, или там уже сейчас есть скрытые противоречия?

---

## 4.2. `app/services/driver_permissions_service.py`

### What to verify

- [ ] permission checks не завязаны на старые status names
- [ ] `can_go_online()` не конфликтует с planned trip-sheet adapter meaning
- [ ] `can_accept_order()` не делает допущений по order state, которые ломаются после `assigned` decision
- [ ] blocked / not-eligible paths уже смотрят на canonical meaning, а не на legacy strings
- [ ] ownership assumptions остаются валидными

### Main question

После cleanup/mapping decisions permissions layer всё ещё даёт ту же бизнес-правду, или ей нужно подправить входные assumptions?

---

## 4.3. `app/services/driver_notifications_service.py`

### What to verify

- [ ] events still map to the right priority/channel semantics
- [ ] event routing не зависит от ambiguous legacy states
- [ ] dedupe logic survives updated status semantics cleanly
- [ ] notification planning can remain canonical even if persistence still contains compatibility values

### Main question

Notifications layer already reads like canonical orchestration. Нужно подтвердить, что она действительно не течёт от unresolved persistence ambiguity.

---

## 4.4. `app/services/driver_operation_service.py`

### What to verify

- [ ] где ещё остались legacy runtime statuses
- [ ] what will change once `completed -> done` is truly applied
- [ ] does `assign_order()` still leak `assigned` into outward semantics
- [ ] do operation responses already align with canonical `event_name`, `order_status`, `shift_status`
- [ ] can this service safely feed HTTP adapters after the re-check

### Main question

Это ближайший runtime bridge между repository truth и HTTP layer. Он должен быть понятен и clean enough before wiring.

---

## 5. Cross-check matrix

Для каждого service file ответить на один и тот же минимальный набор вопросов.

### 5.1. Status naming

- [ ] использует только canonical names там, где уже должен
- [ ] явно изолирует legacy values там, где cleanup ещё не завершён
- [ ] не смешивает event meanings со status meanings

### 5.2. Input assumptions

- [ ] assumptions about repository facts still valid
- [ ] no hidden dependency on unverified DB shape
- [ ] waybill/trip-sheet ambiguity acknowledged where needed

### 5.3. Output contract readiness

- [ ] outputs are good enough for future HTTP normalization
- [ ] canonical fields already present or straightforward to derive
- [ ] no ambiguous values leak outward where API expects canonical data

---

## 6. Expected outcome

По итогам re-check по каждому service file должен быть результат одного из типов:

### A. Ready as-is

Service already consistent with the current status strategy.

### B. Needs small cleanup

Service conceptually correct, but needs one or two narrow updates.

### C. Blocker before HTTP

Service still depends on unresolved status ambiguity and must be fixed before wiring.

---

## 7. Desired output format

Итог re-check удобно зафиксировать так:

### `driver_status_service.py`
- status: Ready / Needs cleanup / Blocker
- issues:
- recommended fix:

### `driver_permissions_service.py`
- status: Ready / Needs cleanup / Blocker
- issues:
- recommended fix:

### `driver_notifications_service.py`
- status: Ready / Needs cleanup / Blocker
- issues:
- recommended fix:

### `driver_operation_service.py`
- status: Ready / Needs cleanup / Blocker
- issues:
- recommended fix:

---

## 8. Acceptance criteria

- [ ] all four key driver services are explicitly re-checked
- [ ] each service gets a readiness verdict
- [ ] blockers are named concretely
- [ ] small cleanups are separated from true blockers
- [ ] this re-check gives a real go/no-go signal before HTTP wiring

---

## 9. Follow-up after this re-check

If service re-check results are mostly Ready / Needs small cleanup:

1. close small cleanup items
2. apply HTTP wiring from the prepared wiring plan
3. activate API contract tests
4. only then move toward frontend gating

If any true Blocker remains:

1. resolve blocker in backend layer first
2. update pre-HTTP checklist
3. only then go to HTTP

---

## 10. Why this matters

HTTP wiring should be a mechanical bridge, not a magic curtain hiding unresolved backend contradictions.

This re-check step makes sure the backend speaks with one voice before HTTP starts amplifying that voice outward.
