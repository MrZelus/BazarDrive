# GitHub Milestones for BazarDrive

## Purpose

Этот документ фиксирует рекомендуемую структуру **GitHub Milestones** для проекта **BazarDrive** на базе roadmap в `docs/roadmap.md`.

Цель документа:
- разложить roadmap по milestone-волнам;
- упростить назначение issues в GitHub;
- сделать прогресс по проекту видимым не только по отдельным задачам, но и по продуктовым этапам.

---

## Recommended milestone set

Предлагаемая структура milestone-ов:

1. **Wave A — Compliance Core & Release Readiness**
2. **Wave B — Driver Readiness UX**
3. **Wave C — Compliance Automation & Moderation**
4. **Wave D — Feed, Trust & Role UX Hardening**

Если понадобится более компактная модель, можно использовать сокращённые названия:
- `A: Compliance Core`
- `B: Driver Readiness`
- `C: Compliance Automation`
- `D: Feed & Trust Hardening`

---

## Milestone 1 — Wave A: Compliance Core & Release Readiness

### Goal

Собрать базовый технический каркас driver compliance и одновременно удержать проект в хорошем release-ready состоянии.

### Why this milestone comes first

Без этого слоя нельзя безопасно:
- интегрировать driver eligibility в order flow;
- строить readiness UX;
- автоматизировать compliance reminders;
- делать админскую проверку документов.

### Include issues

- #266 — Epic: Driver legal profile, documents, and taxi compliance
- #278 — Tech: Alembic migrations for driver compliance module
- #279 — Tech: SQLAlchemy models for driver compliance module
- #280 — Tech: Repository layer for driver compliance
- #281 — Tech: DriverComplianceService implementation
- #282 — Tech: API endpoints for driver compliance
- #283 — Tech: Integrate compliance guard into order flow
- #285 — Tech: Tests for driver compliance module
- #175 — Epic: Quality, Contracts & Release Readiness
- #204 — Post-172: verification/trust integration hardening

### Exit criteria

- миграции применяются стабильно;
- compliance entities существуют в БД и доступны через repository;
- service определяет eligibility state;
- API возвращает структурированные причины blocked-state;
- guard подключён хотя бы к ключевым server-side entry points;
- regression pack и release checklist не противоречат текущей реализации.

### Suggested milestone description

> Build the technical core for driver compliance, eligibility checks, and release-ready contracts/tests. This milestone establishes the backend and guardrails required for real taxi order access control.

---

## Milestone 2 — Wave B: Driver Readiness UX

### Goal

Превратить driver profile в полноценный рабочий cockpit, где видно, можно ли выходить на линию, чего не хватает и что нужно сделать дальше.

### Include issues

- #267 — Driver profile: legal identity and qualification fields
- #268 — Driver profile: entrepreneur and legal status section
- #269 — Driver vehicle profile: vehicle data and taxi equipment
- #270 — Driver documents: upload, review, expiry tracking, and verification statuses
- #272 — Waybill flow: open before shift, close after shift
- #273 — Driver profile summary: readiness, document health, and warnings

### Exit criteria

- водитель может заполнить ключевые legal/compliance поля;
- карточка автомобиля поддерживает обязательные taxi attributes;
- документы отображаются с корректными статусами;
- путевой лист участвует в readiness state;
- summary card показывает причину ограничений и CTA на следующий шаг.

### Suggested milestone description

> Deliver the driver-facing readiness experience: legal profile, vehicle, documents, waybill, and summary UX needed for operational taxi eligibility.

---

## Milestone 3 — Wave C: Compliance Automation & Moderation

### Goal

Сделать compliance не ручной и не хрупкой, а автоматически поддерживаемой системой с reminders, expiry logic, moderation and audit behavior.

### Include issues

- #274 — Order journal: store taxi order registration fields for compliance
- #275 — Driver document reminders: expiry warnings and action prompts
- #276 — Admin moderation: review driver documents and compliance decisions
- #284 — Tech: Document expiry background job

### Exit criteria

- у документов есть автоматическая expiry/expiring_soon логика;
- reminders не спамят пользователя дублями;
- модератор может approve/reject документы и оставлять reason;
- order journal фиксирует необходимые compliance snapshots;
- состояние compliance становится пригодным для аудита и дальнейшего экспорта.

### Suggested milestone description

> Automate document lifecycle, reminders, and moderation flows so compliance stays current without relying on manual upkeep.

---

## Milestone 4 — Wave D: Feed, Trust & Role UX Hardening

### Goal

Довести publication/feed часть BazarDrive до консистентного продуктового состояния: роли, trust layer, moderation rules, feed interactions.

### Include issues

- #171 — Epic: Publication Profile & Role UX
- #172 — Epic: Documents & Trust Layer
- #173 — Epic: Feed Engagement & Interaction
- #174 — Epic: Moderation, Safety & Authorization
- #177 — Role matrix enforcement for profile tabs
- #110 — Feed: DELETE /api/feed/posts/{id} + проверка прав
- #182 — Добавить поддержку загрузки фото в гостевой ленте
- #184 — Добавить поддержку загрузки фото в гостевой ленте

### Exit criteria

- role matrix стабильно enforced в UI;
- documents/trust state не расходится с role logic;
- object-level authorization работает предсказуемо;
- delete/edit ownership cases покрыты;
- feed interactions устойчивы к reload и ошибкам;
- docs/tests/OpenAPI не отстают от поведения продукта.

### Suggested milestone description

> Harden the publication/feed platform: role-based profile UX, trust/document consistency, moderation rules, ownership checks, and stable interaction flows.

---

## Mapping summary

| Milestone | Main focus | Issues |
| --- | --- | --- |
| Wave A — Compliance Core & Release Readiness | backend core, eligibility, tests, contracts | #175, #204, #266, #278, #279, #280, #281, #282, #283, #285 |
| Wave B — Driver Readiness UX | profile, legal data, vehicle, docs, waybill, summary | #267, #268, #269, #270, #272, #273 |
| Wave C — Compliance Automation & Moderation | reminders, expiry, moderation, order journal | #274, #275, #276, #284 |
| Wave D — Feed, Trust & Role UX Hardening | feed UX, role matrix, trust, moderation/auth | #110, #171, #172, #173, #174, #177, #182, #184 |

---

## Optional labels to use together with milestones

Чтобы milestone-ы работали чище, можно дополнительно ввести набор label-ов:

### Domain labels
- `domain:driver`
- `domain:compliance`
- `domain:feed`
- `domain:moderation`
- `domain:quality`

### Layer labels
- `layer:db`
- `layer:api`
- `layer:service`
- `layer:web`
- `layer:bot`
- `layer:docs`
- `layer:test`

### Priority labels
- `priority:p0`
- `priority:p1`
- `priority:p2`
- `priority:p3`

### Type labels
- `type:epic`
- `type:feature`
- `type:tech`
- `type:bug`
- `type:hardening`

---

## Suggested GitHub usage rules

### Rule 1
Каждый issue должен иметь:
- один milestone;
- минимум один domain label;
- при необходимости layer label.

### Rule 2
Epic issues можно назначать в milestone вместе с их implementation issues, если milestone используется как high-level progress bucket.

### Rule 3
Если issue выходит за рамки ближайших волн, его можно оставить без milestone и пометить только label-ом `priority:p3` до уточнения roadmap.

### Rule 4
Если issue одинаково относится к двум milestones, выбирать milestone по **основному выходу задачи**, а не по побочным эффектам.

Пример:
- задача про driver documents UI с влиянием на eligibility всё равно идёт в **Wave B**, если её основной результат — UX/readiness;
- задача про service-layer eligibility logic идёт в **Wave A**, даже если UI потом будет использовать этот результат.

---

## Recommended rollout order in GitHub

### Step 1
Создать milestone-ы:
- Wave A — Compliance Core & Release Readiness
- Wave B — Driver Readiness UX
- Wave C — Compliance Automation & Moderation
- Wave D — Feed, Trust & Role UX Hardening

### Step 2
Распределить уже существующие issues по таблице выше.

### Step 3
Для новых задач использовать правило:
- сначала milestone;
- потом labels;
- потом детализация acceptance criteria.

### Step 4
По завершении каждой волны обновлять:
- `docs/roadmap.md`
- этот документ;
- при необходимости epic descriptions.

---

## Short version

- **Wave A**: backend compliance core + guard + tests + contracts
- **Wave B**: driver profile / docs / vehicle / waybill / readiness UX
- **Wave C**: reminders / expiry / moderation / order journal
- **Wave D**: feed interactions / role UX / trust / moderation hardening

---

## Note

В GitHub milestones нет смысла перегружать десятками мелких фаз. Четыре волны выше достаточно хорошо разделяют проект на большие смысловые блоки и не превращают roadmap в лабиринт с табличками на каждом углу.
