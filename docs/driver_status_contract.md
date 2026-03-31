# Driver Status Contract

Единый контракт статусов driver domain для BazarDrive.

Документ нужен как source of truth для:
- backend state machine;
- frontend state rendering;
- Telegram bot flows;
- QA test cases;
- валидации допустимых переходов.

---

## 1. Scope

В документ входят:
- profile statuses;
- document statuses;
- trip sheet statuses;
- eligibility statuses;
- shift statuses;
- order statuses;
- allowed transitions;
- forbidden transitions;
- stored vs derived state rules.

В документ не входят:
- permissions matrix;
- notification delivery rules;
- endpoint-level API contract.

---

## 2. Общие правила

### 2.1. Canonical naming
- В БД и backend использовать canonical snake_case статусы.
- Во frontend и Telegram допускаются человекочитаемые labels, но не новые статусы.
- Один доменный смысл = один canonical status.

### 2.2. Stored vs derived
- В БД хранить только устойчивые доменные статусы.
- Derived statuses вычислять на backend из набора фактов, а не дублировать в нескольких местах.
- Если derived status критичен для UI, его можно отдавать в API response как computed field.

### 2.3. Transition ownership
- Переходы статусов валидирует backend.
- Frontend и Telegram bot только инициируют действие.
- Backend не должен принимать недопустимый переход даже если UI его случайно отправил.

---

## 3. Profile status contract

### 3.1. Canonical statuses
- `draft`
- `incomplete`
- `pending_verification`
- `approved`
- `rejected`
- `blocked`

### 3.2. Meaning
| Status | Meaning |
| --- | --- |
| `draft` | профиль создан, но почти не заполнен |
| `incomplete` | профиль частично заполнен, но не готов к верификации |
| `pending_verification` | профиль отправлен или ожидает проверки |
| `approved` | профиль подтверждён и может участвовать в рабочем сценарии при выполнении других условий |
| `rejected` | профиль отклонён, требуется исправление |
| `blocked` | профиль заблокирован и не может участвовать в работе |

### 3.3. Allowed transitions
- `draft -> incomplete`
- `incomplete -> pending_verification`
- `pending_verification -> approved`
- `pending_verification -> rejected`
- `rejected -> incomplete`
- `approved -> blocked`
- `blocked -> incomplete`

### 3.4. Forbidden transitions
- `draft -> approved`
- `draft -> blocked`
- `approved -> draft`
- `approved -> pending_verification` without explicit re-verification flow
- `blocked -> approved` without corrective flow

### 3.5. Stored or derived
- `profile_status` хранится в БД.
- `profile_readiness` может быть derived field.

---

## 4. Document status contract

### 4.1. Canonical statuses
- `missing`
- `uploaded`
- `checking`
- `approved`
- `rejected`
- `expired`

### 4.2. Meaning
| Status | Meaning |
| --- | --- |
| `missing` | документ отсутствует |
| `uploaded` | файл загружен, но проверка ещё не стартовала или не подтверждена |
| `checking` | документ находится на проверке |
| `approved` | документ подтверждён |
| `rejected` | документ отклонён |
| `expired` | документ истёк и требует обновления |

### 4.3. Allowed transitions
- `missing -> uploaded`
- `uploaded -> checking`
- `uploaded -> approved` only if auto-approval exists
- `checking -> approved`
- `checking -> rejected`
- `approved -> expired`
- `rejected -> uploaded`
- `expired -> uploaded`

### 4.4. Forbidden transitions
- `missing -> approved` without upload record
- `approved -> checking` without re-review flow
- `expired -> approved` without re-upload or revalidation
- `rejected -> approved` without new validation flow

### 4.5. Stored or derived
- `document_status` хранится в БД.
- `document_is_valid_for_work` может быть derived boolean.

---

## 5. Trip sheet status contract

### 5.1. Canonical statuses
- `missing`
- `open`
- `requires_closing`
- `closed`

### 5.2. Meaning
| Status | Meaning |
| --- | --- |
| `missing` | путевой лист не создан или не открыт |
| `open` | путевой лист открыт и действует для текущей смены |
| `requires_closing` | смена завершена, но путевой лист ещё не закрыт |
| `closed` | путевой лист закрыт |

### 5.3. Allowed transitions
- `missing -> open`
- `open -> requires_closing`
- `requires_closing -> closed`
- `closed -> open` only for new workday/new sheet

### 5.4. Forbidden transitions
- `missing -> closed`
- `open -> closed` if closure flow requires explicit end data first
- `closed -> requires_closing`

### 5.5. Stored or derived
- `trip_sheet_status` хранится в БД.
- `trip_sheet_required_for_shift` обычно derived rule based on business config.

---

## 6. Eligibility status contract

### 6.1. Canonical statuses
- `not_ready`
- `partially_ready`
- `ready`
- `blocked`

### 6.2. Meaning
| Status | Meaning |
| --- | --- |
| `not_ready` | обязательные условия в целом не выполнены |
| `partially_ready` | часть условий выполнена, но выйти на линию ещё нельзя |
| `ready` | все обязательные условия выполнены |
| `blocked` | есть стоп-фактор, который делает выход на линию невозможным |

### 6.3. Source of truth
Eligibility не должна быть главным persisted статусом, если её можно вычислить из:
- profile status;
- vehicle readiness;
- required documents validity;
- trip sheet status;
- hard blockers.

### 6.4. Derived rules
Пример вычисления:
- если `profile_status != approved` -> не `ready`
- если есть обязательный документ в `missing/rejected/expired` -> не `ready`
- если путевой лист обязателен и не `open` -> не `ready`
- если есть hard block -> `blocked`
- если все условия выполнены -> `ready`

### 6.5. Recommendation
- В API отдавать `eligibility_status` как computed field.
- В БД хранить snapshot только если это нужно для аналитики / аудита.

---

## 7. Shift status contract

### 7.1. Canonical statuses
- `offline`
- `ready`
- `online`
- `busy`
- `ending`
- `closed`

### 7.2. Meaning
| Status | Meaning |
| --- | --- |
| `offline` | водитель вне рабочей смены |
| `ready` | все условия выполнены, можно выходить на линию |
| `online` | водитель на линии и ждёт заказ |
| `busy` | водитель находится в активном рабочем сценарии заказа |
| `ending` | инициировано завершение смены, но есть незавершённые шаги |
| `closed` | смена закрыта |

### 7.3. Allowed transitions
- `offline -> ready`
- `ready -> online`
- `online -> busy`
- `busy -> online`
- `online -> ending`
- `ending -> closed`
- `closed -> ready` only as a new shift cycle

### 7.4. Forbidden transitions
- `offline -> online` without readiness check
- `ready -> busy` without accepted order
- `busy -> closed` if active order still exists
- `closed -> online` directly

### 7.5. Stored or derived
- `shift_status` хранится в БД.
- `can_go_online` может быть derived boolean from eligibility.

---

## 8. Order status contract

### 8.1. Canonical statuses
- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### 8.2. Meaning
| Status | Meaning |
| --- | --- |
| `created` | заказ создан и ещё не принят водителем |
| `accepted` | водитель принял заказ |
| `arriving` | водитель едет к пассажиру |
| `ontrip` | поездка началась |
| `done` | поездка завершена |
| `canceled` | заказ отменён |

### 8.3. Allowed transitions
- `created -> accepted`
- `accepted -> arriving`
- `arriving -> ontrip`
- `ontrip -> done`
- `created -> canceled`
- `accepted -> canceled`
- `arriving -> canceled`
- `ontrip -> canceled` only if business rules allow emergency cancel

### 8.4. Forbidden transitions
- `created -> ontrip`
- `created -> done`
- `accepted -> done`
- `done -> canceled`
- `canceled -> accepted`
- `done -> accepted`

### 8.5. Stored or derived
- `order_status` хранится в БД.
- `next_allowed_actions` лучше отдавать как derived API field.

---

## 9. Cross-domain invariants

### 9.1. Shift and order
- При `order_status in {accepted, arriving, ontrip}` shift не должен быть `offline` или `closed`.
- При активном заказе shift обычно должен быть `busy`.

### 9.2. Eligibility and shift
- Переход `ready -> online` возможен только если `eligibility_status == ready`.
- При `eligibility_status == blocked` shift не должен перейти в `online`.

### 9.3. Profile and eligibility
- `profile_status != approved` исключает `eligibility_status == ready`.

### 9.4. Documents and eligibility
- Обязательный документ в `missing`, `rejected` или `expired` исключает `eligibility_status == ready`.

### 9.5. Trip sheet and eligibility
- Если путевой лист обязателен, `trip_sheet_status != open` исключает `eligibility_status == ready`.

---

## 10. API recommendations

Backend response для driver domain желательно строить так:
- persisted statuses:
  - `profile_status`
  - `document_status`
  - `trip_sheet_status`
  - `shift_status`
  - `order_status`
- computed fields:
  - `eligibility_status`
  - `profile_readiness`
  - `document_is_valid_for_work`
  - `can_go_online`
  - `next_allowed_actions`

---

## 11. Validation rules for backend

Backend должен:
- валидировать every transition against canonical contract;
- логировать недопустимые transition attempts;
- возвращать понятную доменную ошибку на invalid transition;
- не доверять status transitions, предложенным клиентом без server-side проверки.

Примеры ошибок:
- `invalid_shift_transition`
- `invalid_order_transition`
- `eligibility_blocked`
- `required_document_missing`
- `trip_sheet_required`

---

## 12. Related docs

- `docs/driver_master_ux_map.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_profile_components_board.md`
- `docs/driver_ui_kit.md`
- `docs/driver_permissions_matrix.md` (planned)
- `docs/driver_notifications_matrix.md` (planned)

---

## 13. Next steps

После фиксации этого документа логично добавить:
- `docs/driver_permissions_matrix.md`
- `docs/driver_notifications_matrix.md`
- backend enum mapping в коде
- таблицу API error codes для invalid transitions
