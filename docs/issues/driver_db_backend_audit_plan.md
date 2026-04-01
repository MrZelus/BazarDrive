# Driver DB and Backend Audit Plan

Этот документ фиксирует следующий практический шаг для driver domain в BazarDrive:

**не расширять docs и не уходить сразу во frontend, а сначала проверить БД и выровнять backend с canonical contract layer.**

---

## 1. Почему это следующий шаг

В репозитории уже есть:

- driver docs как source of truth;
- canonical enums, error codes и event names;
- backend contract services;
- operation-layer integration;
- HTTP payload helpers;
- handler adapters;
- wiring plan для `app/api/http_handlers.py`;
- endpoint contract test scaffolds.

Значит следующий узкий и правильный шаг:

1. проверить persisted truth в БД;
2. выровнять backend services с реальными моделями;
3. после этого довести HTTP wiring;
4. только потом идти во frontend gating.

---

## 2. Цель

Проверить, что реальные таблицы, ORM models и runtime services не расходятся с canonical driver contract.

Итогом должно быть:

- persisted status fields соответствуют canonical enums;
- derived fields не дублируются хаотично в БД;
- ownership и invariants можно валидировать на backend;
- backend services используют реальные model facts;
- HTTP layer получает устойчивую truth-base для canonical responses.

---

## 3. Scope

### Входит

- audit ORM models / schema / migrations для driver domain;
- проверка persisted statuses;
- проверка ownership links;
- проверка shift / trip sheet / order invariants;
- проверка совместимости service layer с моделью данных;
- подготовка списка schema fixes или migration notes;
- подготовка backend follow-up перед HTTP wiring.

### Не входит

- frontend button gating;
- крупный UI refactor;
- полные E2E tests;
- новые UX docs без явной найденной неоднозначности.

---

## 4. Canonical persisted statuses to verify

Проверить, что persisted layer согласован со следующими canonical значениями.

### Profile status

- `draft`
- `incomplete`
- `pending_verification`
- `approved`
- `rejected`
- `blocked`

### Document status

- `missing`
- `uploaded`
- `checking`
- `approved`
- `rejected`
- `expired`

### Trip sheet status

- `missing`
- `open`
- `requires_closing`
- `closed`

### Shift status

- `offline`
- `ready`
- `online`
- `busy`
- `ending`
- `closed`

### Order status

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

---

## 5. DB audit checklist

Найти реальные model/schema/migration files для:

- driver profile;
- driver documents;
- trip sheet / waybill;
- shift;
- order.

Для каждого persisted поля проверить:

### 5.1. Status field audit

- [ ] какие значения поле хранит сейчас;
- [ ] есть ли legacy значения вне canonical enums;
- [ ] есть ли nullable / blank states, которые ломают contract;
- [ ] есть ли дефолты, противоречащие docs.

### 5.2. Ownership audit

- [ ] profile привязан к driver/user корректно;
- [ ] documents ownership можно проверить строго;
- [ ] trip sheet ownership можно проверить строго;
- [ ] shift ownership можно проверить строго;
- [ ] order assignment/ownership можно проверить строго.

### 5.3. Invariant audit

- [ ] активный order не допускает конфликтного shift state;
- [ ] blocked profile может быть вычислен и enforced;
- [ ] missing/rejected/expired docs влияют на readiness;
- [ ] trip sheet requirement может быть валидирован без обходных путей;
- [ ] модель не позволяет молча перепрыгивать forbidden transitions.

### 5.4. Derived vs persisted audit

- [ ] `eligibility_status` не хранится как хаотичный независимый источник истины без нужды;
- [ ] `can_go_online` остаётся derived field, а не persisted truth;
- [ ] `next_allowed_actions` не зашиваются в БД как суррогат статуса;
- [ ] derived readiness строится из model facts.

---

## 6. Backend service audit checklist

Проверить backend contract/services против реальных моделей.

### 6.1. `app/services/driver_status_service.py`

Проверить:

- [ ] transition maps совпадают с реальными persisted states;
- [ ] сервис не использует статусы, которых нет в БД;
- [ ] forbidden transitions реально можно отловить на runtime слое;
- [ ] `compute_eligibility()` использует реальные model facts;
- [ ] hard blockers корректно дают `blocked`.

Минимальные контрольные вопросы:

- можно ли реально вычислить `profile_not_approved`;
- можно ли реально вычислить `required_documents_missing_or_invalid`;
- можно ли реально вычислить `trip_sheet_not_ready`;
- не теряется ли distinction между `not_ready` и `partially_ready`.

### 6.2. `app/services/driver_permissions_service.py`

Проверить:

- [ ] ownership checks можно опереть на реальные model relations;
- [ ] `can_go_online()` использует достаточный набор фактов;
- [ ] `can_accept_order()` не допускает дыр в assigned scope;
- [ ] blocked profile / not eligible cases маппятся в canonical errors;
- [ ] permission checks не расходятся с DB realities.

### 6.3. `app/services/driver_notifications_service.py`

Проверить:

- [ ] event routing можно собрать из реальных entity ids;
- [ ] dedupe key можно построить стабильно;
- [ ] `state_version` реально доступен или нужен заменитель;
- [ ] notification plan не опирается на отсутствующие данные.

---

## 7. Expected outputs of this audit

По итогам аудита должен появиться один из двух результатов:

### Вариант A. Schema already compatible

Если всё совместимо:

- зафиксировать, что persisted layer готов;
- перейти к HTTP wiring step.

### Вариант B. Schema gaps found

Если есть расхождения:

- составить список exact schema/model gaps;
- определить, что правится миграцией, а что сервисным слоем;
- только после этого переходить к HTTP wiring.

---

## 8. Follow-up after audit

После DB + backend audit следующий шаг:

### 8.1. HTTP wiring

Применить минимальный wiring по:

- `docs/issues/driver_http_handlers_wiring_plan.md`

То есть:

- подключить adapters в `app/api/http_handlers.py`;
- заменить inline payload dicts на canonical adapter calls;
- сохранить control flow без большого рефактора.

### 8.2. Activate API contract tests

После wiring:

- снять `@unittest.skip(...)` с endpoint contract tests;
- проверить canonical `error.code`;
- проверить canonical `event_name`;
- проверить `shift_status`, `order_status`, `trip_sheet_status`.

### 8.3. Only then frontend gating

Только после стабилизации API переходить к:

- `test_driver_ui_gating.py`
- blocker banners
- CTA visibility / disabled states
- flow-level UI checks.

---

## 9. Acceptance criteria

- [ ] найдены и просмотрены реальные DB/model/migration files driver domain;
- [ ] зафиксировано, какие status fields persisted;
- [ ] найдено и описано наличие или отсутствие legacy status values;
- [ ] ownership links проверены;
- [ ] cross-domain invariants проверены на уровне модели данных;
- [ ] service layer сверена с реальными DB facts;
- [ ] определено, нужен ли schema fix / migration;
- [ ] после аудита можно безопасно переходить к HTTP wiring.

---

## 10. Practical priority

Правильная лестница для ближайших шагов такая:

1. **DB audit**
2. **Backend service alignment**
3. **HTTP wiring**
4. **API contract activation**
5. **Frontend gating**
6. **E2E**

Это снижает ложный шум и даёт понятную диагностику по слоям вместо смешанного хаоса.
