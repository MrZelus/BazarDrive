# Driver Waybill → Trip Sheet Adapter Plan

Этот документ фиксирует следующий узкий backend step после status-alignment work around `completed` and `assigned`:

**ввести явный adapter layer между persisted waybill data в `driver_documents` и canonical `TripSheetStatus` contract.**

---

## 1. Почему это следующий шаг

Сейчас в driver domain уже видно смешение двух разных смыслов в одном persisted слое:

- ordinary document review lifecycle
- waybill / trip-sheet lifecycle

Практически это выглядит так:

- waybill хранится в `driver_documents`
- `type = 'waybill'`
- активный waybill ищется через `status = 'open'`
- закрытие пишет `status = 'closed'`

В то же время canonical contract ожидает отдельный trip-sheet ladder:

- `missing`
- `open`
- `requires_closing`
- `closed`

Пока этого adapter layer нет, backend, API и будущий frontend рискуют по-разному интерпретировать одни и те же persisted данные.

---

## 2. Цель

Сделать так, чтобы backend имел **одну явную и централизованную интерпретацию** waybill persistence в терминах canonical trip-sheet contract.

Итогом должно быть:

- backend знает, как из `driver_documents(type='waybill', status=...)` получить canonical `TripSheetStatus`
- ordinary document logic не путается с trip-sheet logic
- HTTP/API later can return stable `trip_sheet_status`
- frontend/UI не нужно знать внутреннюю смешанную persisted модель

---

## 3. Scope

### Входит

- mapping from waybill persistence to `TripSheetStatus`
- rule for deriving `missing`
- rule for deriving `open`
- rule for deriving `closed`
- investigation and provisional rule for `requires_closing`
- centralized adapter placement in backend layer

### Не входит

- полный schema split `driver_documents` vs separate trip_sheets table
- frontend UI changes
- HTTP wiring in this PR
- migration historical rows

---

## 4. Current persisted reality

Текущая backend persistence already suggests:

- waybill is stored in `driver_documents`
- waybill rows are identified by `type = 'waybill'`
- active waybill lookup uses `status = 'open'`
- closing flow writes `status = 'closed'`

Это означает, что persisted source уже существует, но canonical interpretation пока не оформлена как отдельный adapter contract.

---

## 5. Canonical target

Adapter должен приводить persisted reality к canonical trip-sheet statuses:

- `missing`
- `open`
- `requires_closing`
- `closed`

---

## 6. Recommended initial mapping

### 6.1. `missing`

Рекомендация:

- если у профиля нет актуальной waybill row, usable for current shift/workday semantics,
  возвращать `TripSheetStatus.MISSING`

### 6.2. `open`

Рекомендация:

- `driver_documents(type='waybill', status='open')`
  → `TripSheetStatus.OPEN`

### 6.3. `closed`

Рекомендация:

- `driver_documents(type='waybill', status='closed')`
  → `TripSheetStatus.CLOSED`

### 6.4. `requires_closing`

Это пока самый неясный элемент.

Промежуточная рекомендация:

- считать `requires_closing` derived state,
- а не требовать немедленного нового persisted значения,
- пока не доказано, что без отдельного persisted field backend rule будет ненадёжной.

---

## 7. Key audit questions for `requires_closing`

Нужно ответить на вопросы:

- [ ] есть ли уже shift-end signal, после которого open waybill должен считаться close-required?
- [ ] есть ли обязательные closure fields, отсутствие которых отделяет `open` от `requires_closing`?
- [ ] должен ли `requires_closing` зависеть от shift state?
- [ ] должен ли `requires_closing` зависеть от наличия завершённой работы за день?
- [ ] есть ли уже в repository layer признаки close-required condition без нового status field?

---

## 8. Recommended adapter placement

Adapter не должен жить во frontend.

Adapter не должен расползаться по случайным helper-функциям.

### Preferred backend placement

Один из вариантов:

- dedicated backend helper/service next to driver status layer
- or a small adapter function used by repository/service boundary

Главное правило:

**one place only**

чтобы mapping оставался:

- явно тестируемым
- переиспользуемым
- безопасным для HTTP layer later

---

## 9. Suggested output shape

Когда adapter будет реализован, backend сможет оперировать примерно такой логикой:

- persisted waybill facts in
- canonical `trip_sheet_status` out
- optional helper flags out, for example:
  - `trip_sheet_ok`
  - `trip_sheet_requires_action`
  - `trip_sheet_missing_reason`

Но на этом шаге достаточно сначала зафиксировать сам mapping contract.

---

## 10. Testing expectations

После введения adapter layer нужны tests как минимум на:

- [ ] no waybill row -> `missing`
- [ ] waybill with `status='open'` -> `open`
- [ ] waybill with `status='closed'` -> `closed`
- [ ] derived close-required condition -> `requires_closing` according to chosen rule
- [ ] ordinary non-waybill documents never affect trip-sheet mapping directly unless explicitly part of readiness rule

---

## 11. Decision rule

### Preferred near-term approach

- keep existing persistence in `driver_documents`
- add centralized backend adapter
- derive `requires_closing` if possible
- defer schema split unless backend evidence shows adapter is not enough

### Avoid for now

- large table redesign
- pushing mixed persistence semantics into API or UI
- duplicating mapping in multiple layers

---

## 12. Acceptance criteria

- [ ] current persisted waybill shape is explicitly mapped to canonical `TripSheetStatus`
- [ ] `missing/open/closed` rules are described clearly
- [ ] `requires_closing` has an audit path and provisional rule
- [ ] adapter placement is defined as one backend place
- [ ] this prepares a stable `trip_sheet_status` source for later HTTP wiring

---

## 13. Follow-up

После этого adapter step логичная лестница такая:

1. finalize `assigned` semantics
2. finalize waybill → trip-sheet adapter
3. re-check driver status / permissions services against resolved status rules
4. apply HTTP wiring
5. activate API contract tests
6. move to frontend gating

Это keeps the backend rails clean before UI starts depending on canonical trip-sheet state.
