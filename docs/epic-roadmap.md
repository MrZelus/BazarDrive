# BazarDrive Epic Roadmap (Core Platform)

Ниже — базовая карта Epic/Sub-epic для планирования в GitHub или Linear.

## Epic 1. Driver Readiness Platform
- **1.1 Driver Profile and Onboarding**: роль, базовый профиль, данные водителя, прогресс, статус допуска, следующий шаг.
- **1.2 Driver Documents and Compliance**: загрузка/проверка документов, review comments, rejected/reupload, сроки действия, compliance states.
- **1.3 Taxi / IP Business Identity**: форма деятельности, ИНН/ОГРНИП, налоговый режим, регион, автомобиль, правовая привязка к допуску.
- **1.4 Driver Availability and Going Online**: готовность к линии, проверки перед online, активная смена, вход/выход с линии.
- **1.5 Readiness Contracts and Validation**: readiness summary API, blocking reasons, final readiness gate, server checks, contract tests.

## Epic 2. Orders Marketplace Core
- **2.1 Passenger Order Creation**: создание заказа, адреса, комментарии, время поездки, scheduled orders.
- **2.2 Driver Order Intake**: список/карточка заказов, принятие, доступность заказа для водителя.
- **2.3 Order Lifecycle**: `CREATED` → `ACCEPTED` → `ARRIVING` → `ONTRIP` → `DONE` + `CANCELED`/`EXPIRED`.
- **2.4 Active Trip UX**: активная карточка, переходы статусов, маршрут и важные данные.

## Epic 3. Feed, Posts, and Public Presence
- **3.1 Publish Profile**: display name, фото, bio, publish-ready state.
- **3.2 Feed Posting**: создание, типы и публикация постов.
- **3.3 Feed Engagement**: реакции, комментарии, counters.
- **3.4 Search and Discovery**: поиск, фильтры, сортировка, выдача.

## Epic 4. Trust, Rules, and Moderation
- **4.1 User-facing Rules and Requirements**: правила, требования к документам, legal summaries.
- **4.2 Trust States and Blocking Reasons**: причины блокировки, severity, next step, target section.
- **4.3 Moderation and Review Flows**: review states, approve/reject, moderation comments, escalation logic.

## Epic 5. Payouts and Driver Earnings
- **5.1 Payout Profile**: способ получения, реквизиты, статус выплат.
- **5.2 Earnings History**: начисления, история выплат, детализация.
- **5.3 Financial Readiness Rules**: влияние payout profile на допуск, обязательные поля, блокировки/предупреждения.

## Epic 6. Admin and Backoffice
- **6.1 Document Review Backoffice**: очередь документов, approve/reject, notes, audit trail.
- **6.2 Driver Profile Review**: ручная проверка, блокировки, override readiness.
- **6.3 Support and Resolution Tools**: support actions, исправления данных, ручные решения.

## Epic 7. Design System and Mobile UX Consistency
- **7.1 Profile UI System**: hero-card, status-card, checklist, document-card, sticky CTA.
- **7.2 App-wide States**: empty/loading/error/pending/success.
- **7.3 Navigation and Layout Consistency**: bottom nav, sticky bars, spacing, typography, mobile hierarchy.

## Epic 8. Data Contracts and Domain Model
- **8.1 Domain Entities**: `DriverProfile`, `DriverDocument`, `BusinessProfile`, `Vehicle`, `PublishProfile`, `ReadinessStatus`, `BlockingReason`.
- **8.2 Enum Normalization**: document/readiness statuses, business/employment/document types.
- **8.3 API Surface**: profile/documents/readiness/validation APIs.

## Epic 9. Analytics and Observability
- **9.1 Onboarding Funnel Metrics**: старт onboarding, drop-off, completion, readiness conversion.
- **9.2 Compliance Metrics**: missing docs, rejection rates, review time, expired docs.
- **9.3 Product and Error Observability**: UI/backend errors, perf hotspots, alerts.

## Phase plan
- **Phase A**: Epic 1 + Epic 8 + Epic 7.
- **Phase B**: Epic 4 + Epic 6.
- **Phase C**: Epic 2 + Epic 5.
- **Phase D**: Epic 3 + Epic 9.

## Recommended starter set
1. Driver Readiness Platform
2. Orders Marketplace Core
3. Design System and Mobile UX Consistency
4. Data Contracts and Domain Model

## QA review checklist for this roadmap

### 1) Coverage and decomposition
- [ ] У каждой Epic есть минимум 3 sub-epic с чёткой продуктовой ценностью.
- [ ] Нет дублирования между Epic 1/4/6 (readiness, trust, backoffice) — границы ответственности зафиксированы.
- [ ] Для каждого sub-epic понятен владелец (product + tech owner).

### 2) Contract-first readiness
- [ ] Для Epic 1, 2, 8 определены основные domain entities и enum-контракты до начала UI-реализации.
- [ ] Изменения контрактов сопровождаются backward-compatibility планом и миграциями.
- [ ] На ключевые readiness/checking API запланированы contract tests.

### 3) Delivery quality gates
- [ ] Для каждой sub-epic есть measurable acceptance criteria (SLA, conversion, error budget).
- [ ] Для критичных пользовательских потоков предусмотрены loading/empty/error/success состояния.
- [ ] Для backend-изменений заложены smoke/regression проверки в CI.

### 4) Dependency and risk control
- [ ] Взаимозависимости между фазами A→D отражены в issue links и milestones.
- [ ] Для compliance и moderation задач обозначены юридические/операционные риски.
- [ ] Для payout и orders задач обозначены финансовые и антифрод-риски.

### 5) Observability and post-release
- [ ] Для каждой Epic заранее определены метрики результата и мониторинг ошибок.
- [ ] Для production rollout предусмотрены feature flags и rollback-процедуры.
- [ ] После релиза запланирован review результатов (7/14/30 дней).
