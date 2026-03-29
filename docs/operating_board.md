# BazarDrive Operating Board

Этот документ — **главная обзорная панель проекта BazarDrive**.

Его цель: собрать в одном месте ключевые слои управления проектом:
- lifecycle изменений;
- governance и ownership;
- RACI-подход;
- core system domains;
- roles и permissions;
- quality и delivery discipline;
- next actions / roadmap.

Operating Board нужен для того, чтобы проект развивался как **единая управляемая система**, а не как набор разрозненных задач.

---

## 1. Зачем нужен Operating Board

BazarDrive уже содержит несколько важных слоёв:
- web;
- API;
- Telegram bot;
- data layer;
- docs;
- permissions / RBAC;
- moderation / compliance;
- tests;
- PR / release process.

Проблема роста любого проекта в том, что без общей панели управления эти слои начинают жить отдельно.

Operating Board решает это за счёт одной общей картины:
- что меняется;
- где это отражается;
- кто за это отвечает;
- как это проходит путь до merge;
- какие проверки не дают системе расползтись.

---

## 2. Главные секции Operating Board

### A. Operating Lifecycle
Верхний слой: как изменения входят в систему.

Поток:

`Idea / Problem -> Issue / Epic -> PR / Review -> Merge / Release`

Смысл:
- любая идея должна материализоваться в issue;
- issue должно иметь scope;
- изменения должны проходить review;
- merge должен обновлять состояние системы, а не только код.

### B. Governance / Docs
Левый слой: правила и управляющие артефакты.

Сюда входят:
- `docs/contributing.md`
- `docs/security/permissions_matrix.md`
- governance map
- RACI map
- `docs/project_operating_plan.md`
- `README.md`
- `docs/openapi.yaml`
- flow docs / architecture docs

Смысл:
- docs не вспомогательны, а управляющи;
- они определяют контракты, ответственность и правила развития проекта.

### C. System Core
Центральный слой: основная техническая система проекта.

Сюда входят:
- Web UI
- HTTP API
- Telegram Bot
- Data Layer / DB / Migrations

Смысл:
- это ядро BazarDrive;
- все product flows должны проходить через согласованные точки между этими четырьмя частями.

### D. Roles / Operations
Правый слой: роли и операционные домены.

Сюда входят:
- guest
- passenger
- driver
- moderator
- admin
- compliance / moderation
- RBAC / security

Смысл:
- система должна быть role-aware;
- права, ограничения и процессы допуска должны быть явными.

### E. Quality / Delivery
Нижний слой: как проект проверяется и доставляется.

Сюда входят:
- tests / smoke / regression
- PR template
- docs sync
- scope guardrails
- roadmap / next actions

Смысл:
- именно этот слой удерживает качество;
- он не даёт в main попадать несвязным или неописанным изменениям.

---

## 3. Operating principle

Главный operating principle проекта:

> Изменение считается завершённым только тогда, когда согласованы docs, code, roles, tests и delivery path.

Это означает:
- недостаточно просто изменить код;
- нужно понимать влияние на роли, docs, API/bot flows и проверку;
- merge должен обновлять систему целиком, а не отдельный слой.

---

## 4. Как читать эту панель

### Сверху вниз
- идея входит в lifecycle;
- проходит через issue;
- влияет на docs/governance;
- реализуется в core system;
- проверяется quality layer;
- уходит в PR и merge.

### Слева направо
- правила и docs определяют рамки;
- ядро системы реализует поведение;
- role/operations слой определяет who/what/why;
- delivery слой проверяет готовность.

---

## 5. Что должно обновляться при изменениях

### Если меняется role model
Обновить:
- permissions matrix;
- RBAC-related docs;
- bot/API restrictions;
- role flows;
- tests.

### Если меняется compliance flow
Обновить:
- docs по compliance;
- moderation/compliance схемы;
- API endpoints / services;
- bot status / reminders / guard logic;
- tests.

### Если меняется frontend flow
Обновить:
- UX docs / flow docs;
- contributing / scope notes, если затрагиваются process expectations;
- smoke/regression checks.

### Если меняется API contract
Обновить:
- `docs/openapi.yaml`;
- связанные docs;
- bot/web интеграцию;
- tests.

---

## 6. Ownership summary

Operating Board опирается на несколько ownership-зон:

- Product / Scope owner
- UX / Docs owner
- API / Service owner
- Bot owner
- Data / Migration owner
- Security / RBAC owner
- Moderation / Compliance owner
- QA / Test owner
- Release / Merge owner

Задача этой панели не заменить ownership, а сделать его прозрачным.

---

## 7. RACI summary

В упрощённом виде:

- Docs / Contributing / OpenAPI
  - A: Product / Scope
  - R: UX / Docs

- Web UI
  - A: Product / Scope
  - R: UX / Docs

- API / Services
  - A: Product / Scope
  - R: API / Services

- Telegram Bot
  - A: Product / Scope
  - R: Bot owner

- Data / Migrations
  - A/R: Data owner

- RBAC / Security
  - A/R: Security owner

- Compliance / Moderation
  - A/R: Moderation / Compliance owner

- Tests / QA
  - A/R: QA owner

- PR / Release
  - A/R: Release owner

---

## 8. Board-driven review checklist

Перед merge полезно проверять change-set по этой панели:

### Lifecycle
- Есть ли issue / epic?
- Понятен ли scope?
- Не смешаны ли unrelated изменения?

### Docs / Governance
- Обновлены ли docs?
- Не устарела ли permissions / governance информация?
- Нужно ли обновлять схемы?

### Core system
- Какие слои реально затронуты: web / API / bot / data?
- Нет ли расхождения между ними?

### Roles / Operations
- Меняются ли права?
- Меняется ли moderation / compliance / guard поведение?
- Есть ли влияние на guest / passenger / driver / moderator / admin?

### Quality / Delivery
- Есть ли smoke-check?
- Есть ли regression risk?
- Достаточно ли понятен PR?

---

## 9. What “healthy project state” means

Operating Board помогает удерживать проект в healthy state.

Признаки healthy state:
- docs отражают реальную систему;
- роли и permissions не размыты;
- bot и API не дублируют бизнес-логику вразнобой;
- PR не тащат лишний scope;
- lifecycle прозрачен;
- ownership понятен;
- merge обновляет не только код, но и картину проекта.

---

## 10. Связанные артефакты

### Документы
- `README.md`
- `docs/contributing.md`
- `docs/project_operating_plan.md`
- `docs/security/permissions_matrix.md`
- `docs/openapi.yaml`
- role / flow docs

### Визуальные карты
- architecture maps
- system map
- lifecycle map
- governance map
- RACI map
- operating board

---

## 11. Recommended usage

Использовать этот документ:
- при планировании Epic-ов;
- при review больших PR;
- при синхронизации docs и code;
- при разборе конфликтов scope;
- как обзорную панель для развития проекта.

---

## 12. Next actions

1. Держать `docs/contributing.md` актуальным
2. Утвердить PR template как обязательный минимум
3. Синхронизировать operating board с governance / lifecycle / RACI
4. Обновлять board при изменении roles, permissions, compliance или delivery model
5. Использовать board как источник истины для high-level project control

---

BazarDrive должен развиваться как продуктовая система, а не как случайная последовательность задач. Operating Board фиксирует именно эту модель развития.
