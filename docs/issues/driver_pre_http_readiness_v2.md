# Driver Pre-HTTP Readiness Snapshot v2

Этот документ фиксирует **обновлённую сводку готовности перед переходом к HTTP wiring** после серии узких status-alignment и backend-readiness шагов.

Цель snapshot v2:

- убрать старый широкий туман;
- показать, что уже очищено;
- сузить оставшиеся блокеры до короткого списка;
- дать честный текущий verdict: GO или NO-GO к HTTP.

---

## 1. Что уже собрано и зафиксировано

На этом этапе в repo уже есть подготовительные слои для driver domain:

- canonical contract docs
- backend contract layer
- HTTP payload helpers / adapters / wiring plan
- pre-HTTP checklist
- service-layer re-check
- status alignment prep around `completed -> done`
- semantic audit path for `assigned`
- waybill → trip-sheet adapter planning

Иными словами:

архитектурная лестница перед HTTP уже не абстрактная, а repo-backed.

---

## 2. Что уже можно считать cleaned enough

### 2.1. Contract direction

Можно считать очищенным направление по canonical contract:

- order ladder: `created -> accepted -> arriving -> ontrip -> done -> canceled`
- shift ladder remains canonical
- profile/document ladders зафиксированы
- `error.code` / `event_name` / canonical status fields already understood as target HTTP language

### 2.2. Planning discipline

Тоже уже достаточно cleaned:

- frontend не смешивается в ту же волну
- giant schema redesign не мешается в pre-HTTP stage
- HTTP больше не рассматривается как исследование, а как mechanical integration step

### 2.3. Most service layer direction

По service-layer re-check уже видно, что:

- `driver_status_service.py` largely OK
- `driver_permissions_service.py` largely OK
- `driver_notifications_service.py` OK

Это важный сдвиг: pre-HTTP проблема уже не в "всём backend сразу".

---

## 3. What remains as actual blockers

На текущем шаге остались **два реальных backend blockers**.

## Blocker A. `app/services/driver_operation_service.py`

### Почему это blocker

Потому что этот файл всё ещё смешивает:

- legacy runtime/persistence semantics
- canonical outward semantics

Главные оставшиеся проблемы:

- `completed` vs `done`
- outward `status` vs canonical `order_status`
- `assigned` still leaking outward as runtime status while its meaning is not fully stabilized

### Что должно стать true

- новые completion writes не используют `completed`
- outward completion semantics не противоречат canonical `done`
- `assigned` не считается молча canonical external truth

---

## Blocker B. One backend source for `trip_sheet_status`

### Почему это blocker

Потому что canonical HTTP later will want a stable `trip_sheet_status`, while current persisted reality is mixed inside waybill rows in `driver_documents`.

Без одного backend source later layers могут начать по-разному интерпретировать:

- missing waybill
- open waybill
- closed waybill
- close-required state

### Что должно стать true

- есть one backend place only for waybill → `TripSheetStatus`
- `missing/open/closed` rules explicit
- `requires_closing` has backend-side rule, even if provisional

---

## 4. What is no longer a primary blocker

Следующие вещи уже **не выглядят как главные стоп-факторы**:

- общий status contract direction
- общий permissions direction
- notifications contract direction
- общий вопрос “а надо ли вообще идти в HTTP?”

Ответ на последний пункт уже такой:

**да, идти в HTTP надо, но после закрытия двух узких backend blockers, а не раньше.**

---

## 5. Current GO / NO-GO verdict

### Current verdict

**Still NO-GO for HTTP right now.**

Но это уже хороший NO-GO, а не туманный:

- не 10 разрозненных проблем
- не спор про docs vs frontend
- не отсутствие структуры
- а всего два оставшихся backend узла

Именно это означает, что дорожка к HTTP почти очищена.

---

## 6. Minimal bundle to flip to GO

Чтобы перевести snapshot из NO-GO в GO, нужен минимальный practical bundle:

### 6.1. Stabilize `driver_operation_service.py`

- apply `completed -> done`
- stop semantic contradiction between outward `status` and canonical `order_status`
- contain unresolved `assigned`

### 6.2. Stabilize one trip-sheet backend source

- one backend place for waybill → `TripSheetStatus`
- explicit `missing/open/closed`
- backend-side rule for `requires_closing`

### 6.3. Re-check once more

После этих двух шагов ещё раз quickly check:

- service layer no longer leaks unresolved semantics
- HTTP adapters now have stable inputs

---

## 7. Expected transition after blockers are closed

When the two blockers above are closed, the next sequence becomes straightforward:

1. apply HTTP wiring
2. activate API contract tests
3. inspect failures as actual contract issues, not as backend fog
4. only then move toward frontend gating

Именно в этот момент HTTP becomes a clean integration step.

---

## 8. Acceptance criteria for snapshot v2

- [ ] updated pre-HTTP snapshot exists in repo
- [ ] remaining blockers are reduced to a short explicit list
- [ ] non-blocking areas are named so the team stops re-litigating them
- [ ] current verdict is honest: still NO-GO, but narrowly so
- [ ] next move toward GO is mechanically clear

---

## 9. One-line summary

**Before HTTP, the project no longer needs more broad analysis. It needs two narrow backend stabilizations: `driver_operation_service.py` and one canonical backend source for `trip_sheet_status`.**
