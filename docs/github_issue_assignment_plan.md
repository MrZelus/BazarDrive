# GitHub Issue Assignment Plan for BazarDrive

## Purpose

Этот документ фиксирует **готовый batch-план назначения текущих GitHub issues** по milestone-ам и labels для проекта **BazarDrive**.

Он нужен, чтобы:
- быстро разложить существующий backlog по milestone-волнам;
- не назначать milestone и labels каждый раз заново вручную;
- сделать triage прозрачным и повторяемым.

Связанные документы:
- `docs/roadmap.md`
- `docs/github_milestones.md`
- `docs/github_milestone_descriptions.md`
- `docs/github_labels.md`

---

## Milestone mapping summary

| Milestone | Main focus |
| --- | --- |
| Wave A — Compliance Core & Release Readiness | compliance backend core, eligibility, tests, contracts |
| Wave B — Driver Readiness UX | driver profile, legal data, vehicle, docs, waybill, summary |
| Wave C — Compliance Automation & Moderation | reminders, expiry, moderation, order journal |
| Wave D — Feed, Trust & Role UX Hardening | feed UX, role matrix, trust, moderation/auth |

---

## Assignment table

### Wave A — Compliance Core & Release Readiness

| Issue | Title | Milestone | Recommended labels | Why |
| --- | --- | --- | --- | --- |
| #175 | Epic: Quality, Contracts & Release Readiness | Wave A — Compliance Core & Release Readiness | `type:epic`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:docs` | Это общий quality-контур, поддерживающий текущую волну и снижающий риск регрессий |
| #204 | Post-172: verification/trust integration hardening | Wave A — Compliance Core & Release Readiness | `type:hardening`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:test` | Добивка trust/verification mapping без расширения продуктового scope |
| #266 | Epic: Driver legal profile, documents, and taxi compliance | Wave A — Compliance Core & Release Readiness | `type:epic`, `priority:p0`, `domain:driver`, `domain:compliance` | Главный стратегический epic текущего этапа |
| #278 | Tech: Alembic migrations for driver compliance module | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:compliance`, `layer:db` | Миграционный фундамент compliance-модуля |
| #279 | Tech: SQLAlchemy models for driver compliance module | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:compliance`, `layer:model` | Базовые ORM entities для всей дальнейшей логики |
| #280 | Tech: Repository layer for driver compliance | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:compliance`, `layer:repository` | Data-access слой нужен до API и service orchestration |
| #281 | Tech: DriverComplianceService implementation | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:driver`, `domain:compliance`, `layer:service` | Основная business-логика eligibility и blocked-state |
| #282 | Tech: API endpoints for driver compliance | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:compliance`, `domain:web`, `layer:api` | API-поверхность для driver readiness и UI integration |
| #283 | Tech: Integrate compliance guard into order flow | Wave A — Compliance Core & Release Readiness | `type:tech`, `priority:p0`, `domain:compliance`, `domain:orders`, `layer:service` | Guard должен начать работать как можно раньше на ключевых entry points |
| #285 | Tech: Tests for driver compliance module | Wave A — Compliance Core & Release Readiness | `type:test`, `priority:p0`, `domain:quality`, `domain:compliance`, `layer:test` | Без этого compliance-core будет слишком хрупким |

---

### Wave B — Driver Readiness UX

| Issue | Title | Milestone | Recommended labels | Why |
| --- | --- | --- | --- | --- |
| #267 | Driver profile: legal identity and qualification fields | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web` | Это уже driver-facing readiness UX и legal prerequisites |
| #268 | Driver profile: entrepreneur and legal status section | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web` | Раздел правового статуса нужен для полного readiness-профиля |
| #269 | Driver vehicle profile: vehicle data and taxi equipment | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web` | Автомобиль и taxi equipment участвуют в допуске и UX readiness |
| #270 | Driver documents: upload, review, expiry tracking, and verification statuses | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web` | Основной пользовательский сценарий документов водителя |
| #272 | Waybill flow: open before shift, close after shift | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `domain:orders`, `layer:web` | Путевой лист напрямую влияет на readiness и operational UX |
| #273 | Driver profile summary: readiness, document health, and warnings | Wave B — Driver Readiness UX | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `type:ux`, `layer:web` | Summary card это главный cockpit-слой для понимания статуса допуска |

---

### Wave C — Compliance Automation & Moderation

| Issue | Title | Milestone | Recommended labels | Why |
| --- | --- | --- | --- | --- |
| #274 | Order journal: store taxi order registration fields for compliance | Wave C — Compliance Automation & Moderation | `type:feature`, `priority:p2`, `domain:orders`, `domain:compliance`, `layer:service` | Это support-слой для audit/export/compliance snapshots |
| #275 | Driver document reminders: expiry warnings and action prompts | Wave C — Compliance Automation & Moderation | `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:ops` | Напоминания и предупреждения делают compliance живым, а не статичным |
| #276 | Admin moderation: review driver documents and compliance decisions | Wave C — Compliance Automation & Moderation | `type:feature`, `priority:p1`, `domain:moderation`, `domain:compliance`, `layer:web` | Здесь появляется человеческий review-loop для документов водителя |
| #284 | Tech: Document expiry background job | Wave C — Compliance Automation & Moderation | `type:tech`, `priority:p1`, `domain:compliance`, `layer:ops` | Автоматическое обновление expiry state должно жить в automation-волне |

---

### Wave D — Feed, Trust & Role UX Hardening

| Issue | Title | Milestone | Recommended labels | Why |
| --- | --- | --- | --- | --- |
| #110 | Feed: DELETE /api/feed/posts/{id} + проверка прав | Wave D — Feed, Trust & Role UX Hardening | `type:feature`, `priority:p2`, `domain:feed`, `domain:auth`, `layer:api` | Ownership/delete behavior относится к moderation/auth hardening слоям feed |
| #171 | Epic: Publication Profile & Role UX | Wave D — Feed, Trust & Role UX Hardening | `type:epic`, `priority:p2`, `domain:web`, `domain:feed`, `type:ux` | Role-based publication UX — отдельная продуктовая волна после core compliance |
| #172 | Epic: Documents & Trust Layer | Wave D — Feed, Trust & Role UX Hardening | `type:epic`, `priority:p2`, `domain:feed`, `domain:compliance`, `type:ux` | Trust/document layer должен быть консистентен с feed/profile UX |
| #173 | Epic: Feed Engagement & Interaction | Wave D — Feed, Trust & Role UX Hardening | `type:epic`, `priority:p2`, `domain:feed`, `layer:web` | Реакции и комментарии относятся к growth/hardening feed-части |
| #174 | Epic: Moderation, Safety & Authorization | Wave D — Feed, Trust & Role UX Hardening | `type:epic`, `priority:p2`, `domain:moderation`, `domain:auth`, `type:security` | Это общий safety/auth слой для публикационной платформы |
| #177 | Role matrix enforcement for profile tabs | Wave D — Feed, Trust & Role UX Hardening | `type:feature`, `priority:p2`, `domain:web`, `type:ux`, `layer:web` | Жёсткий role-matrix guard относится к publication profile polish |
| #182 | Добавить поддержку загрузки фото в гостевой ленте | Wave D — Feed, Trust & Role UX Hardening | `type:feature`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web` | Media support важен, но не должен обгонять core compliance и moderation layers |
| #184 | Добавить поддержку загрузки фото в гостевой ленте | Wave D — Feed, Trust & Role UX Hardening | `type:feature`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web` | Дублирующая/перекрывающая media-задача, держать в той же волне до финального triage |

---

## Triage notes

### 1. Issues #182 and #184
Обе задачи относятся к поддержке фото в гостевой ленте и выглядят как сильно пересекающиеся.

Рекомендуемое действие:
- проверить, нужна ли консолидация;
- выбрать одну из задач как primary;
- вторую либо закрыть как duplicate, либо оставить как follow-up hardening issue.

Рекомендуемые labels для secondary issue:
- `status:follow-up`
- или `type:hardening`

---

### 2. Issue #204
Хотя #204 относится к trust/docs слою, его стоит держать в **Wave A** как hardening для уже построенного foundation, чтобы verification-state mapping не расползался при росте compliance и UI.

---

### 3. Issue #175
Это cross-cutting epic. Его можно оставить в **Wave A**, потому что именно в первой волне quality discipline наиболее ценен. Если позже scope станет слишком широким, допускается выделить часть подзадач в будущие milestones, но сам epic полезно держать привязанным к стартовой волне.

---

## Recommended batch order for manual assignment

### Step 1
Назначить milestone **Wave A** всем compliance-core задачам:
- #175
- #204
- #266
- #278
- #279
- #280
- #281
- #282
- #283
- #285

### Step 2
Назначить milestone **Wave B** всем readiness UX задачам:
- #267
- #268
- #269
- #270
- #272
- #273

### Step 3
Назначить milestone **Wave C** automation / moderation задачам:
- #274
- #275
- #276
- #284

### Step 4
Назначить milestone **Wave D** publication/feed hardening задачам:
- #110
- #171
- #172
- #173
- #174
- #177
- #182
- #184

### Step 5
После назначения milestone-ов проставить priority labels, затем domain/type, затем layer labels.

Почему именно так:
- milestone отвечает за волну;
- priority помогает triage внутри волны;
- domain/type помогают понять смысл задачи;
- layer labels нужны уже для точной маршрутизации implementation work.

---

## Compact assignment list

### Wave A
- #175 -> `type:epic`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:docs`
- #204 -> `type:hardening`, `priority:p1`, `domain:quality`, `domain:docs`, `layer:test`
- #266 -> `type:epic`, `priority:p0`, `domain:driver`, `domain:compliance`
- #278 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:db`
- #279 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:model`
- #280 -> `type:tech`, `priority:p0`, `domain:compliance`, `layer:repository`
- #281 -> `type:tech`, `priority:p0`, `domain:driver`, `domain:compliance`, `layer:service`
- #282 -> `type:tech`, `priority:p0`, `domain:compliance`, `domain:web`, `layer:api`
- #283 -> `type:tech`, `priority:p0`, `domain:compliance`, `domain:orders`, `layer:service`
- #285 -> `type:test`, `priority:p0`, `domain:quality`, `domain:compliance`, `layer:test`

### Wave B
- #267 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- #268 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- #269 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- #270 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:web`
- #272 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `domain:orders`, `layer:web`
- #273 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `type:ux`, `layer:web`

### Wave C
- #274 -> `type:feature`, `priority:p2`, `domain:orders`, `domain:compliance`, `layer:service`
- #275 -> `type:feature`, `priority:p1`, `domain:driver`, `domain:compliance`, `layer:ops`
- #276 -> `type:feature`, `priority:p1`, `domain:moderation`, `domain:compliance`, `layer:web`
- #284 -> `type:tech`, `priority:p1`, `domain:compliance`, `layer:ops`

### Wave D
- #110 -> `type:feature`, `priority:p2`, `domain:feed`, `domain:auth`, `layer:api`
- #171 -> `type:epic`, `priority:p2`, `domain:web`, `domain:feed`, `type:ux`
- #172 -> `type:epic`, `priority:p2`, `domain:feed`, `domain:compliance`, `type:ux`
- #173 -> `type:epic`, `priority:p2`, `domain:feed`, `layer:web`
- #174 -> `type:epic`, `priority:p2`, `domain:moderation`, `domain:auth`, `type:security`
- #177 -> `type:feature`, `priority:p2`, `domain:web`, `type:ux`, `layer:web`
- #182 -> `type:feature`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web`
- #184 -> `type:feature`, `priority:p3`, `domain:feed`, `domain:web`, `layer:web`

---

## Note

Этот документ intentionally не пытается автоматически менять GitHub metadata. Его задача — дать **чёткую карту назначения**, чтобы milestone/label triage происходил быстро, одинаково и без разночтений между roadmap и backlog.
