# Driver UI Kit v2 Draft

Этот документ расширяет `docs/driver_ui_kit.md` и фиксирует содержательное наполнение для версии v2.

## 1. Что добавляет v2

По сравнению с v1, здесь появляются:
- concrete token values;
- button size matrix;
- status chip catalog;
- banner variants;
- domain component state examples;
- initial frontend code mapping.

## 2. Token values

### 2.1. Color roles
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
| `info` | системная подсказка | `#38BDF8` |

### 2.2. Radius and spacing
| Element | Recommendation |
| --- | --- |
| Card radius | 16 |
| Button radius | 12 |
| Chip radius | pill |
| Banner radius | 12 |

Базовая шкала spacing:
- 4
- 8
- 12
- 16
- 24
- 32

## 3. Button matrix

| Type | Use case | Size |
| --- | --- | --- |
| Primary | главное действие шага | `md` / `lg` |
| Secondary | важное вторичное действие | `md` |
| Tertiary | вспомогательное действие | `sm` / link |
| Danger | деструктивное действие | `md` |

### States
- `default`
- `disabled`
- `loading`
- `pressed`

## 4. Status chip catalog

| Chip | Meaning | Usage |
| --- | --- | --- |
| `approved` | подтверждено | документы |
| `checking` | на проверке | документы / verification |
| `rejected` | отклонено | документы |
| `expired` | истекло | документы / разрешения |
| `ready` | готово | eligibility |
| `blocked` | заблокировано | eligibility / profile |
| `online` | на линии | shift |
| `busy` | занят | shift / active order |
| `offline` | офлайн | shift |

## 5. Banner variants

| Type | When to use | Dismissible |
| --- | --- | --- |
| info banner | системная подсказка | обычно да |
| warning banner | есть проблема, но сценарий не всегда остановлен | иногда |
| blocker banner | ключевой сценарий остановлен | нет |
| success banner | действие выполнено / всё готово | обычно да |

Примеры:
- `Нельзя выйти на линию` -> blocker
- `Документ скоро истекает` -> warning
- `Путевой лист открыт` -> success

## 6. Domain component states

### Required fields block
- empty
- partial
- complete

### Documents component
- empty
- checking
- approved
- has_rejected_docs
- has_expired_docs

### Trip sheet component
- missing
- open
- requires_closing
- closed

### Eligibility component
- not_ready
- partially_ready
- ready
- blocked

### Shift component
- offline
- ready
- online
- busy
- ending
- closed

### Active order component
- accepted
- arriving
- ontrip
- done
- canceled

## 7. Frontend mapping draft

| UI concept | Suggested frontend component |
| --- | --- |
| Status chip | `DriverStatusChip` |
| Warning banner | `DriverWarningBanner` |
| Progress block | `DriverProgressBlock` |
| Eligibility card | `DriverEligibilityCard` |
| Sticky action bar | `DriverStickyActionBar` |
| Shift card | `DriverShiftCard` |
| Active order card | `DriverActiveOrderCard` |

## 8. Recommended merge path

После согласования этот draft нужно:
1. влить содержательно в `docs/driver_ui_kit.md`;
2. удалить `docs/driver_ui_kit_v2_draft.md`;
3. обновить README и `docs/driver_ui_assets_index.md` только если изменится позиционирование документа.
