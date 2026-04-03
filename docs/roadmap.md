# BazarDrive Roadmap

## Goal

Зафиксировать понятную roadmap-карту проекта **BazarDrive** по основным продуктовым и техническим направлениям: platform quality, publication/feed UX, moderation/safety, driver compliance и интеграция в taxi order flow.

Этот документ нужен как:
- единая верхнеуровневая карта развития проекта;
- ориентир для GitHub issues / epic decomposition;
- быстрый ответ на вопрос: **что делать сейчас, что следующим шагом, что можно отложить**.

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

2. **Driver / taxi operations platform**
   - профиль водителя;
   - driver onboarding / driver UX docs;
   - документы и trust signals;
   - legal/compliance domain для допуска водителя к работе;
   - будущая интеграция в order flow.

Практически это значит, что BazarDrive развивается как гибрид:
- **marketplace / feed / community layer**;
- **taxi operations / driver compliance platform**.

---

## Roadmap buckets

### Now

То, что даёт наибольший эффект прямо сейчас и разблокирует следующий слой работ.

| Priority | Direction | Issues | Focus |
| --- | --- | --- | --- |
| P0 | Driver compliance foundation | #266, #278, #279, #280, #281, #282 | Миграции, ORM, repository, compliance service, API |
| P0 | Compliance guard in order flow | #283 | Блокировка `go_online` / `accept_order` при invalid compliance |
| P0 | Compliance regression coverage | #285 | Стабильный тестовый контур для core compliance logic |
| P1 | Quality / contracts / release readiness | #175 | OpenAPI sync, regression pack, release checklist |
| P1 | Post-172 trust hardening | #204 | Проверки `verification_state` / `is_verified` без расширения scope |

#### Why now

Сейчас главный стратегический вектор проекта уже смещён в сторону **driver legal profile, documents and taxi compliance**. Без этого order flow и driver UX останутся частично декоративными.

---

### Next

Следующий слой после стабилизации compliance-core.

| Priority | Direction | Issues | Focus |
| --- | --- | --- | --- |
| P1 | Driver legal identity and qualification | #267 | Личные данные, стаж, eligibility prerequisites |
| P1 | Entrepreneur / legal status | #268 | ИП / правовой статус / налоговый режим |
| P1 | Vehicle profile | #269 | Автомобиль, обязательные поля и taxi equipment |
| P1 | Driver documents | #270 | Upload, review, expiry, verification statuses |
| P1 | Waybill flow | #272 | Открытие перед сменой, закрытие после смены |
| P1 | Driver readiness summary | #273 | Summary card: можно ли работать и почему нет |
| P1 | Reminders / expiry automation | #275, #284 | Напоминания и background refresh по срокам |
| P1 | Admin moderation for compliance | #276 | Review UI / decisions / rejection reason / audit |

#### Outcome

Водитель получает не просто форму профиля, а полноценный **readiness cockpit**:
- что заполнено;
- что подтверждено;
- что скоро истекает;
- что прямо сейчас блокирует работу.

---

### Later

Важные направления, которые нужно делать после закрепления core compliance и order gating.

| Priority | Direction | Issues | Focus |
| --- | --- | --- | --- |
| P2 | Feed engagement & interaction | #173 | Реакции, комментарии, `my_reaction`, counts, UX ошибок |
| P2 | Moderation, safety & authorization | #174, #110 | Object-level auth, delete ownership, moderator override |
| P2 | Publication profile & trust UX polish | #171, #172, #177, #204 | Role matrix consistency, documents/trust polishing |
| P2 | Order journal compliance storage | #274 | Snapshot taxi order fields для compliance / export / audit |

#### Outcome

Feed и publication-платформа становятся более живыми, безопасными и предсказуемыми, а taxi-domain получает обязательный слой order journal и compliance storage.

---

### Icebox

То, что имеет смысл сохранить в поле зрения, но не затягивать в ближайшие спринты.

| Priority | Direction | Issues | Focus |
| --- | --- | --- | --- |
| P3 | Feed media expansion | #182, #184 | Дальнейшее развитие сценариев с фото, если останутся пробелы |
| P3 | Larger social/feed growth layer | #173 | Дополнительные engagement-механики после стабилизации core flows |
| P3 | Extended backoffice | #174, #276 | Более крупная модераторская / административная панель |
| P3 | Major visual redesign | n/a | Делать только после закрепления контрактов и сценариев |

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

---

## Strategic sequencing

Если упростить roadmap до одной линии развития, то порядок такой:

1. **Сначала** — quality + contracts + compliance core.
2. **Потом** — driver readiness: legal profile, docs, vehicle, waybill, summary.
3. **Потом** — compliance automation, reminders, admin review, order journal.
4. **Потом** — feed interaction hardening, moderation/auth, publication profile polish.

Это помогает не перепутать приоритеты:
- не полировать вторичный UX раньше, чем готов core eligibility;
- не строить rich interaction layer поверх плавающих контрактов;
- не интегрировать driver order flow до появления реального compliance guard.

---

## Short version

### Now
- compliance backend core;
- guard in order flow;
- compliance tests;
- contracts and release hygiene.

### Next
- driver legal profile;
- entrepreneur / legal section;
- vehicle and documents;
- waybill;
- readiness summary;
- reminders and admin review.

### Later
- feed engagement;
- moderation and object-level authorization;
- publication profile / trust UX polish;
- order journal.

### Icebox
- larger media/social expansion;
- extended backoffice;
- major redesign waves.

---

## Notes

- Этот roadmap описывает **приоритеты и последовательность**, а не жёсткие дедлайны.
- Если order flow станет критическим раньше, допускается ускорить интеграцию части задач из #283 при условии, что compliance core уже собран.
- Для дальнейшей декомпозиции roadmap рекомендуется держать связку:
  - `epic -> wave -> milestone -> implementation issues -> tests/docs sync`.
