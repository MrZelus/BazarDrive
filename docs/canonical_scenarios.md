# BazarDrive Canonical Scenarios

Этот документ фиксирует **канонические сценарии проекта BazarDrive**.

Его задача:
- определить основные продуктовые user journeys;
- зафиксировать их как reference-потоки;
- связать сценарии с docs, governance и operating board;
- создать основу для следующего этапа: RBAC, guards, compliance enforcement и role-aware UI.

Канонический сценарий — это не просто идея фичи, а **утверждённый опорный поток**, которому должны соответствовать:
- docs;
- UI flows;
- API contracts;
- bot behaviour;
- tests;
- permissions / RBAC / moderation rules.

---

## 1. Статусы сценариев

Рекомендуемая модель статусов:
- **Draft** — сценарий набросан, но не согласован
- **Reviewed** — сценарий обсуждён и уточнён
- **Approved** — сценарий принят как reference
- **Canonical** — сценарий закреплён как source of truth для реализации и review

На текущем этапе сценарии проекта считаются **Reviewed**, с целью довести их до **Approved / Canonical** по мере синхронизации с кодом.

---

## 2. Сводная таблица канонических сценариев

| # | Scenario | Purpose | Current status | Core roles | Related areas |
|---|---|---|---|---|---|
| 1 | Guest / Publication | Публикация контента и верификация publication profile | Reviewed | guest, moderator | feed, profile, moderation |
| 2 | Passenger / Taxi Order | Создание и просмотр заказов такси | Reviewed | passenger | taxi orders, history |
| 3 | Driver / Operations | Допуск, документы, смена, online, заказ, summary | Reviewed | driver, moderator | compliance, documents, waybill, guard |
| 4 | Moderator / Review | Проверка профилей и документов, решения approve/reject | Reviewed | moderator, admin | moderation, compliance |
| 5 | Admin / Control | Управление ролями, статусами и чувствительными действиями | Reviewed | admin | RBAC, governance, control |

---

## 3. Canonical Scenario 1: Guest / Publication

### Purpose
Определяет путь гостя от просмотра ленты до публикации контента через publication profile и moderation flow.

### Core flow
1. Пользователь открывает feed
2. Просматривает публикации
3. Создаёт publication profile
4. Отправляет profile на verification
5. Создаёт пост
6. Редактирует / удаляет пост
7. Взаимодействует с feed через реакции и комментарии
8. Пост попадает в moderation path

### Decision points
- publication profile валиден или нет?
- profile verification pending / approved / rejected?
- пост можно публиковать или нет?
- автор может редактировать пост или уже нет?
- moderator может approve/reject?

### Related docs
- `docs/contributing.md`
- `docs/operating_board.md`
- flow docs для feed / publication
- permissions / moderation docs

### Related system areas
- `public/guest_feed.html`
- `public/web/js/feed.js`
- `app/api/http_handlers.py`
- moderation flow

---

## 4. Canonical Scenario 2: Passenger / Taxi Order

### Purpose
Определяет пользовательский путь пассажира по заказу такси и просмотру собственных заказов.

### Core flow
1. Пользователь открывает приложение / bot
2. Имеет роль `passenger`
3. Создаёт заказ такси
4. Указывает: откуда / куда / время / комментарий
5. Отправляет заказ
6. Смотрит свои заказы
7. Смотрит статус и историю

### Decision points
- роль пользователя позволяет создавать заказ?
- все обязательные поля заказа заполнены?
- заказ принят / назначен / завершён / отменён?
- пассажир смотрит только свои заказы?

### Related docs
- users / roles docs
- order flow docs
- operating board

### Related system areas
- passenger UI / bot flow
- order API
- data layer для заявок / истории

---

## 5. Canonical Scenario 3: Driver / Operations

### Purpose
Это один из главных системообразующих сценариев проекта.
Определяет путь водителя от профиля и документов до operational flow.

### Core flow
1. Водитель открывает профиль
2. Заполняет compliance profile
3. Загружает документы
4. Открывает смену / путевой лист
5. Выходит online
6. Принимает заказ
7. Выполняет / завершает / отменяет заказ
8. Получает summary / reminders / score

### Decision points
- профиль заполнен достаточно или нет?
- документы обязательные / missing / expired?
- можно ли открыть смену?
- можно ли выйти online?
- можно ли принять заказ?
- нужен ли blocker reason?
- можно ли закрыть shift / waybill?

### Related docs
- `docs/security/permissions_matrix.md`
- compliance / waybill docs
- `docs/project_operating_plan.md`
- `docs/operating_board.md`

### Related system areas
- driver compliance profile
- driver documents
- waybill flow
- driver summary / reminders / score
- eligibility / guard / RBAC

---

## 6. Canonical Scenario 4: Moderator / Review

### Purpose
Определяет review-поток для профилей и документов.

### Core flow
1. Moderator получает объект на review
2. Проверяет guest publication profile или driver document
3. Принимает решение approve / reject
4. При необходимости указывает reason
5. Система фиксирует решение и обновляет состояние объекта

### Decision points
- reviewer имеет нужные права?
- какой тип объекта рассматривается?
- approve или reject?
- обязателен ли reason?
- как решение влияет на downstream flow?

### Related docs
- permissions matrix
- moderation / compliance docs
- governance / RACI

### Related system areas
- verification actions
- document review endpoints
- moderation chat / admin controls
- audit-sensitive actions

---

## 7. Canonical Scenario 5: Admin / Control

### Purpose
Определяет высокоуровневый control flow для чувствительных операций.

### Core flow
1. Admin управляет ролями
2. Admin управляет статусами пользователей
3. Admin выполняет override-sensitive actions
4. Admin следит за governance / system state

### Decision points
- операция доступна только admin или moderator тоже?
- требуется ли audit trail?
- можно ли менять роль / статус этого пользователя?
- не нарушает ли операция RBAC boundaries?

### Related docs
- permissions matrix
- operating board
- project operating plan
- governance / RACI

### Related system areas
- role management
- status management
- security / RBAC
- release / governance controls

---

## 8. Scenario-to-system mapping

| Scenario | Web | API | Bot | Data | Docs | Security |
|---|---|---|---|---|---|---|
| Guest / Publication | yes | yes | optional | yes | yes | moderation-sensitive |
| Passenger / Taxi Order | yes | yes | yes | yes | yes | role-aware |
| Driver / Operations | yes | yes | yes | yes | yes | RBAC + guard + compliance |
| Moderator / Review | yes | yes | yes | yes | yes | permission-sensitive |
| Admin / Control | limited | yes | optional | yes | yes | admin-only |

---

## 9. Как использовать эти сценарии

### Для docs
- использовать как reference flows;
- обновлять при изменении product model;
- сверять с operating docs.

### Для review
- проверять, какой canonical scenario затрагивает PR;
- не допускать изменения сценария без docs sync;
- использовать сценарии для проверки scope.

### Для RBAC / compliance
- использовать decision points как основу для permission checks и policy guards.

### Для тестов
- использовать сценарии как основу для critical-path smoke/regression coverage.

---

## 10. Связь с Operating Board и другими docs

Этот документ нужно читать вместе с:
- `docs/operating_board.md`
- `docs/project_operating_plan.md`
- `docs/security/permissions_matrix.md`
- `docs/system_health_dashboard.md`
- `docs/contributing.md`

Роль документа:
- `operating_board.md` даёт обзорную панель
- `project_operating_plan.md` даёт operating model
- `permissions_matrix.md` даёт модель прав
- `canonical_scenarios.md` даёт product/system reference flows

---

## 11. Next recommended actions

1. Довести 5 сценариев до статуса **Approved**
2. Привязать к каждому сценарию конкретные decision rules
3. Сверить сценарии с current code paths
4. Использовать сценарии как основу для RBAC foundation
5. Использовать сценарии как основу для smoke/regression prioritization

---

BazarDrive должен развиваться не как набор разрозненных функций, а как система с утверждёнными каноническими потоками. Этот документ закрепляет именно такую модель.
