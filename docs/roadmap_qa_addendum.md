# QA Addendum to `docs/roadmap.md`

## Purpose

Этот документ добавляет QA-perspective к текущему roadmap BazarDrive.

Он не заменяет `docs/roadmap.md`, а дополняет его теми направлениями, которые критичны для продукта уровня агрегатора с двумя связанными доменами:
- **feed / publication platform**;
- **taxi ordering and ride lifecycle**.

Главная цель этого addendum:
- усилить roadmap с точки зрения money-loss и operations-risk;
- сделать видимыми критичные пассажирские сценарии, payment/location risks и mobile edge cases;
- уменьшить риск того, что roadmap хорошо покрывает compliance, но недопокрывает ride-ordering reality.

---

## Why this addendum is needed

В текущем roadmap сильнее всего раскрыты:
- driver compliance foundation;
- guard in order flow;
- quality / contracts / release readiness;
- driver readiness UX;
- feed hardening and moderation.

Это правильный фундамент, но для реального taxi/feed продукта остаются недораскрытыми критичные QA-домены:
- location reliability;
- payments and billing safety;
- passenger order lifecycle;
- peak-load resilience;
- mobile interruption handling;
- feed-to-taxi integration flows.

---

# Proposed roadmap extensions

## 1. Add a new workstream: Taxi Core Order Lifecycle & Passenger Flow

### Why
Текущий roadmap много говорит о driver readiness и compliance, но недостаточно явно выделяет пассажирский end-to-end lifecycle заказа.

### Goal
Сделать пассажирский taxi flow отдельной first-class осью roadmap:
- создание заказа;
- поиск машины;
- назначение водителя;
- ожидание;
- посадка;
- поездка;
- завершение;
- post-ride states.

### Scope
- create order
- quote / fare preview
- driver search timeout
- matching / rematching
- cancel before assignment
- cancel after assignment
- arrival and ETA updates
- start ride / end ride
- post-ride receipt / dispute / support handoff

### QA focus
- state machine consistency;
- recovery after cancellation/rematch;
- idempotency of order state changes;
- sync between client, backend, and driver state.

### Suggested priority
**Now / Next border**, не Later.

### Suggested insertion into roadmap
Добавить в **Now** или ранний **Next** отдельную строку:

| Priority | Direction | Focus |
| --- | --- | --- |
| P0/P1 | Taxi core order lifecycle | Passenger order creation, matching, ETA, ride state machine, cancel/rematch, post-ride states |

---

## 2. Add a new workstream: Location Reliability & Mapping QA

### Why
Для taxi-продукта геолокация — это денежный и операционный риск, а не просто UI-detail.

### Goal
Сделать reliability геолокации и карт отдельным QA/product engineering workstream.

### Scope
- GPS accuracy
- pickup point confidence
- coordinate drift
- route snapping / map matching
- moving passenger before pickup
- driver/passenger location sync
- manual pin correction
- poor GPS / urban canyon / indoor pickup
- permission downgrade (`precise -> coarse`)
- background location updates

### QA focus
- адрес на карте vs текстовый адрес;
- wrong pickup cost;
- ETA drift;
- incorrect arrival detection;
- fallback behavior when location is unreliable.

### Suggested priority
**Now / Next border**, не Later.

### Suggested insertion into roadmap

| Priority | Direction | Focus |
| --- | --- | --- |
| P0/P1 | Location reliability & mapping | GPS accuracy, pickup confidence, movement before pickup, map matching, degraded location handling |

---

## 3. Add a new workstream: Payments & Billing Safety

### Why
Сейчас roadmap не даёт отдельного payment/billing слоя, а именно он напрямую защищает бизнес от потери денег.

### Goal
Сделать оплату и биллинг отдельной продуктовой и QA-осью.

### Scope
- card binding and validation
- preauth / hold
- capture after ride completion
- cancellation fees
- refunds and partial refunds
- payment retry logic
- duplicate callback protection
- idempotent billing operations
- change payment method before/after assignment
- change card during ride where supported
- failed payment resolution

### QA focus
- money-loss protection;
- PSP callback race conditions;
- receipt and invoice consistency;
- reconciliation between payment state and ride state.

### Suggested priority
**Now**, если сервис заказа такси планируется как real-money product.

### Suggested insertion into roadmap

| Priority | Direction | Focus |
| --- | --- | --- |
| P0 | Payments & billing safety | Hold/capture/refund flows, payment retries, billing idempotency, ride-payment reconciliation |

---

## 4. Add a new workstream: Peak Load / Surge / Resilience Testing

### Why
Для агрегатора час пик, праздники и weather spikes — это штатный режим, а не экзотика.

### Goal
Вынести performance/resilience для taxi + feed в явную roadmap-ветку.

### Scope
- peak ride request load
- mass driver matching
- cancel/rematch storms
- feed traffic spikes
- media-heavy feed load
- payment provider slowdown
- map provider slowdown
- surge/surge-drop transitions
- queue buildup and timeout behavior

### QA focus
- graceful degradation;
- system backpressure;
- retry storms;
- queue visibility;
- SLA/SLO breaches on critical flows.

### Suggested priority
**Next**, но подготовка метрик и сценариев должна начаться раньше.

### Suggested insertion into roadmap

| Priority | Direction | Focus |
| --- | --- | --- |
| P1 | Peak load and resilience | Rush hour, holiday peaks, surge, retry storms, degraded external dependencies |

---

## 5. Add a new workstream: Mobile Edge Cases & Interruption Handling

### Why
Для мобильного taxi-продукта потеря связи, звонки, backgrounding и батарея — стандартная среда использования.

### Goal
Сделать interruption handling видимой частью roadmap, а не implicit test debt.

### Scope
- tunnel / network loss
- switching Wi-Fi <-> LTE
- incoming call during order creation
- background / foreground transitions
- process kill and app restore
- battery saver / 1% battery state
- lost internet during ride
- delayed push / missed realtime update

### QA focus
- state recovery;
- duplicate actions after reconnect;
- stale UI vs actual backend state;
- safe resume of ride/order/payment flow.

### Suggested priority
**Next**.

### Suggested insertion into roadmap

| Priority | Direction | Focus |
| --- | --- | --- |
| P1 | Mobile interruptions and recovery | Network loss, app backgrounding, calls, battery saver, restore after reconnect |

---

## 6. Add a new workstream: Feed-to-Taxi Conversion Flows

### Why
Roadmap уже описывает BazarDrive как гибрид feed/community layer и taxi operations platform, но cross-domain сценарии между ними не вынесены отдельно.

### Goal
Проверить и закрепить сценарии, где feed становится входом в taxi order flow.

### Scope
- ad/promo card -> open taxi order
- prefilled destination from card/deep link
- promo code from feed into ride flow
- campaign card -> tariff screen
- conversion analytics consistency
- safe fallback if target location is unavailable

### QA focus
- deep links;
- prefilled address correctness;
- campaign attribution;
- analytics and billing safety when promo is applied.

### Suggested priority
**Later**, но не Icebox, если продукт реально связывает ленту и такси.

### Suggested insertion into roadmap

| Priority | Direction | Focus |
| --- | --- | --- |
| P2 | Feed-to-taxi integration flows | CTA/deep link to order, prefilled destination, promo propagation, attribution correctness |

---

# Suggested updates to roadmap waves

## Wave A — Core compliance backend

### Keep as-is
Эта волна остаётся логичной и полезной.

### Add QA note
После описания Wave A добавить:

```md
### QA risk note
Wave A stabilizes driver compliance, but does not yet fully protect the business against passenger flow failures, location errors, or payment losses. Those risks must be covered by dedicated workstreams in parallel or immediately after Wave A.
```

---

## Wave B — Driver profile readiness

### Keep as-is
Эта волна остаётся полезной.

### Add QA note

```md
### QA risk note
Wave B improves driver readiness UX, but should not be treated as sufficient protection for the full taxi product until passenger order flow, location reliability, and payment handling are explicitly covered.
```

---

## Wave C — Compliance automation and moderation

### Keep as-is
Эта волна имеет смысл.

### Add QA note

```md
### QA risk note
Wave C strengthens compliance maintenance and auditability, but does not replace load/resilience testing, billing safety validation, or ride lifecycle recovery testing.
```

---

## Wave D — Feed, trust and role UX hardening

### Expand scope slightly
Добавить в Wave D cross-domain note:

```md
### QA risk note
Feed hardening should eventually include cross-domain flows where feed content launches taxi actions, passes prefilled data, or affects conversion-critical order entry points.
```

---

# Suggested new section for `docs/roadmap.md`

## QA-critical product risks not yet fully covered

```md
## QA-critical product risks not yet fully covered

To protect the business from high-cost failures, the roadmap should explicitly track several additional risk domains beyond compliance and feed hardening:

- taxi core passenger order lifecycle
- location reliability and mapping correctness
- payments and billing safety
- peak-load and resilience scenarios
- mobile interruptions and recovery flows
- feed-to-taxi conversion and deep-link scenarios

These areas are critical because they directly affect:
- money loss
- failed or duplicated orders
- wrong pickups and ETA drift
- support load during degraded network conditions
- broken conversion from feed content into taxi actions
```

---

# Suggested QA acceptance criteria for roadmap completeness

Roadmap можно считать более зрелым для production planning, если в нём явно появились:

- отдельный payment workstream;
- отдельный location workstream;
- пассажирский ride lifecycle как отдельная axis;
- performance/resilience workstream для peak periods;
- interruption handling for mobile runtime;
- cross-domain feed-to-taxi flows.

---

## Recommended tools and infrastructure to mention in QA planning

Если roadmap будет расширяться в сторону execution-readiness, полезно явно указать tooling expectations:

- Appium / Maestro for mobile E2E
- Charles / Proxyman for network and payment debugging
- route simulation / mock GPS tooling
- payment sandbox with failure-mode coverage
- k6 / Locust / JMeter for load testing
- observability with correlation ids across feed -> order -> payment -> ride

---

## Final QA position

Текущий roadmap — хороший foundation-doc для compliance-driven развития, но недостаточный как защита от high-cost operational failures в real taxi + feed product.

После добавления workstreams из этого addendum roadmap будет лучше защищать продукт от:
- багов оплаты;
- багов геолокации;
- потери заказа при interruptions;
- массовых деградаций в час пик;
- некорректных переходов между лентой и заказом такси.
