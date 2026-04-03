# BazarDrive Roadmap — QA-integrated Draft

## Goal

Зафиксировать roadmap-карту проекта **BazarDrive** по основным продуктовым и техническим направлениям: platform quality, publication/feed UX, moderation/safety, driver compliance, taxi core order flow и QA-critical risk domains.

Этот документ нужен как:
- единая верхнеуровневая карта развития проекта;
- ориентир для GitHub issues / epic decomposition;
- быстрый ответ на вопрос: **что делать сейчас, что следующим шагом, что можно отложить**;
- QA-visible карта product risks для гибридного продукта, где вместе живут **лента** и **сервис заказа такси**.

---

## Current project shape

На текущем этапе у проекта уже есть две сильные оси развития:

1. **Feed / publication platform**
   - гостевая лента;
   - публикация постов;
   - профиль публикации;
   - role-based profile UX;
   - документы / trust layer;
   - moderation-ready API surface.

2. **Taxi platform**
   - driver onboarding / readiness / compliance;
   - driver documents and trust signals;
   - legal/compliance domain для допуска водителя к работе;
   - taxi order flow integration;
   - location, payment, ride lifecycle и peak-load risks как отдельные критичные QA-domains.

Практически это значит, что BazarDrive развивается как гибрид:
- **marketplace / feed / community layer**;
- **taxi ordering / ride lifecycle / driver operations platform**.

---

## QA-critical product risks that must stay visible

Чтобы roadmap защищал не только архитектуру, но и деньги бизнеса, в нём должны быть видимы следующие risk domains:

- taxi core passenger order lifecycle
- location reliability and mapping correctness
- payments and billing safety
- peak-load and resilience scenarios
- mobile interruptions and recovery flows
- feed-to-taxi conversion and deep-link scenarios

Эти направления напрямую влияют на:
- money loss
- failed or duplicated orders
- wrong pickups and ETA drift
- support load при деградации сети
- broken conversion from feed content into taxi actions

---

## Roadmap buckets

### Now

То, что даёт наибольший эффект прямо сейчас и разблокирует следующий слой работ.

| Priority | Direction | Issues / Focus | Why now |
| --- | --- | --- | --- |
| P0 | Driver compliance foundation | #266, #278, #279, #280, #281, #282 | Нужен технический фундамент driver eligibility |
| P0 | Compliance guard in order flow | #283 | Блокировка `go_online` / `accept_order` при invalid compliance |
| P0 | Compliance regression coverage | #285 | Стабильный тестовый контур для core compliance logic |
| P0 | Payments & billing safety | hold/capture/refund flows, payment retries, billing idempotency, ride-payment reconciliation | Защита бизнеса от прямой потери денег |
| P0/P1 | Taxi core order lifecycle | passenger order creation, matching, ETA, ride state machine, cancel/rematch, post-ride states | Без этого ride product остаётся неполным |
| P0/P1 | Location reliability & mapping | GPS accuracy, pickup confidence, movement before pickup, map matching, degraded location handling | Геолокация — денежный и операционный риск |
| P1 | Quality / contracts / release readiness | #175 | OpenAPI sync, regression pack, release checklist |
| P1 | Post-172 trust hardening | #204 | Проверки `verification_state` / `is_verified` без расширения scope |

#### Why now

Сейчас главный стратегический вектор проекта уже смещён в сторону **driver legal profile, documents and taxi compliance**. Это правильный фундамент. Но для real taxi product этого недостаточно без явного покрытия:
- пассажирского order lifecycle;
- геолокации;
- оплаты и биллинга.

---

### Next

Следующий слой после стабилизации compliance-core и базовых taxi risk domains.

| Priority | Direction | Issues / Focus | Outcome |
| --- | --- | --- | --- |
| P1 | Driver legal identity and qualification | #267 | Личные данные, стаж, eligibility prerequisites |
| P1 | Entrepreneur / legal status | #268 | ИП / правовой статус / налоговый режим |
| P1 | Vehicle profile | #269 | Автомобиль, обязательные поля и taxi equipment |
| P1 | Driver documents | #270 | Upload, review, expiry, verification statuses |
| P1 | Waybill flow | #272 | Открытие перед сменой, закрытие после смены |
| P1 | Driver readiness summary | #273 | Summary card: можно ли работать и почему нет |
| P1 | Reminders / expiry automation | #275, #284 | Напоминания и background refresh по срокам |
| P1 | Admin moderation for compliance | #276 | Review UI / decisions / rejection reason / audit |
| P1 | Peak load and resilience | rush hour, holiday peaks, surge, retry storms, degraded external dependencies | Подготовка к hours-of-peak и weather spikes |
| P1 | Mobile interruptions and recovery | network loss, app backgrounding, calls, battery saver, restore after reconnect | Стабильность при реальном мобильном использовании |

#### Outcome

Водитель получает полноценный **readiness cockpit**, а продукт начинает устойчиво вести себя:
- в час пик;
- при плохой связи;
- при interruptions;
- при реальных поездках с оплатой и изменением статусов.

---

### Later

Важные направления после закрепления taxi core, compliance, resilience и recovery layers.

| Priority | Direction | Issues / Focus | Outcome |
| --- | --- | --- | --- |
| P2 | Feed engagement & interaction | #173 | Реакции, комментарии, `my_reaction`, counts, UX ошибок |
| P2 | Moderation, safety & authorization | #174, #110 | Object-level auth, delete ownership, moderator override |
| P2 | Publication profile & trust UX polish | #171, #172, #177, #204 | Role matrix consistency, documents/trust polishing |
| P2 | Order journal compliance storage | #274 | Snapshot taxi order fields для compliance / export / audit |
| P2 | Feed-to-taxi integration flows | deep links, prefilled destination, promo propagation, attribution correctness | Связать feed и taxi не только концептуально, но и продуктово |

#### Outcome

Feed и publication-платформа становятся более живыми, безопасными и предсказуемыми, а taxi-domain получает cross-domain conversion flows и order journal support layer.

---

### Icebox

То, что имеет смысл сохранить в поле зрения, но не затягивать в ближайшие спринты.

| Priority | Direction | Focus |
| --- | --- | --- |
| P3 | Feed media expansion | Дальнейшее развитие сценариев с фото/медиа, если останутся пробелы |
| P3 | Larger social/feed growth layer | Дополнительные engagement-механики после стабилизации core flows |
| P3 | Extended backoffice | Более крупная модераторская / административная панель |
| P3 | Major visual redesign | Делать только после закрепления контрактов и сценариев |

---

## Recommended implementation waves

### Wave A — Core compliance backend

**Goal:** собрать доменную и техническую основу driver compliance.

**Includes:**
- #266
- #278
- #279
- #280
- #281
- #282
- #285
- #175

**Result:**
- есть миграции и модели;
- есть repository layer;
- есть compliance service;
- есть API;
- есть тестовый каркас;
- контракты и release-readiness не расползаются.

### QA risk note
Wave A stabilizes driver compliance, but does not yet fully protect the business against passenger flow failures, location errors, or payment losses. Эти риски должны покрываться параллельными или следующими workstreams.

---

### Wave B — Driver profile readiness

**Goal:** вывести driver profile из состояния «заготовка» в состояние «готов к реальному допуску».

**Includes:**
- #267
- #268
- #269
- #270
- #272
- #273

**Result:**
- водитель заполняет личные данные;
- водитель добавляет автомобиль и документы;
- водитель работает с путевым листом;
- UI показывает readiness state и next required action.

### QA risk note
Wave B улучшает driver readiness UX, но не должна считаться достаточной защитой taxi product без явного покрытия passenger order flow, location reliability и payment handling.

---

### Wave C — Compliance automation and moderation

**Goal:** сделать compliance не ручной, а живой и самоподдерживаемый.

**Includes:**
- #275
- #284
- #276
- #274

**Result:**
- документы автоматически переходят в `expired` / `expiring_soon`;
- пользователь получает напоминания;
- модератор может принимать решения по документам;
- order journal сохраняет обязательные taxi/compliance поля.

### QA risk note
Wave C усиливает compliance maintenance и auditability, но не заменяет load/resilience testing, billing safety validation и ride lifecycle recovery testing.

---

### Wave D — Feed, trust and role UX hardening

**Goal:** довести publication/feed часть проекта до стабильного продуктового состояния.

**Includes:**
- #173
- #174
- #110
- #171
- #172
- #177
- #204

**Result:**
- устойчивые feed interactions;
- прозрачные ownership / moderation rules;
- консистентный role-based publication profile UX;
- trust layer синхронизирован с UI, docs и tests.

### QA risk note
Feed hardening должно в перспективе включать cross-domain flows, где feed content запускает taxi actions, передаёт prefilled data или влияет на conversion-critical order entry points.

---

## Strategic sequencing

Если упростить roadmap до одной линии развития, то порядок такой:

1. **Сначала** — quality + contracts + compliance core.
2. **Параллельно или сразу после** — payments, location reliability, passenger order lifecycle.
3. **Потом** — driver readiness: legal profile, docs, vehicle, waybill, summary.
4. **Потом** — peak-load, interruption handling, resilience.
5. **Потом** — compliance automation, reminders, admin review, order journal.
6. **Потом** — feed interaction hardening, moderation/auth, publication profile polish, feed-to-taxi flows.

Это помогает не перепутать приоритеты:
- не полировать вторичный UX раньше, чем защищены деньги и ride state machine;
- не строить rich interaction layer поверх плавающих location/payment foundations;
- не интегрировать feed и taxi глубже до появления корректных deep-link и conversion flows.

---

## Recommended tools and infrastructure to mention in QA planning

Если roadmap расширяется в сторону execution-readiness, полезно явно учитывать tooling expectations:

- Appium / Maestro for mobile E2E
- Charles / Proxyman for network and payment debugging
- route simulation / mock GPS tooling
- payment sandbox with failure-mode coverage
- k6 / Locust / JMeter for load testing
- observability with correlation ids across feed -> order -> payment -> ride

---

## Suggested QA acceptance criteria for roadmap completeness

Roadmap можно считать более зрелым для production planning, если в нём явно появились:
- отдельный payment workstream;
- отдельный location workstream;
- пассажирский ride lifecycle как отдельная axis;
- performance/resilience workstream для peak periods;
- interruption handling for mobile runtime;
- cross-domain feed-to-taxi flows.

---

## Short version

### Now
- compliance backend core;
- guard in order flow;
- compliance tests;
- contracts and release hygiene;
- payments and billing safety;
- taxi core order lifecycle;
- location reliability and mapping.

### Next
- driver legal profile;
- entrepreneur / legal section;
- vehicle and documents;
- waybill;
- readiness summary;
- reminders and admin review;
- peak load and resilience;
- mobile interruptions and recovery.

### Later
- feed engagement;
- moderation and object-level authorization;
- publication profile / trust UX polish;
- order journal;
- feed-to-taxi integration flows.

### Icebox
- larger media/social expansion;
- extended backoffice;
- major redesign waves.

---

## Final QA position

Этот roadmap сильнее базового варианта защищает продукт не только от compliance gaps, но и от high-cost operational failures в real taxi + feed product.

После реального включения workstreams из этой версии продукт будет лучше защищён от:
- багов оплаты;
- багов геолокации;
- потери заказа при interruptions;
- массовых деградаций в час пик;
- некорректных переходов между лентой и заказом такси.

---

## Notes

- Этот roadmap описывает **приоритеты и последовательность**, а не жёсткие дедлайны.
- Если order flow станет критическим раньше, допускается ускорить интеграцию payment/location/order-lifecycle workstreams ещё до полного завершения driver readiness UX.
- Для дальнейшей декомпозиции roadmap рекомендуется держать связку:
  - `epic -> wave -> milestone -> implementation issues -> tests/docs sync`.
