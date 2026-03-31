# Driver UI Kit

Единый визуально-компонентный стандарт driver-интерфейсов BazarDrive.

## 1. Цель

Этот документ задаёт базовые правила для:
- tokens;
- buttons;
- chips;
- banners;
- cards;
- sticky actions;
- domain components;
- responsive behavior.

## 2. Scope

### Входит
- design principles;
- button system;
- status chips;
- alerts / blockers;
- progress blocks;
- domain components;
- responsive rules.

### Не входит
- backend contracts;
- state machine;
- full UX flows;
- pixel-perfect specs.

## 3. Design principles

- Один смысл = один визуальный паттерн.
- Blockers выше вторичных сигналов.
- Primary CTA показывает следующий шаг.
- Driver UI остаётся рабочим инструментом, а не декоративным экраном.

## 4. Tokens

### Color roles
- `bg`
- `surface`
- `border`
- `text-primary`
- `text-secondary`
- `accent`
- `success`
- `warning`
- `danger`
- `info`

### Typography roles
- page title
- section title
- card title
- body text
- helper text
- button text
- chip text

## 5. Button system

### Primary
Примеры:
- `Выйти на линию`
- `Подтвердить следующий этап`
- `Заполнить недостающие поля`

### Secondary
Примеры:
- `Открыть документы`
- `Перейти в профиль`
- `Заменить документ`

### Danger
Примеры:
- `Отменить заказ`
- `Закрыть путевой лист`
- `Завершить смену`

## 6. Status chips

Ключевые статусы:
- `approved`
- `checking`
- `rejected`
- `expired`
- `ready`
- `blocked`
- `online`
- `busy`

## 7. Alerts and blockers

Типы:
- info banner
- warning banner
- blocker banner
- success banner

## 8. Progress block

Состав:
- title
- progress text
- progress bar
- completed items
- missing items
- CTA

## 9. Domain components

- required fields block
- documents component
- trip sheet component
- go online eligibility component
- shift component
- active order component

## 10. Responsive rules

### Mobile
- одна колонка
- sticky CTA
- wrapped chips

### Desktop
- grid для summary/status cards
- inline CTA где это уместно

## 11. Related docs

- `docs/driver_ui_assets_index.md`
- `docs/driver_profile_components_board.md`
- `docs/driver_profile_wireframe_spec.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`

## 12. Next steps

Во второй версии стоит добавить:
- token values
- button size matrix
- chip catalog
- banner variants
- code mapping
