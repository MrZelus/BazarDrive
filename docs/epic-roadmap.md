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
