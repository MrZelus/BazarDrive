# Epic: Driver UX Docs

## Цель

После `docs/driver_onboarding_flow.md` зафиксировать остальную водительскую систему так, чтобы frontend, backend, Telegram bot и QA работали по единой карте.

## Outcome

В репозитории появляется цельный набор driver-документации:
- смена;
- заказ;
- меню Telegram / Web;
- permissions;
- status contract.

---

## Issue 1: Docs: описать жизненный цикл смены водителя

### Зачем
После сценария входа водителя нужно зафиксировать, как водитель:
- проходит проверку допуска;
- выходит на линию;
- работает в смене;
- завершает смену;
- взаимодействует с путевым листом и активным заказом.

### Scope
- [ ] Описать состояния смены:
  - `offline`
  - `blocked`
  - `ready`
  - `online`
  - `busy`
  - `ending`
  - `closed`
- [ ] Описать preconditions для открытия смены
- [ ] Зафиксировать блокеры выхода на линию
- [ ] Описать связь смены с путевым листом
- [ ] Описать связь смены с активным заказом
- [ ] Добавить основные edge cases
- [ ] Сослаться на связанные docs и FigJam

### Acceptance criteria
- Есть файл `docs/driver_shift_flow.md`
- Документ отделяет shift lifecycle от onboarding и order flow
- В документе есть состояния, preconditions, blockers, transitions, edge cases
- Термины согласованы с existing driver docs

### Related docs
- `docs/driver_onboarding_flow.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_figjam_links.md`

---

## Issue 2: Docs: описать сценарий заказа глазами водителя

### Зачем
После допуска к работе нужен отдельный документ, описывающий:
- ожидание заказа;
- получение карточки заказа;
- принятие / пропуск;
- переходы по статусам;
- отмену;
- scheduled order.

### Scope
- [ ] Описать preconditions начала order flow
- [ ] Описать шаги:
  - ожидание заказа
  - получение карточки
  - принятие / отказ
  - `ACCEPTED`
  - `ARRIVING`
  - `ONTRIP`
  - `DONE`
  - `CANCELED`
- [ ] Отдельно описать scheduled order
- [ ] Зафиксировать допустимые и недопустимые переходы
- [ ] Добавить ветку отмены
- [ ] Добавить edge cases и UX requirements

### Acceptance criteria
- Есть файл `docs/driver_order_flow.md`
- В документе есть state machine заказа
- Документ покрывает обычный и scheduled order
- Статусы и переходы пригодны для frontend/backend sync

### Related docs
- `docs/driver_shift_flow.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_onboarding_flow.md`

---

## Issue 3: Docs: описать карту меню водителя для Telegram и Web

### Зачем
Нужно зафиксировать, как driver UX раскладывается по двум интерфейсам:
- Telegram для быстрых действий;
- Web для расширенного управления.

### Scope
- [ ] Описать верхнеуровневые разделы Telegram
- [ ] Описать верхнеуровневые разделы Web
- [ ] Зафиксировать назначение каждого раздела:
  - профиль
  - авто
  - документы
  - путевой лист
  - смена
  - активный заказ
  - история
  - выплаты
  - поддержка / настройки
- [ ] Описать роль Web overview
- [ ] Описать cross-links и deep-link transitions
- [ ] Добавить navigation rules и edge cases

### Acceptance criteria
- Есть файл `docs/driver_menu_map.md`
- Разделы Telegram и Web согласованы
- Переходы к blocker flows и active order описаны явно
- Документ ссылается на master map и FigJam

### Related docs
- `docs/driver_master_ux_map.md`
- `docs/driver_profile_wireframe_spec.md`
- `docs/driver_figjam_links.md`

---

## Issue 4: Docs: зафиксировать permissions matrix для driver domain

### Зачем
После описания onboarding / shift / order flow нужно явно определить:
- кто что может делать;
- какие действия доступны до и после верификации;
- где действуют backend restrictions;
- чем отличаются driver, moderator, admin и system rules.

### Scope
- [ ] Описать роли:
  - driver
  - moderator
  - admin
  - system
- [ ] Зафиксировать права на:
  - профиль
  - авто
  - документы
  - путевой лист
  - открытие смены
  - принятие заказа
  - смену статусов заказа
  - отмену заказа
  - просмотр истории
  - выплаты
- [ ] Выделить pre-verification / post-verification restrictions
- [ ] Отдельно отметить backend-only validations и forbidden actions

### Acceptance criteria
- Есть файл `docs/driver_permissions_matrix.md`
- Для каждого action указан actor и restriction
- Матрица согласована с driver flows
- Документ пригоден для QA и backend validation

### Related docs
- `docs/driver_onboarding_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_order_flow.md`

---

## Issue 5: Docs: зафиксировать единый status contract для driver flows

### Зачем
Нужен единый документ, который синхронизирует:
- profile statuses;
- document statuses;
- shift statuses;
- order statuses.

### Scope
- [ ] Описать profile statuses
- [ ] Описать document statuses
- [ ] Описать shift statuses
- [ ] Описать order statuses
- [ ] Зафиксировать допустимые transitions
- [ ] Зафиксировать forbidden transitions
- [ ] Добавить glossary / naming rules
- [ ] Отметить source of truth поля и доменные ограничения

### Acceptance criteria
- Есть файл `docs/driver_status_contract.md`
- Все ключевые driver статусы собраны в одном месте
- Допустимые переходы описаны явно
- Документ может использоваться как reference для frontend/backend/QA

### Related docs
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_onboarding_flow.md`

---

## Issue 6: Docs: связать driver UX docs через README и внутренние cross-links

### Зачем
После добавления набора driver docs нужно сделать их читаемыми как систему, а не как набор разрозненных файлов.

### Scope
- [ ] Обновить `README.md` с блоком `Driver UX docs`
- [ ] Проверить cross-links между:
  - `driver_master_ux_map.md`
  - `driver_onboarding_flow.md`
  - `driver_shift_flow.md`
  - `driver_order_flow.md`
  - `driver_menu_map.md`
  - `driver_permissions_matrix.md`
  - `driver_status_contract.md`
- [ ] Проверить ссылки на FigJam
- [ ] Убедиться, что порядок чтения понятен новому участнику проекта

### Acceptance criteria
- README содержит актуальный индекс driver docs
- Все driver docs ссылаются друг на друга
- Нет orphan docs без входной точки

---

## Рекомендуемый порядок реализации

1. `driver_shift_flow.md`
2. `driver_order_flow.md`
3. `driver_menu_map.md`
4. `driver_status_contract.md`
5. `driver_permissions_matrix.md`
6. README + cross-links
