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
- responsive behavior;
- initial mapping to frontend components.

## 2. Scope

### Входит
- design principles;
- token roles и рекомендуемые значения;
- button system и size/state matrix;
- status chips catalog;
- alerts / blockers / success banners;
- progress blocks;
- domain components;
- state examples;
- responsive rules;
- initial code mapping.

### Не входит
- backend contracts;
- state machine переходов;
- full UX flows;
- pixel-perfect specs;
- окончательный visual handoff для production UI.

## 3. Design principles

- Один смысл = один визуальный паттерн.
- Blockers выше вторичных сигналов.
- Primary CTA показывает следующий шаг.
- Driver UI остаётся рабочим инструментом, а не декоративным экраном.
- Критическое действие не должно теряться за scroll или визуальным шумом.

## 4. Tokens

### 4.1. Color roles
| Role | Назначение | Рекомендуемое значение |
| --- | --- | --- |
| `bg` | фон приложения | `#050812` |
| `surface` | основные карточки и панели | `#121826` |
| `surface-muted` | вторичные зоны | `#1A2233` |
| `border` | обводки и разделители | `#2A3448` |
| `text-primary` | основной текст | `#F3F6FB` |
| `text-secondary` | вторичный текст | `#A8B3C7` |
| `accent` | акцентные действия | `#4F8CFF` |
| `success` | успешные статусы | `#22C55E` |
| `warning` | предупреждения | `#F59E0B` |
| `danger` | ошибки и блокеры | `#EF4444` |
| `info` | нейтральная системная подсказка | `#38BDF8` |

### 4.2. Status color mapping
| Status | Semantic role | Рекомендация |
| --- | --- | --- |
| `approved` | success | зелёный chip / badge |
| `checking` | info | голубой или нейтрально-синий chip |
| `rejected` | danger | красный chip |
| `expired` | danger | красный chip / banner |
| `expiring_soon` | warning | жёлтый chip |
| `ready` | success | зелёный статус готовности |
| `blocked` | danger | красный blocker pattern |
| `online` | success | зелёный online status |
| `busy` | info or accent | синий / accent status |
| `offline` | neutral | muted / gray status |

### 4.3. Typography roles
- page title
- section title
- card title
- body text
- helper text
- button text
- chip text
- caption / meta text

### 4.4. Spacing scale
Базовая шкала:
- 4
- 8
- 12
- 16
- 24
- 32

### 4.5. Radius and elevation
| Element | Recommendation |
| --- | --- |
| Card radius | 16 |
| Button radius | 12 |
| Chip radius | 9999 / pill |
| Banner radius | 12 |
| Card shadow | минимальная или отсутствует, упор на контраст поверхностей |

## 5. Button system

### 5.1. Primary
Примеры:
- `Выйти на линию`
- `Подтвердить следующий этап`
- `Заполнить недостающие поля`

Назначение:
- одно главное действие текущего шага;
- не больше одного visually dominant CTA в одной рабочей зоне.

### 5.2. Secondary
Примеры:
- `Открыть документы`
- `Перейти в профиль`
- `Заменить документ`

Назначение:
- важное, но не главное действие;
- переход к соседнему сценарию или исправлению.

### 5.3. Tertiary / link action
Примеры:
- `Подробнее`
- `Открыть историю`
- `Открыть документ`

Назначение:
- вспомогательное действие с низкой визуальной доминантой.

### 5.4. Danger
Примеры:
- `Отменить заказ`
- `Закрыть путевой лист`
- `Завершить смену`

Назначение:
- деструктивные действия;
- при необходимости дополняются confirm-step.

### 5.5. Button size matrix
| Size | Height | Use case |
| --- | --- | --- |
| `sm` | 32-36 px | inline actions в списках и карточках |
| `md` | 40-44 px | стандартные кнопки в cards и forms |
| `lg` | 48-52 px | главные CTA, sticky action bar |

### 5.6. Button states
| State | Behavior |
| --- | --- |
| `default` | обычный активный вид |
| `disabled` | неактивна, действие недоступно |
| `loading` | повторный submit заблокирован |
| `pressed` | краткая обратная связь на tap/click |

## 6. Status chips

### 6.1. Status chip catalog
| Chip | Meaning | Typical usage |
| --- | --- | --- |
| `approved` | подтверждено | документы |
| `checking` | на проверке | документы / verification |
| `rejected` | отклонено | документы / verification |
| `expired` | истекло | документы / ОСАГО / разрешения |
| `ready` | готово | eligibility / profile readiness |
| `blocked` | заблокировано | eligibility / profile status |
| `online` | на линии | shift status |
| `busy` | занят | shift / active order |
| `offline` | офлайн | shift status |

### 6.2. Rules
- chip должен быть коротким;
- статус не должен зависеть только от цвета;
- одинаковый статус должен выглядеть одинаково во всех экранах.

## 7. Alerts and blockers

### 7.1. Banner types
| Type | Когда использовать | Dismissible |
| --- | --- | --- |
| info banner | системная подсказка | обычно да |
| warning banner | есть проблема, но сценарий не всегда полностью заблокирован | иногда |
| blocker banner | сценарий остановлен | нет |
| success banner | требования выполнены / действие успешно завершено | обычно да |

### 7.2. Banner content pattern
- title
- short body
- optional CTA
- optional icon

### 7.3. Banner examples
- `Нельзя выйти на линию` -> blocker banner
- `Документ скоро истекает` -> warning banner
- `Путевой лист открыт` -> success banner
- `Профиль почти готов` -> info banner

## 8. Progress block

### 8.1. Composition
- title
- progress text
- progress bar
- completed items
- missing items
- CTA

### 8.2. Usage
- обязательные поля;
- документы;
- readiness / eligibility blocks.

### 8.3. States
- empty
- partial
- complete
- blocked if completion is mandatory for next step

## 9. Card types

| Card type | Purpose |
| --- | --- |
| status card | краткое состояние сущности |
| checklist card | список требований или readiness items |
| entity card | документ, заказ, авто |
| summary card | дашборд / обзор |

## 10. Sticky actions

Использовать когда:
- есть одно главное действие;
- экран длинный;
- CTA нельзя терять при скролле.

Примеры:
- `Выйти на линию`
- `Заполнить недостающие поля`
- `Подтвердить следующий этап`

Rules:
- на mobile sticky action bar допустим;
- на desktop предпочтителен inline CTA, если экран короткий;
- sticky CTA не должен конкурировать сразу с двумя равнозначными primary actions.

## 11. Domain components

### 11.1. Required fields block
Состав:
- progress
- filled chips
- missing chips
- warning block
- CTA `Заполнить недостающие поля`

Состояния:
- empty
- partial
- complete

### 11.2. Documents component
Состав:
- documents progress
- status chips
- warning / rejected / expired handling
- CTA `Добавить / заменить документ`

Состояния:
- empty
- checking
- approved
- has_rejected_docs
- has_expired_docs

### 11.3. Trip sheet component
Состав:
- trip sheet status
- shift period
- warning if missing
- CTA `Открыть / закрыть путевой лист`

Состояния:
- missing
- open
- requires_closing
- closed

### 11.4. Go online eligibility component
Состав:
- eligibility status
- checklist
- blocker / success state
- CTA `Выйти на линию` / `Исправить блокеры`

Состояния:
- not_ready
- partially_ready
- ready
- blocked

### 11.5. Shift component
Состав:
- shift status
- readiness checklist
- timeline / recent events
- CTA `Выйти на линию` / `Завершить смену`

Состояния:
- offline
- ready
- online
- busy
- ending
- closed

### 11.6. Active order component
Состав:
- order status
- route block
- passenger note
- CTA `Следующий этап`
- CTA `Связаться` / `Отменить`

Состояния:
- accepted
- arriving
- ontrip
- done
- canceled

## 12. State examples

### Documents component
- `approved`: все критичные документы валидны
- `has_rejected_docs`: есть хотя бы один документ, требующий замены
- `has_expired_docs`: есть просроченный документ, влияющий на допуск

### Eligibility component
- `ready`: все обязательные условия выполнены
- `blocked`: есть стоп-фактор для выхода на линию

### Shift component
- `ready`: водитель ещё не онлайн, но допуск уже пройден
- `busy`: есть активный заказ или рабочее состояние занятости

## 13. Responsive rules

### Mobile
- одна колонка
- sticky CTA
- wrapped chips
- secondary actions могут сворачиваться

### Tablet
- допускаются двухколоночные summary layouts
- secondary cards могут идти рядом

### Desktop
- grid для summary/status cards
- inline CTA где это уместно
- больше расстояние между секциями

## 14. Code mapping

| UI concept | Suggested frontend component |
| --- | --- |
| Status chip | `DriverStatusChip` |
| Warning banner | `DriverWarningBanner` |
| Progress block | `DriverProgressBlock` |
| Eligibility card | `DriverEligibilityCard` |
| Sticky action bar | `DriverStickyActionBar` |
| Shift card | `DriverShiftCard` |
| Active order card | `DriverActiveOrderCard` |

## 15. Related docs

- `docs/driver_ui_assets_index.md`
- `docs/driver_profile_components_board.md`
- `docs/driver_profile_wireframe_spec.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_figjam_links.md`

## 16. Next steps

Следующей итерацией стоит добавить:
- concrete token usage by component;
- button do/don't examples;
- real screenshots or Figma component refs;
- mapping to actual frontend files;
- a11y checklist per component.

## 17. Summary of recent changes

В данной итерации интерфейса были произведены следующие изменения:

- **Тема по умолчанию стала тёмной.** Все цветовые CSS-токены (`--feed-bg-rgb`, `--feed-panel-rgb` и т. д.) теперь определяются тёмными значениями из раздела 4.1 документа. Светлая палитра доступна как override через селектор `:root[data-theme="light"]`, что упрощает переключение между темами без ручной замены классов.
- **Обновлена Tailwind-конфигурация.** Цветовые токены теперь считываются из CSS-переменных с помощью `rgb(var(--token))`, благодаря чему один utility-класс корректно работает и в тёмной, и в светлой палитре.
- **Добавлен механизм выбора темы в `feed.js`.** Поддерживается query-параметр `?theme=dark|light`, сохранение выбора в `localStorage`, fallback на `prefers-color-scheme` и применение темы через атрибут `data-theme` на корневом элементе.
- **Переписан guardrail-тест.** Теперь он отдельно валидирует контраст и разделение поверхностей для тёмной и светлой палитр.
- **Проведено тестирование.** Все изменения проходят тест `tests/test_guest_feed_theme_contrast_guardrails.py`. В текущей среде недоступен инструмент создания браузерных скриншотов, поэтому UI-изменения не приложены.
