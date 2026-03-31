# Driver Permissions Matrix

Единая матрица прав для driver domain в BazarDrive.

Документ нужен как source of truth для:
- backend authorization;
- frontend gating;
- Telegram bot action availability;
- QA сценариев доступа;
- разграничения действий между driver, system и moderator/admin.

---

## 1. Scope

В документ входят:
- actor roles;
- домены действий;
- разрешённые и запрещённые действия;
- условия допуска;
- backend enforcement notes.

В документ не входят:
- notification rules;
- визуальные UI rules;
- HTTP endpoint schemas.

---

## 2. Actors

### 2.1. Driver
Основной пользователь с ролью `driver`.

### 2.2. System
Backend / scheduled jobs / автоматические проверки / derived transitions.

### 2.3. Moderator/Admin
Оператор, support, внутренний админский контур или доверенный staff actor.

### 2.4. Backend API
Не отдельный бизнес-actor, а технический enforcement layer, который обязан проверять права независимо от UI.

---

## 3. Общие правила

### 3.1. Backend is final authority
Даже если UI показал кнопку, backend обязан заново проверить право на действие.

### 3.2. Visibility != permission
Если экран или раздел виден, это ещё не значит, что действие разрешено.

### 3.3. Role + state + ownership
Право определяется не только actor role, но и:
- текущим статусом сущности;
- ownership;
- eligibility / blockers;
- cross-domain invariants.

### 3.4. Forbidden by default for invalid state
Если действие не описано как разрешённое, backend должен считать его запрещённым.

---

## 4. Permission legend

| Symbol | Meaning |
| --- | --- |
| `ALLOW` | действие разрешено |
| `ALLOW_IF` | разрешено только при выполнении условий |
| `DENY` | действие запрещено |
| `SYSTEM_ONLY` | выполняется только системой/backend |
| `ADMIN_ONLY` | доступно только moderator/admin |

---

## 5. Driver profile permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Create own profile | ALLOW | DENY | ADMIN_ONLY | только для самого себя |
| Edit own draft/incomplete profile | ALLOW | DENY | ADMIN_ONLY | ownership required |
| Submit profile for verification | ALLOW_IF | DENY | ADMIN_ONLY | required fields satisfied |
| Approve profile | DENY | SYSTEM_ONLY | ADMIN_ONLY | moderation/verification flow |
| Reject profile | DENY | SYSTEM_ONLY | ADMIN_ONLY | moderation/verification flow |
| Block profile | DENY | SYSTEM_ONLY | ADMIN_ONLY | policy / compliance reason |
| Unblock profile | DENY | DENY | ADMIN_ONLY | corrective/admin flow |
| View own profile | ALLOW | ALLOW | ADMIN_ONLY | ownership or admin scope |
| View another driver profile | DENY | DENY | ADMIN_ONLY | unless explicit staff tooling |

### Backend notes
- Driver может менять только свой профиль.
- Driver не может сам поставить себе `approved` / `blocked`.
- `profile_status` transition должен валидироваться по `driver_status_contract.md`.

---

## 6. Vehicle permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Add own vehicle | ALLOW | DENY | ADMIN_ONLY | ownership required |
| Edit own vehicle | ALLOW_IF | DENY | ADMIN_ONLY | no forbidden active-state conflict |
| Remove own vehicle | ALLOW_IF | DENY | ADMIN_ONLY | no active shift/order conflict |
| Mark vehicle verified | DENY | SYSTEM_ONLY | ADMIN_ONLY | compliance flow |
| Mark vehicle invalid | DENY | SYSTEM_ONLY | ADMIN_ONLY | compliance/policy flow |
| View own vehicle | ALLOW | ALLOW | ADMIN_ONLY | ownership required |

### Backend notes
- Нельзя silently заменить vehicle так, чтобы обходить eligibility.
- При активной смене или активном заказе edit/remove vehicle обычно требует deny или deferred flow.

---

## 7. Driver documents permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Upload document | ALLOW | DENY | ADMIN_ONLY | ownership required |
| Replace rejected/expired document | ALLOW | DENY | ADMIN_ONLY | ownership required |
| Delete uploaded document | ALLOW_IF | DENY | ADMIN_ONLY | only if allowed by business rules and no locked review state |
| Move document to checking | DENY | SYSTEM_ONLY | ADMIN_ONLY | triggered by review flow |
| Approve document | DENY | SYSTEM_ONLY | ADMIN_ONLY | moderation/verification flow |
| Reject document | DENY | SYSTEM_ONLY | ADMIN_ONLY | moderation/verification flow |
| Expire document | DENY | SYSTEM_ONLY | ADMIN_ONLY | date-driven or admin correction |
| View own documents | ALLOW | ALLOW | ADMIN_ONLY | ownership required |

### Backend notes
- Driver never sets final review status directly.
- `document_status` transitions must follow canonical contract.
- Delete of document in `checking` may be denied to preserve review consistency.

---

## 8. Trip sheet permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Open trip sheet | ALLOW_IF | DENY | ADMIN_ONLY | driver eligible for opening workday sheet |
| Edit open trip sheet data | ALLOW_IF | DENY | ADMIN_ONLY | only while sheet is mutable |
| Mark trip sheet requires closing | DENY | SYSTEM_ONLY | ADMIN_ONLY | usually triggered by shift end |
| Close trip sheet | ALLOW_IF | DENY | ADMIN_ONLY | required closing data present |
| Force close trip sheet | DENY | SYSTEM_ONLY | ADMIN_ONLY | exceptional/admin flow |
| View own trip sheet | ALLOW | ALLOW | ADMIN_ONLY | ownership required |

### Backend notes
- Driver не должен перепрыгивать `missing -> closed`.
- Если trip sheet обязателен, без `open` нельзя позволять `go_online`.

---

## 9. Eligibility permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Read eligibility status | ALLOW | ALLOW | ADMIN_ONLY | own scope or admin scope |
| Override eligibility to ready | DENY | DENY | ADMIN_ONLY | exceptional manual override only if policy allows |
| Compute eligibility | DENY | SYSTEM_ONLY | ADMIN_ONLY | derived backend computation |
| Override hard block | DENY | DENY | ADMIN_ONLY | admin-only, auditable |

### Backend notes
- `eligibility_status` should be computed, not manually client-controlled.
- Любой override должен быть редким, auditable and explicit.

---

## 10. Shift permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| Move shift `offline -> ready` | DENY | SYSTEM_ONLY | ADMIN_ONLY | computed after eligibility success |
| Go online (`ready -> online`) | ALLOW_IF | DENY | ADMIN_ONLY | eligibility_status == ready |
| Accept workload and become busy | DENY | SYSTEM_ONLY | ADMIN_ONLY | tied to accepted order |
| Return `busy -> online` | DENY | SYSTEM_ONLY | ADMIN_ONLY | active order completed/canceled |
| Start ending shift | ALLOW_IF | DENY | ADMIN_ONLY | no blocking unfinished work or handled by ending flow |
| Close shift | ALLOW_IF | SYSTEM_ONLY | ADMIN_ONLY | all required close conditions satisfied |
| Force close shift | DENY | SYSTEM_ONLY | ADMIN_ONLY | exceptional/admin/system cleanup |
| View own shift state | ALLOW | ALLOW | ADMIN_ONLY | ownership required |

### Backend notes
- Driver может инициировать `go_online` и `end_shift`, но backend делает финальную state validation.
- Некоторые shift transitions practically system-driven after order updates.

---

## 11. Order permissions

| Action | Driver | System | Moderator/Admin | Conditions |
| --- | --- | --- | --- | --- |
| View available order | ALLOW_IF | ALLOW | ADMIN_ONLY | driver online and allowed to receive offers |
| Accept order | ALLOW_IF | DENY | ADMIN_ONLY | order is open and driver eligible |
| Move `accepted -> arriving` | ALLOW_IF | DENY | ADMIN_ONLY | accepted by same driver |
| Move `arriving -> ontrip` | ALLOW_IF | DENY | ADMIN_ONLY | accepted by same driver |
| Move `ontrip -> done` | ALLOW_IF | DENY | ADMIN_ONLY | accepted by same driver |
| Cancel order before acceptance | DENY | SYSTEM_ONLY | ADMIN_ONLY | depends on who owns cancel flow |
| Cancel accepted/active order | ALLOW_IF | SYSTEM_ONLY | ADMIN_ONLY | emergency/business rules only |
| Reassign order | DENY | SYSTEM_ONLY | ADMIN_ONLY | support/dispatch/system flow |
| View own active order | ALLOW | ALLOW | ADMIN_ONLY | assigned driver only |
| View чужой active order in detail | DENY | DENY | ADMIN_ONLY | staff tooling only |

### Backend notes
- Driver can only mutate orders assigned to self.
- `order_status` transitions must follow canonical contract.
- Cancel flows should validate policy, reason code and possible audit trail.

---

## 12. Cross-domain permission rules

### 12.1. Driver cannot bypass readiness
Driver не может напрямую сделать:
- `offline -> online`
- `profile -> approved`
- `document -> approved`
- `eligibility -> ready`

если это противоречит backend checks.

### 12.2. Busy restrictions
Если shift/order state indicates active work:
- remove vehicle = usually DENY
- destructive profile mutations = usually DENY
- some document deletions = usually DENY

### 12.3. Blocked profile restrictions
При `profile_status == blocked`:
- go_online = DENY
- accept order = DENY
- privileged work actions = DENY
- viewing own data usually remains ALLOW

### 12.4. Ownership restrictions
Driver может управлять только:
- своим профилем
- своими документами
- своим путевым листом
- своей сменой
- своим назначенным заказом

---

## 13. Backend enforcement recommendations

Backend должен:
- проверять actor role;
- проверять ownership;
- проверять current entity status;
- проверять cross-domain blockers;
- возвращать доменную ошибку instead of silent failure.

Примеры ошибок:
- `permission_denied`
- `ownership_required`
- `driver_not_eligible`
- `profile_blocked`
- `active_shift_conflict`
- `active_order_conflict`
- `admin_override_required`

---

## 14. Telegram / Frontend guidance

Frontend и Telegram bot могут:
- скрывать недоступные действия;
- дизейблить CTA;
- показывать helper text;
- показывать blocker reasons.

Но они не могут считаться final authority по permissions.

---

## 15. Related docs

- `docs/driver_status_contract.md`
- `docs/driver_master_ux_map.md`
- `docs/driver_order_flow.md`
- `docs/driver_shift_flow.md`
- `docs/driver_ui_kit.md`
- `docs/driver_notifications_matrix.md` (planned)

---

## 16. Next steps

После фиксации этой матрицы логично добавить:
- `docs/driver_notifications_matrix.md`
- mapping permissions to endpoint groups
- audit log policy for admin overrides
- error code table for permission failures
