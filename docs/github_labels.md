# Recommended GitHub Labels for BazarDrive

## Purpose

Этот документ фиксирует рекомендуемый каталог **GitHub labels** для проекта **BazarDrive**.

Он нужен для того, чтобы:
- roadmap, milestones и issues были связаны одной системой;
- задачи можно было быстро фильтровать по домену, слою, типу и приоритету;
- backlog не превращался в коробку с деталями без подписей.

Связанные документы:
- `docs/roadmap.md`
- `docs/github_milestones.md`
- `docs/github_milestone_descriptions.md`

---

## Label groups

Рекомендуется использовать 4 основные группы label-ов:

1. **Domain** — о какой части продукта задача
2. **Layer** — на каком техническом слое изменения
3. **Type** — что это за работа по характеру
4. **Priority** — насколько срочно / важно

Опционально можно добавить 5-ю группу:

5. **Status / Workflow** — состояние подготовки задачи

---

## 1. Domain labels

Эти labels помогают понять, к какому продуктовому направлению относится задача.

| Label | Color | Description |
| --- | --- | --- |
| `domain:driver` | `1D76DB` | Задачи, связанные с профилем водителя, driver UX и operational driver flows |
| `domain:compliance` | `B60205` | Legal/compliance, документы, eligibility, waybill, readiness, audit |
| `domain:feed` | `5319E7` | Гостевая лента, публикации, реакции, комментарии, media |
| `domain:moderation` | `FBCA04` | Модерация контента, review flows, override behavior, safety rules |
| `domain:quality` | `0E8A16` | Контракты, тесты, release readiness, regression hardening |
| `domain:auth` | `D93F0B` | Авторизация, ownership checks, object-level permissions, CORS/auth rules |
| `domain:docs` | `006B75` | Документация, roadmap, specs, OpenAPI sync, README updates |
| `domain:bot` | `0052CC` | Telegram bot flows, handlers, moderation/chat bot behavior |
| `domain:web` | `C2E0C6` | Web UI, guest feed HTML/JS, profile tabs, web UX |
| `domain:orders` | `E99695` | Order flow, go_online, accept_order, journal, scheduling, status transitions |

---

## 2. Layer labels

Эти labels нужны, чтобы быстро видеть, на каком слое лежит основная работа.

| Label | Color | Description |
| --- | --- | --- |
| `layer:db` | `5319E7` | Миграции, схемы БД, SQL, constraints, индексы |
| `layer:model` | `BFDADC` | ORM модели, enums, domain objects, typed entities |
| `layer:repository` | `C5DEF5` | Data access layer, repository methods, loading strategies |
| `layer:service` | `0E8A16` | Business logic, domain services, validations, orchestration |
| `layer:api` | `1D76DB` | HTTP handlers, FastAPI/API contracts, request/response behavior |
| `layer:web` | `FBCA04` | Frontend logic, HTML/JS/CSS, web interaction behavior |
| `layer:bot` | `0052CC` | Telegram bot commands, callbacks, handlers, bot UX |
| `layer:test` | `D4C5F9` | Unit, integration, smoke, regression, contract tests |
| `layer:docs` | `006B75` | README, specs, QA docs, roadmap docs, milestone docs |
| `layer:ops` | `D876E3` | Scheduler, background jobs, deployment, env, runtime infrastructure |

---

## 3. Type labels

Эта группа отвечает на вопрос: **что за работа перед нами**.

| Label | Color | Description |
| --- | --- | --- |
| `type:epic` | `000000` | Крупный продуктовый контейнер из нескольких задач |
| `type:feature` | `A2EEEF` | Новая пользовательская или платформенная возможность |
| `type:tech` | `C5DEF5` | Техническая реализация без самостоятельной продуктовой ценности |
| `type:hardening` | `F9D0C4` | Укрепление уже существующего поведения без расширения scope |
| `type:bug` | `D73A4A` | Исправление дефекта или некорректного поведения |
| `type:refactor` | `8A63D2` | Улучшение структуры кода без изменения внешнего контракта |
| `type:test` | `BFD4F2` | Задача, основной результат которой — тестовое покрытие |
| `type:docs` | `0075CA` | Задача, основной результат которой — документация |
| `type:ux` | `F9D0C4` | Навигация, microcopy, visual/interaction polish |
| `type:security` | `B60205` | Безопасность, auth, ownership, moderation-safety guardrails |

---

## 4. Priority labels

Эти labels нужны для быстрой triage-сортировки.

| Label | Color | Description |
| --- | --- | --- |
| `priority:p0` | `B60205` | Критично. Блокирует core flow, выпуск или стратегический этап |
| `priority:p1` | `D93F0B` | Очень важно. Следующий естественный приоритет после p0 |
| `priority:p2` | `FBCA04` | Важно, но не блокирует текущую волну |
| `priority:p3` | `0E8A16` | Можно отложить. Icebox / backlog / exploratory |

---

## 5. Optional status/workflow labels

Если хочется более явного workflow в GitHub, можно использовать дополнительные labels состояния.

| Label | Color | Description |
| --- | --- | --- |
| `status:ready` | `0E8A16` | Задача описана и готова к работе |
| `status:needs-spec` | `D93F0B` | Нужна дополнительная постановка или уточнение acceptance criteria |
| `status:blocked` | `B60205` | Работа заблокирована другой задачей или внешним условием |
| `status:in-review` | `5319E7` | Идёт review / validation / final check |
| `status:follow-up` | `8A63D2` | Задача является добивкой после уже завершённой работы |

---

## Suggested minimal set

Если не хочется сразу заводить большой каталог, можно начать с минимального ядра.

### Minimal domain set
- `domain:driver`
- `domain:compliance`
- `domain:feed`
- `domain:moderation`
- `domain:quality`

### Minimal layer set
- `layer:db`
- `layer:service`
- `layer:api`
- `layer:web`
- `layer:test`
- `layer:docs`

### Minimal type set
- `type:epic`
- `type:feature`
- `type:tech`
- `type:bug`
- `type:hardening`

### Minimal priority set
- `priority:p0`
- `priority:p1`
- `priority:p2`
- `priority:p3`

---

## Suggested labeling rules

### Rule 1
Каждый issue должен иметь:
- **1 milestone**
- **1 priority label**
- **1 type label**
- **минимум 1 domain label**

### Rule 2
Layer label добавляется, если он помогает маршрутизировать задачу к правильному implementation scope.

### Rule 3
Если задача реально затрагивает несколько слоёв, всё равно желательно выбрать **главный слой**, а не вешать на неё весь дождь из label-ов.

### Rule 4
Если задача междоменная, использовать максимум **2 domain labels**.

Пример:
- задача про compliance guard в order flow может иметь:
  - `domain:compliance`
  - `domain:orders`
  - `layer:service`
  - `type:tech`
  - `priority:p0`

### Rule 5
`type:epic` не должен заменять milestone.

Epic отвечает на вопрос **что объединяет задачи по смыслу**, а milestone отвечает на вопрос **в какой волне мы это делаем**.

---

## Recommended label combos

### Driver compliance backend issue
- `domain:driver`
- `domain:compliance`
- `layer:service`
- `type:tech`
- `priority:p0`

### Feed interaction feature
- `domain:feed`
- `layer:web`
- `type:feature`
- `priority:p2`

### OpenAPI sync task
- `domain:quality`
- `domain:docs`
- `layer:docs`
- `type:hardening`
- `priority:p1`

### Ownership / auth bug
- `domain:auth`
- `domain:moderation`
- `layer:api`
- `type:bug`
- `priority:p1`

### Roadmap / docs issue
- `domain:docs`
- `layer:docs`
- `type:docs`
- `priority:p2`

---

## Ready-to-create catalog

Ниже список label-ов в компактном формате `name -> color -> description`, удобный для ручного заведения в GitHub.

### Domain
- `domain:driver` -> `1D76DB` -> Driver profile, driver UX, driver operations
- `domain:compliance` -> `B60205` -> Legal/compliance, documents, eligibility, waybill
- `domain:feed` -> `5319E7` -> Feed, posts, reactions, comments, media
- `domain:moderation` -> `FBCA04` -> Moderation, review, safety, override flows
- `domain:quality` -> `0E8A16` -> Tests, contracts, release readiness
- `domain:auth` -> `D93F0B` -> Auth, ownership, permissions, CORS/write-auth
- `domain:docs` -> `006B75` -> Docs, specs, OpenAPI, roadmap
- `domain:bot` -> `0052CC` -> Telegram bot logic and bot UX
- `domain:web` -> `C2E0C6` -> Web UI and browser-side behavior
- `domain:orders` -> `E99695` -> Order flow, scheduling, lifecycle, journal

### Layer
- `layer:db` -> `5319E7` -> DB schema, migrations, SQL, constraints
- `layer:model` -> `BFDADC` -> ORM/domain models and enums
- `layer:repository` -> `C5DEF5` -> Repository/data access layer
- `layer:service` -> `0E8A16` -> Business logic and validations
- `layer:api` -> `1D76DB` -> API handlers and contracts
- `layer:web` -> `FBCA04` -> Frontend HTML/JS/CSS behavior
- `layer:bot` -> `0052CC` -> Bot handlers and callback logic
- `layer:test` -> `D4C5F9` -> Tests and regression coverage
- `layer:docs` -> `006B75` -> Documentation files and sync
- `layer:ops` -> `D876E3` -> Scheduler, jobs, deployment/runtime ops

### Type
- `type:epic` -> `000000` -> Multi-issue product container
- `type:feature` -> `A2EEEF` -> New capability
- `type:tech` -> `C5DEF5` -> Technical implementation work
- `type:hardening` -> `F9D0C4` -> Stability and integration strengthening
- `type:bug` -> `D73A4A` -> Defect fix
- `type:refactor` -> `8A63D2` -> Structural improvement without contract change
- `type:test` -> `BFD4F2` -> Test-first or coverage-focused work
- `type:docs` -> `0075CA` -> Documentation-focused work
- `type:ux` -> `F9D0C4` -> UX/copy/navigation polish
- `type:security` -> `B60205` -> Security/auth/safety related work

### Priority
- `priority:p0` -> `B60205` -> Critical, blocking core flow or release
- `priority:p1` -> `D93F0B` -> High priority, next natural focus
- `priority:p2` -> `FBCA04` -> Important but not blocking current wave
- `priority:p3` -> `0E8A16` -> Backlog / can wait / icebox

### Optional status
- `status:ready` -> `0E8A16` -> Ready for implementation
- `status:needs-spec` -> `D93F0B` -> Needs more definition
- `status:blocked` -> `B60205` -> Blocked by another task or dependency
- `status:in-review` -> `5319E7` -> Under review or validation
- `status:follow-up` -> `8A63D2` -> Follow-up to earlier completed work

---

## Note

Лучше начать с понятного и устойчивого каталога, чем с сотни label-ов, которые потом никто не помнит. Для BazarDrive оптимально держать labels как навигационные маяки, а не как новогоднюю гирлянду на весь backlog.
