# Driver `assigned` Read/Write Audit

Этот документ фиксирует следующий узкий шаг после read-аудита legacy `completed`:

**проверить все write/read paths, где фигурирует `assigned`, и решить, является ли он статусом, событием или переходным legacy-артефактом.**

---

## 1. Почему это следующий шаг

После `completed -> done` и read-side аудита по `completed` самым заметным семантическим узлом остаётся `assigned`.

Это не просто rename-case. Здесь нужно понять сам смысл значения:

- `assigned` как order status
- `assigned` как internal dispatch event
- `assigned` как historical marker
- `assigned` как неудачная замена canonical `created`

Пока это не решено, нельзя безопасно продолжать HTTP wiring и UI gating для order flow.

---

## 2. Цель

Найти и описать:

- где `assigned` пишется;
- где `assigned` читается;
- что именно он означает в каждом месте;
- должен ли он остаться только в истории/событиях или быть вычищен из canonical status path.

---

## 3. Scope

### Входит

- audit write paths по `assigned`
- audit read/filter/report paths по `assigned`
- semantic classification: status vs event
- решение по cleanup или centralized mapping

### Не входит

- прямой code refactor на этом шаге
- HTTP wiring
- frontend changes
- trip-sheet adapter

---

## 4. Primary audit targets

### 4.1. Runtime service layer

Проверить:

- `app/services/driver_operation_service.py`

Найти:

- [ ] где `assigned` пишется в journal/runtime payload
- [ ] возвращается ли `assigned` наружу как `status`
- [ ] отделён ли он от canonical `order_status`

### 4.2. Repository layer

Проверить:

- `app/db/repository.py`

Найти:

- [ ] есть ли filters / reports / readers по `order_status = assigned`
- [ ] живёт ли `assigned` только в `order_journal_records`
- [ ] используется ли `assigned` как current state или только как history marker

### 4.3. Downstream consumers

Проверить:

- [ ] API payload builders
- [ ] analytics/report paths
- [ ] любые summary/list endpoints
- [ ] возможные UI-facing consumers raw journal data

---

## 5. Audit questions

Для каждого найденного path ответить:

- [ ] `assigned` пишется до accept или после него?
- [ ] `assigned` order-global или driver-specific?
- [ ] `assigned` означает ownership или только routing/offer?
- [ ] может ли один заказ быть `assigned` нескольким драйверам?
- [ ] если да, можно ли считать `assigned` canonical order status?

---

## 6. Decision rule

### If `assigned` is really just dispatch/event semantics

Тогда:

- не пускать его в canonical `order_status`
- держать только как internal/history event
- наружу отдавать canonical current status separately

### If `assigned` is just a legacy stand-in for `created`

Тогда:

- cleanup preferred: `assigned -> created`
- historical rows при необходимости маппить на read side

### If `assigned` is truly a stable external domain state

Тогда:

- это уже contract-expansion decision
- сначала нужно менять docs/enums/services/tests
- только потом выпускать его наружу

Этот вариант least preferred, пока нет сильного business-proof.

---

## 7. Output format expected from this audit

Результат должен быть коротким и явным:

1. write paths list
2. read paths list
3. semantic conclusion for `assigned`
4. recommended action:
   - cleanup to `created`
   - internal event only
   - contract expansion

---

## 8. Acceptance criteria

- [ ] все ключевые write paths по `assigned` просмотрены
- [ ] все ключевые read paths по `assigned` просмотрены
- [ ] семантика `assigned` описана явно
- [ ] принято решение: cleanup, internal event only, or contract expansion
- [ ] после этого order-status ladder готова к следующему backend step

---

## 9. Follow-up

После этого аудита:

1. принять решение по `assigned`
2. затем двигаться к waybill/trip-sheet adapter
3. потом к HTTP wiring
4. затем к API contract activation
5. потом к frontend gating

Это сохраняет правильный ритм: сначала убрать семантический туман в persisted/runtime layer, потом уже укреплять API и UI.
