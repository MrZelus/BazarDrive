# BazarDrive Project Operating Plan

Этот документ фиксирует **операционную модель развития проекта BazarDrive**: как должны быть связаны продуктовые идеи, документация, UX, API, Telegram bot, база данных, тесты, PR-процесс и ответственность по доменам.

Документ опирается на уже подготовленные карты проекта:
- architecture maps
- role flows
- permissions matrix
- lifecycle map
- governance map
- RACI map

---

## 1. Цель документа

Нужен не просто backlog, а **единый operating plan**, который отвечает на вопросы:
- как развивается проект;
- кто за что отвечает;
- как изменения проходят путь от идеи до merge;
- как не терять связность между docs, bot, API и data layer;
- как удерживать систему в контролируемом виде по мере роста.

---

## 2. Operating model проекта

BazarDrive должен развиваться как единая система из пяти взаимосвязанных слоёв:

1. **Product / Scope layer**
   - идеи;
   - product goals;
   - issues / epics;
   - acceptance criteria.

2. **Docs / Governance layer**
   - `README.md`
   - `docs/contributing.md`
   - `docs/security/permissions_matrix.md`
   - flow docs / architecture docs
   - `docs/openapi.yaml`

3. **Implementation layer**
   - Web UI
   - HTTP API
   - Telegram bot
   - services
   - repository / DB / migrations

4. **Quality layer**
   - tests
   - smoke checks
   - regression checks
   - manual verification

5. **Delivery layer**
   - PR template
   - PR review
   - merge rules
   - release discipline

Ключевой принцип:

> Любое существенное изменение должно быть связано не только с кодом, но и с документацией, проверками и зоной ответственности.

---

## 3. Change lifecycle

Каждое изменение в проекте должно проходить путь:

`Idea -> Issue/Epic -> Docs/Design -> Code -> Tests -> PR -> Review -> Merge -> Updated system state`

### Шаги

#### 1. Idea / Problem / Request
Источник изменения:
- новая функция;
- баг;
- UX-проблема;
- compliance / legal requirement;
- refactor / technical debt.

#### 2. Issue / Epic
Для значимых изменений нужно фиксировать:
- цель;
- scope;
- business value;
- критерии готовности;
- связи с tech issues.

#### 3. Docs / Design
Перед или во время реализации должны обновляться:
- role flows;
- API contracts;
- permissions;
- contributing / operating docs;
- architecture maps;
- UX схемы.

#### 4. Implementation
Изменения в коде должны быть ограничены scope задачи и не смешивать unrelated work.

#### 5. Tests / Verification
Нужно проверить:
- корректность;
- целостность флоу;
- отсутствие регрессий;
- совместимость между web / API / bot.

#### 6. PR / Review
PR должен быть:
- внятно описан;
- связан с issue;
- ограничен по scope;
- понятен reviewer-у.

#### 7. Merge / Updated system state
После merge должны быть синхронизированы:
- docs;
- код;
- flows;
- permissions;
- карты проекта.

---

## 4. Домены проекта

### 4.1 Docs
Что входит:
- contributing
- permissions
- openapi
- flow docs
- architecture docs

Роль домена:
- хранить правила проекта;
- описывать границы ответственности;
- не давать коду и продукту разъехаться.

### 4.2 Web UI
Что входит:
- guest feed
- profile
- rules
- documents
- driver summary UI

Роль домена:
- пользовательский интерфейс;
- отображение role-based navigation;
- frontend UX для publication, compliance, reminders.

### 4.3 HTTP API
Что входит:
- handlers
- services
- payloads
- validation
- transport layer

Роль домена:
- центральный прикладной слой web-интерфейса;
- реализация API-контрактов;
- orchestration между UI и repository/services.

### 4.4 Telegram bot
Что входит:
- пользовательские сценарии;
- moderation;
- driver status;
- shift / accept order / notifications.

Роль домена:
- второй интерфейс проекта;
- operational UX;
- связь с moderation и driver flows.

### 4.5 Data layer
Что входит:
- repository
- migrations
- SQLite schema
- persistence

Роль домена:
- источник истины для данных;
- обеспечение совместимости и воспроизводимости состояния.

### 4.6 RBAC / Security
Что входит:
- roles
- permissions
- eligibility guard
- admin/moderator separation
- audit-sensitive actions

Роль домена:
- защита системы от логического расползания прав;
- удержание безопасной модели доступа.

### 4.7 Compliance / Moderation
Что входит:
- driver profile
- documents
- waybill
- review decisions
- moderation status flows

Роль домена:
- соответствие требованиям проекта и перевозочной логике;
- допуск к операциям только готовых профилей.

### 4.8 Tests / QA
Что входит:
- unit tests
- smoke tests
- regression tests
- UI checks

Роль домена:
- раннее обнаружение поломок;
- страховка против неявных конфликтов между bot / API / UI.

### 4.9 Release / PR discipline
Что входит:
- PR template
- review process
- merge discipline
- release hygiene

Роль домена:
- не давать в main попадать несвязные или неописанные изменения.

---

## 5. Governance model

Ниже описана базовая governance-модель проекта.

### Product / Scope owner
Отвечает за:
- что входит в scope;
- какие задачи приоритетны;
- где заканчивается текущий PR/issue.

### UX / Docs owner
Отвечает за:
- UX flows;
- docs quality;
- архитектурные и продуктовые схемы.

### API / Service owner
Отвечает за:
- HTTP handlers;
- business services;
- transport-to-service discipline.

### Bot owner
Отвечает за:
- Telegram UX;
- bot handlers;
- согласованность bot flow с API/business logic.

### Data / Migration owner
Отвечает за:
- repository;
- DB schema;
- migration stability.

### Security / RBAC owner
Отвечает за:
- permission model;
- доступы по ролям;
- guard restrictions;
- чувствительные операции.

### Moderation / Compliance owner
Отвечает за:
- documents review;
- compliance decisions;
- readiness / restrictions / moderation flows.

### QA / Test owner
Отвечает за:
- smoke / regression strategy;
- test coverage для критичных потоков.

### Release / Merge owner
Отвечает за:
- hygiene PR;
- финальную проверку scope;
- merge discipline.

---

## 6. RACI-подход

Упрощённо:

- **Docs / Contributing / OpenAPI**
  - A: Product / Scope
  - R: UX / Docs
  - C: API / Security / Release

- **Web UI**
  - A: Product / Scope
  - R: UX / Docs
  - C: QA / API

- **HTTP API / Services**
  - A: Product / Scope
  - R: API / Services
  - C: Data / Security / Compliance

- **Telegram Bot**
  - A: Product / Scope
  - R: Bot owner
  - C: API / Compliance

- **Data / Migrations**
  - A/R: Data owner
  - C: API / QA

- **RBAC / Security**
  - A/R: Security owner
  - C: API / Bot / Release

- **Compliance / Moderation**
  - A/R: Moderation / Compliance owner
  - C: Bot / Security / API

- **Tests / QA**
  - A/R: QA owner
  - C: все домены, затронутые scope

- **PR / Release**
  - A/R: Release owner
  - C: Product / QA / Security / Docs

---

## 7. Обязательные правила для эволюции проекта

### Rule 1. Docs and code must move together
Если меняется:
- роли;
- permissions;
- API contract;
- flow пользователя;
- moderation/compliance;

то нужно обновлять docs и/или схемы.

### Rule 2. No giant mixed PRs
Один PR не должен одновременно:
- менять UX;
- переписывать API;
- трогать migrations;
- чинить unrelated тесты;
- переписывать docs без явной связи.

### Rule 3. Bot and API must not fork business logic
Guard / compliance / readiness logic не должна дублироваться отдельно в bot и API.
Она должна жить на service/domain уровне.

### Rule 4. Role model must stay explicit
Нельзя допускать размывания прав между:
- moderator
- admin
- driver
- passenger
- guest

### Rule 5. Main branch should reflect the real system
После merge состояние main должно быть:
- понятным;
- воспроизводимым;
- документированным;
- не конфликтующим с текущими схемами проекта.

---

## 8. План развития проекта

### Phase 1. Stabilize project governance
- привести `contributing.md` к project-wide формату;
- утвердить permissions matrix;
- использовать PR template;
- начать поддерживать issue -> PR -> docs связь.

### Phase 2. Align docs with implementation
- синхронизировать role flows;
- синхронизировать Users API, compliance, moderation и permissions;
- поддерживать архитектурные схемы актуальными.

### Phase 3. Harden system boundaries
- зафиксировать RBAC слой;
- убрать дублирование бизнес-логики между bot и API;
- укрепить migration discipline;
- зафиксировать release/merge rules.

### Phase 4. Improve quality discipline
- расширять smoke/regression покрытие;
- проверять критичные role-based потоки;
- использовать docs и схемы как часть review процесса.

### Phase 5. Build operational transparency
- держать governance и lifecycle maps актуальными;
- использовать RACI как основу для разделения ответственности;
- сделать operating board основным обзорным документом проекта.

---

## 9. Definition of healthy project state

Проект находится в здоровом состоянии, если:
- docs отражают реальную систему;
- PR не тащат лишний scope;
- bot / API / docs / data согласованы;
- роли и permissions понятны;
- compliance и moderation flows формализованы;
- тесты ловят критичные регрессии;
- можно быстро понять, кто за что отвечает.

---

## 10. Связанные документы

- `README.md`
- `docs/contributing.md`
- `docs/security/permissions_matrix.md`
- `docs/openapi.yaml`
- `docs/feed_navigation_publish_flow.md`
- `docs/driver_profile_wireframe_spec.md`

Также рекомендуется хранить рядом ссылки на FigJam артефакты:
- architecture maps
- role flows
- lifecycle map
- governance map
- RACI map
- operating board

---

## 11. Next recommended actions

1. Довести до merge project-wide `docs/contributing.md`
2. Добавить / активировать PR template
3. Зафиксировать current permissions / roles как каноничную модель
4. Синхронизировать docs по Users API и compliance flow
5. Свести operating board в один общий обзорный артефакт
6. Использовать этот документ как основу для review и roadmap planning

---

BazarDrive должен расти не как набор разрозненных фич, а как управляемая система, в которой документация, код, роли, проверки и релизный процесс развиваются согласованно.
