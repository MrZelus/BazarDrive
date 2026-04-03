# Driver UI Assets Index — QA-ready Rewrite

## Purpose

Этот документ — QA-ready версия индекса driver UI assets для **BazarDrive**.

Он нужен не только как каталог ссылок, но и как **контрольный реестр артефактов**, который помогает:
- понимать, какие UX-материалы актуальны;
- отличать exploratory assets от source-of-truth артефактов;
- видеть, какие сценарии покрыты, а какие ещё нет;
- связывать driver UX assets с implementation, QA и roadmap.

---

## How to use this document

### Product / UX
Использовать как карту текущих driver UX artifacts и как список пробелов, которые нужно закрыть для согласованной product/UX модели.

### Frontend / Web
Использовать как справочник по экранам, состояниям, CTA и компонентным связям, но проверять maturity/status каждого asset перед реализацией.

### Telegram bot
Использовать только те части, которые явно отмечены как:
- `telegram`
- `shared`

Если asset отмечен как `web-only`, не переносить логику в бот автоматически.

### Backend / API
Использовать как reference для блокеров, статусов, readiness logic, order flow transitions и compliance-related behavior, но проверять status contract и permissions contract отдельно.

### QA
Использовать как:
- реестр артефактов;
- источник для test design;
- карту coverage gaps;
- список зон, где нельзя считать asset production-ready без дополнительной валидации.

---

## Asset status legend

### Platform
- `shared` — используется как общий концепт для Telegram + Web
- `web` — primarily web-oriented
- `telegram` — primarily Telegram-oriented
- `mixed` — оба канала участвуют, но behavior может отличаться

### Maturity
- `exploratory` — ранняя схема/идея, не source of truth
- `draft` — полезно для проектирования, но требует согласования
- `reviewed` — прошёл review и годится как рабочий reference
- `qa-ready` — можно использовать как основу для test design
- `implementation-ready` — можно использовать как source-of-truth для реализации

### Truth level
- `index` — навигационный документ
- `reference` — полезный supporting doc
- `source-of-truth` — основной артефакт для данного слоя
- `needs-sync` — использовать с осторожностью, пока не синхронизирован с docs/contracts/tests

---

## Asset registry

| Asset | Type | Platform | Maturity | Truth level | Main use | QA use | Current risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Общая схема сценариев водителя | FigJam scenario map | shared | draft | reference | Вход в domain map водителя | High-level scenario coverage | Может расходиться с implementation details |
| Сценарий заказа глазами водителя | FigJam order flow | mixed | draft | reference | Order lifecycle и driver actions | Основа для order-flow tests | Нужна синхронизация с status contract |
| Карта меню водителя Telegram / Web | FigJam navigation map | mixed | draft | reference | Навигация и разделы | Menu/navigation QA | Риск platform drift |
| Master UX map водителя | FigJam master map | shared | reviewed | reference | Общий маршрут driver journey | Regression overview | Может быть слишком абстрактной для screen-level QA |
| Карта экранов для сценариев водителя | Screen map | mixed | reviewed | reference | Screen inventory | Screen coverage mapping | Нужны implementation links |
| Driver Screens Wireframe Set | Wireframes | web | draft | reference | Базовые web-screen layouts | UI-flow QA reference | Не отмечен как canonical |
| Driver Mobile Low-Fi Wireframes | Mobile low-fi | web | draft | reference | Mobile version и плотность экранов | Mobile UX checks | Может не совпадать с final responsive rules |
| Driver Screen Copy and CTA Map | UI copy map | shared | draft | needs-sync | CTA/status/helper texts | Copy/state validation | Нужна sync с real UI and error states |
| Driver Profile Components Board | Components board | shared | reviewed | reference | Domain components and required blocks | Component coverage | Нужна связка с real component ownership |
| Driver UI Kit | Doc / component rules | web | reviewed | source-of-truth | Tokens, chips, cards, alerts, sticky actions | UI consistency QA | Нужно поддерживать sync с implementation |

---

## Main assets and links

## 1. Upper-level driver UX maps

### 1.1. Общая схема сценариев водителя
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/cfcf4915-e2b4-4879-b97a-275a7f1323f8?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=7ebfff2c-c220-4eb7-b73a-167b608cca7e
- Platform: `shared`
- Maturity: `draft`
- Truth level: `reference`
- Что покрывает:
  - вход водителя;
  - профиль и валидацию;
  - авто и документы;
  - путевой лист;
  - выход на линию;
  - статусы заказа;
  - завершение или продолжение смены.
- QA note:
  - использовать для high-level scenario decomposition, но не как единственный source of truth для screen-by-screen acceptance.

### 1.2. Сценарий заказа глазами водителя
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/0cddb327-a5b4-4fd5-98b2-97139460c0e0?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=3f45ad89-fa29-46fb-bc1d-dec1a2e28d8e
- Platform: `mixed`
- Maturity: `draft`
- Truth level: `reference`
- Что покрывает:
  - ожидание заказа;
  - карточку заказа;
  - принятие / отказ;
  - `ACCEPTED -> ARRIVING -> ONTRIP -> DONE`;
  - ветку `CANCELED`;
  - scheduled order.
- QA note:
  - использовать для order-flow scenario coverage;
  - не считать status contract завершённым без отдельного status doc.

### 1.3. Карта меню водителя Telegram / Web
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/b801b515-d8de-4af1-9230-089e9593c6e9?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=f934d580-dca8-4ffb-912e-e204fb9efea3
- Platform: `mixed`
- Maturity: `draft`
- Truth level: `reference`
- Что покрывает:
  - разделы Telegram;
  - разделы Web;
  - профиль, авто, документы, путевой лист, смену;
  - активный заказ;
  - историю и выплаты.
- QA note:
  - использовать для navigation sanity checks;
  - platform-specific behavior нужно валидировать отдельно.

### 1.4. Master UX map водителя
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/2fbcb169-f76b-463d-abfb-817ad68773f0?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=efc01466-7a7e-45a8-8b26-a9c54e92a9b0
- Platform: `shared`
- Maturity: `reviewed`
- Truth level: `reference`
- Что покрывает:
  - Telegram + Web как единый маршрут;
  - подготовку водителя к работе;
  - выход на линию;
  - заказ;
  - завершение смены;
  - историю и выплаты.
- QA note:
  - использовать как обзорную regression map;
  - не заменяет screen-level acceptance artifacts.

---

## 2. Screen inventory

### 2.1. Карта экранов для сценариев водителя
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/398bd002-5d52-4c23-a80f-e2e971e062e4?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=6e6c1f89-f055-476a-9734-268b927e29e9
- Platform: `mixed`
- Maturity: `reviewed`
- Truth level: `reference`
- Что покрывает:
  - вход / идентификацию;
  - выбор роли;
  - профиль;
  - авто;
  - документы;
  - путевой лист;
  - обзор / dashboard;
  - смену;
  - карточку нового заказа;
  - активный заказ;
  - завершение смены;
  - историю;
  - выплаты.
- QA note:
  - хороший starting point для screen coverage matrix;
  - не хватает explicit links to implementation status and test suites.

---

## 3. Wireframes

### 3.1. Driver Screens Wireframe Set
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/df3a31e3-6f09-406a-85e8-4f55994ec148?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=d716b431-56fb-41d7-84c9-51625c94f2cd
- Platform: `web`
- Maturity: `draft`
- Truth level: `reference`
- Что покрывает:
  - Driver Dashboard;
  - Driver Documents;
  - Active Order;
  - Shift Screen;
  - Blockers Screen.
- QA note:
  - использовать для screen expectations and state coverage;
  - не считать implementation-ready без подтверждения актуальности.

### 3.2. Driver Mobile Low-Fi Wireframes
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/28c31653-c3ff-4bf1-83ef-d6f292c5d072?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=a98a15d2-5691-4513-8f7a-1463792fe3e8
- Platform: `web`
- Maturity: `draft`
- Truth level: `reference`
- Что покрывает:
  - Dashboard Mobile;
  - Documents Mobile;
  - Active Order Mobile;
  - Shift Mobile;
  - Blockers Mobile.
- QA note:
  - полезно для responsive/mobile review;
  - не заменяет final responsive acceptance rules.

---

## 4. UI copy and CTA

### 4.1. Driver Screen Copy and CTA Map
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/25e4e3aa-a977-435f-9f11-4adf70b41736?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=8d550593-7cb6-4e22-a171-59f2ed1863e0
- Platform: `shared`
- Maturity: `draft`
- Truth level: `needs-sync`
- Что покрывает:
  - заголовки экранов;
  - подзаголовки;
  - статусы;
  - primary CTA;
  - secondary CTA;
  - danger CTA;
  - helper text.
- QA note:
  - полезно для copy review и CTA consistency;
  - нельзя считать canonical, пока не синхронизировано с actual UI states и backend errors.

---

## 5. Components board

### 5.1. Driver Profile Components Board
- Link:
  - https://www.figma.com/online-whiteboard/create-diagram/e00b8008-7aa8-41ca-b47f-5f14e7efed05?utm_source=chatgpt&utm_content=edit_in_figjam&oai_id=v1%2Ft6MzRfJf6HllgdA2vRF9DPvCrECBiZdQDQUJNqWEbsPiu8mB4z1LHy&request_id=0e5ed398-97a0-460f-b55a-7fb1b7f0fab6
- Platform: `shared`
- Maturity: `reviewed`
- Truth level: `reference`
- Что покрывает:
  - обязательные поля;
  - документы;
  - путевой лист;
  - допуск к выходу на линию;
  - активный заказ;
  - смену.
- QA note:
  - использовать как domain-component inventory;
  - нужен отдельный mapping к implementation components/owners.

---

## 6. UI kit

### 6.1. Driver UI Kit
- Doc:
  - `docs/driver_ui_kit.md`
- Platform: `web`
- Maturity: `reviewed`
- Truth level: `source-of-truth`
- Что покрывает:
  - design principles;
  - tokens;
  - buttons;
  - status chips;
  - alerts / blockers;
  - cards;
  - sticky actions;
  - domain components;
  - responsive rules.
- QA note:
  - использовать как основной styling/reference doc для consistency checks.

---

## Recommended reading order

1. Общая схема сценариев водителя
2. Master UX map водителя
3. Сценарий заказа глазами водителя
4. Карта меню водителя Telegram / Web
5. Карта экранов для сценариев водителя
6. Driver Screens Wireframe Set
7. Driver Mobile Low-Fi Wireframes
8. Driver Screen Copy and CTA Map
9. Driver Profile Components Board
10. Driver UI Kit

---

## QA usage guide

### Use for smoke / regression planning
Использовать в первую очередь:
- Master UX map водителя
- Сценарий заказа глазами водителя
- Карта экранов для сценариев водителя
- Driver UI Kit

### Use for screen expectations
Использовать:
- Driver Screens Wireframe Set
- Driver Mobile Low-Fi Wireframes
- Driver Profile Components Board

### Use with caution
Использовать как supporting reference, но не как final truth:
- Driver Screen Copy and CTA Map
- Карта меню водителя Telegram / Web
- Общая схема сценариев водителя

### Do not assume
Не предполагать автоматически, что:
- любой `shared` asset описывает одинаковое поведение для Telegram и Web;
- любой wireframe уже implementation-ready;
- copy/CTA map синхронизирован с backend error contract.

---

## Coverage matrix

| Area | Coverage status | Main asset | QA confidence |
| --- | --- | --- | --- |
| Driver onboarding | partial | Общая схема сценариев водителя / Карта экранов | medium |
| Driver profile | covered | Карта экранов / Components Board | medium |
| Vehicle profile | partial | Карта экранов / Components Board | low-medium |
| Documents | covered | Driver Documents / Components Board / UI Kit | medium |
| Waybill | partial | Общая схема / Components Board | low-medium |
| Shift lifecycle | partial | Shift Screen / Master UX map | medium |
| Active order | covered | Order flow / Active Order wireframes | medium |
| Blockers / readiness | covered | Blockers Screen / Summary logic references | medium |
| History | partial | Карта экранов / Master UX map | low |
| Payouts | partial | Карта меню / Карта экранов | low |
| Notifications | missing | n/a | low |
| Permissions / role restrictions | missing | n/a | low |
| Status contract | missing | n/a | low |
| Error states / backend-driven failure cases | partial | CTA map / Blockers assets | low-medium |
| Offline / degraded network UX | missing | n/a | low |

---

## Main gaps to close next

### Required for stronger QA confidence
- `docs/driver_notifications_matrix.md`
- `docs/driver_permissions_matrix.md`
- `docs/driver_status_contract.md`

### Strongly recommended after that
- implementation status map for driver screens
- test suite mapping: asset -> test file / QA checklist
- ownership registry: who updates which artifact
- stable Figma workspace link migration

---

## Related documents

- `docs/driver_figjam_links.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_onboarding_flow.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_menu_map.md`
- `docs/driver_profile_wireframe_spec.md`
- `docs/driver_profile_components_board.md`
- `docs/driver_ui_kit.md`
- `docs/issues/driver-ux-docs-epic.md`

---

## Stable-link migration note

Текущие ссылки ведут на FigJam-артефакты, созданные через ChatGPT/Figma integration. До переноса в постоянное рабочее пространство Figma:
- считать ссылки рабочими, но нестабильными;
- не использовать их как единственный долгосрочный reference;
- при переносе обновить этот индекс и пометить migrated assets отдельно.

---

## QA verdict

Текущий набор driver UI assets уже полезен как навигационный слой, но ещё не даёт полного production-grade coverage для QA без дополнительных contracts/matrices.

Практически это означает:
- использовать индекс как working map;
- не считать его единственным source of truth;
- обязательно дополнять status/permissions/notifications contracts перед финальным QA sign-off крупных driver flows.
