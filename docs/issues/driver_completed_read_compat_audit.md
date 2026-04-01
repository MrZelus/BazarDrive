# Driver `completed` Read Compatibility Audit

Этот документ фиксирует следующий узкий шаг после mechanical patch `completed -> done`:

**проверить, где repository/read layer, отчёты и API consumers ещё могут зависеть от legacy value `completed`.**

---

## 1. Почему это следующий шаг

После перевода новых write paths на canonical `done` остаётся риск тихих расхождений в read paths:

- фильтры по `order_status = completed`
- отчёты и списки, ожидающие legacy значение
- downstream code, который интерпретирует journal rows буквально

Именно это место обычно прячет "дым без огня": write path уже новый, а старые readers всё ещё смотрят в старое зеркало.

---

## 2. Цель

Проверить, сломается ли что-то после переключения новых completion writes на `done`, и определить, нужен ли временный compatibility read mapping:

- `completed` on read -> treat as `done`

---

## 3. Scope

### Входит

- audit repository readers по `order_status`
- audit report/list/filter paths
- audit API payload builders, если они читают journal rows
- решение, нужен ли temporary compatibility mapping

### Не входит

- migration historical rows
- cleanup `assigned`
- HTTP wiring
- frontend gating

---

## 4. Primary audit targets

### 4.1. `app/db/repository.py`

Найти и проверить все read paths, связанные с `order_journal_records.order_status`.

Минимально проверить:

- [ ] `list_order_journal_records(...)`
- [ ] любые фильтры `status=...`
- [ ] любые агрегаты/группировки по `order_status`
- [ ] любые downstream consumers, завязанные на конкретные string values

### 4.2. Driver services / API readers

Проверить, есть ли код, который:

- [ ] читает journal rows и ожидает `completed`
- [ ] строит API response из raw `order_status`
- [ ] строит analytics/report summaries из legacy статуса

---

## 5. Audit questions

Для каждого read path ответить:

- [ ] читает ли он `completed` явно;
- [ ] сравнивает ли он `order_status` со string literal;
- [ ] нужен ли ему canonical `done`;
- [ ] будет ли он корректен, если новые rows пойдут как `done`, а старые останутся `completed`.

---

## 6. Decision rule

### If no reader depends on `completed`

Тогда:

- cleanup проще,
- compatibility layer можно не добавлять сразу.

### If some readers depend on `completed`

Тогда:

- добавить temporary centralized read normalization
- интерпретировать `completed` как canonical `done`
- не размазывать это по нескольким слоям.

---

## 7. Suggested compatibility rule

Если mapping понадобится, то в одном backend place:

- `completed` -> `done`

Важно:

- mapping только на read side
- mapping не должен течь во frontend как отдельное знание
- новые writes уже должны использовать `done`

---

## 8. Acceptance criteria

- [ ] все ключевые read paths по `order_journal_records` просмотрены
- [ ] найдено, есть ли зависимость от literal `completed`
- [ ] принято решение: нужен compatibility mapping или нет
- [ ] если нужен, он описан как centralized backend read rule
- [ ] это завершено до следующего шага по `assigned` и HTTP wiring

---

## 9. Follow-up

После завершения этого аудита:

1. либо ввести temporary `completed -> done` read normalization
2. либо зафиксировать, что readers уже совместимы
3. затем перейти к `assigned` read/write audit
4. потом к waybill/trip-sheet adapter
5. затем к HTTP wiring
