# Driver `completed -> done` Rollout Plan

Этот документ фиксирует **первый быстрый implementation-step** в работе по persisted status alignment для driver domain:

**убрать расхождение между legacy runtime/journal status `completed` и canonical order status `done`.**

---

## 1. Почему именно это первым

Среди найденных расхождений это самый дешёвый и понятный узел:

- semantic meaning почти совпадает один к одному;
- canonical contract уже использует `done`;
- operation/API слой уже возвращает canonical `order_status = done`;
- runtime/journal слой всё ещё пишет `completed`.

Это хороший первый cleanup-кандидат перед более спорными кейсами вроде `assigned`.

---

## 2. Current state

На текущем шаге подтверждено следующее:

### Canonical layer

Canonical order contract использует:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### Runtime layer

`app/services/driver_operation_service.py` использует внутренний набор journal/runtime statuses, где есть:

- `assigned`
- `accepted`
- `completed`
- `canceled`

### Mismatch

- canonical success payload for complete-order already returns `order_status = done`
- but repository journal payload still uses `order_status = completed`

Это означает, что:

- API contract уже canonical;
- persisted order history пока нет.

---

## 3. Goal

Сделать так, чтобы завершённый заказ в driver backend flow был согласован на всех слоях:

- runtime service semantics;
- repository write path;
- persisted `order_journal_records.order_status`;
- canonical API payload.

Целевое состояние:

- новые записи пишутся как `done`;
- backend reads корректно интерпретируют historical `completed` rows, если они есть;
- frontend/API не видят legacy distinction.

---

## 4. Recommended strategy

### 4.1. New writes -> canonical immediately

Все новые write paths для завершённого заказа должны писать:

- `done`

вместо:

- `completed`

### 4.2. Historical rows -> temporary compatibility read

Если в БД уже есть historical rows со `completed`, допустим временный compatibility rule:

- `completed` on read -> treat as canonical `done`

### 4.3. Optional data cleanup later

После стабилизации backend можно отдельно решить:

- нужен ли one-time SQL update historical rows `completed -> done`

Это желательно, но не обязательно для первого безопасного шага.

---

## 5. Candidate code paths to update

### 5.1. `app/services/driver_operation_service.py`

Проверить и изменить:

- internal supported runtime statuses set;
- `_record_order_status_transition(...)` usage for complete flow;
- `complete_order(...)` write path.

Ожидаемое изменение:

- убрать запись `status="completed"` в journal write path;
- использовать canonical completion status for persistence.

### 5.2. `app/db/repository.py`

Проверить:

- есть ли чтение/фильтрация по `order_status = completed`;
- есть ли отчёты/списки/агрегации, которые ожидают legacy value;
- нужен ли temporary read-normalization для historical rows.

### 5.3. Tests

Добавить или обновить tests так, чтобы проверялось:

- complete-order produces canonical `done` semantics everywhere expected;
- historical `completed` rows do not break reads if compatibility mode remains.

---

## 6. Exact rollout steps

### Step 1. Update runtime write path

- [ ] найти место, где complete-order пишет `completed` в journal payload;
- [ ] заменить его на `done` или canonical enum-based value;
- [ ] убедиться, что success payload остаётся `order_status = done`.

### Step 2. Re-check repository consumers

- [ ] найти repository readers / filters, зависящие от `completed`;
- [ ] если таких мест нет, cleanup проще;
- [ ] если есть, добавить temporary compatibility mapping on read.

### Step 3. Add or update tests

Минимальные проверки:

- [ ] completion write path stores canonical completion status;
- [ ] HTTP/API layer still returns `order_status = done`;
- [ ] legacy `completed` row, если встречается, не ломает downstream interpretation.

### Step 4. Optional historical cleanup

Отдельно решить:

- [ ] нужен ли SQL migration/update old rows from `completed` to `done`;
- [ ] если да, сделать это отдельным узким change-set, а не смешивать с HTTP wiring.

---

## 7. Suggested implementation rule

Для order completion использовать одно правило:

### Persisted and canonical target

- persisted current meaning: `done`
- canonical API meaning: `done`
- compatibility read alias: `completed -> done` (temporary only)

Это убирает разрыв между runtime truth и API contract без большого рефактора.

---

## 8. Acceptance criteria

- [ ] новые completion writes больше не используют `completed`;
- [ ] canonical completion status для order flow = `done` на backend/API слоях;
- [ ] repository readers проверены на зависимость от `completed`;
- [ ] при необходимости добавлен temporary compatibility read mapping;
- [ ] change isolated and ready before broader status alignment work continues.

---

## 9. Follow-up after this quick win

После `completed -> done` логичный следующий status-alignment step:

1. решить семантику `assigned`
2. зафиксировать waybill -> trip-sheet adapter
3. определить поведение `requires_closing`
4. потом перейти к HTTP wiring
5. затем активировать API contract tests

Это хороший первый cleanup-ход, потому что он даёт быстрый выигрыш с низкой смысловой неопределённостью.
