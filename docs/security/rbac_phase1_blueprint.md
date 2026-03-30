# BazarDrive RBAC Phase 1 Blueprint

Этот документ переводит канонические сценарии проекта в **первый рабочий слой RBAC enforcement**.

Его задача:
- зафиксировать canonical roles и permissions;
- определить первые enforcement points;
- связать RBAC с реальными сценариями BazarDrive;
- не смешивать RBAC с full identity redesign;
- дать безопасный implementation plan для Phase 1.

---

## 1. Что такое RBAC Phase 1

Phase 1 — это **security foundation**, а не полный redesign доступа.

В рамки Phase 1 входит:
- единый список ролей;
- единый список permissions;
- centralized authorization helpers;
- первые enforcement points в самых чувствительных сценариях;
- сохранение текущего driver eligibility / compliance layer.

В Phase 1 **не входит**:
- полный пересмотр identity model;
- тотальная интеграция во все endpoints и все bot handlers;
- замена existing compliance/policy logic;
- сложные ACL per-resource.

---

## 2. Canonical roles

Для проекта закрепляются роли:
- `guest`
- `passenger`
- `driver`
- `moderator`
- `admin`

### Notes
- `moderator` не равен `admin`
- `driver` не получает moderation rights
- `passenger` не получает driver/compliance rights
- `admin` остаётся самым широким уровнем доступа

---

## 3. Canonical permissions (Phase 1)

Минимальный набор разрешений для старта:
- `feed.moderate`
- `publication_profile.review`
- `driver_document.review`
- `driver.go_online`
- `driver.accept_order`
- `driver.shift.open`
- `driver_document.upload`
- `taxi_order.create`
- `user.role.manage`

Этого достаточно, чтобы закрыть самые рискованные decision points без преждевременной перегрузки модели.

---

## 4. RBAC vs Policy / Guard

Для BazarDrive одного RBAC недостаточно.

Нужна двухступенчатая модель:

### Layer 1. RBAC
Отвечает на вопрос:
- может ли эта роль делать такой тип действия вообще?

### Layer 2. Policy / Guard / Eligibility
Отвечает на вопрос:
- можно ли это делать **сейчас** в данном контексте?

Пример:
- роль `driver` может иметь permission `driver.accept_order`
- но policy может запретить действие, если:
  - нет допуска;
  - не открыт waybill;
  - документы просрочены;
  - compliance blocked.

Phase 1 не заменяет policy/guard, а ставит **RBAC перед policy**.

---

## 5. Scenario-to-permission mapping

### 5.1 Guest / Publication

| Decision point | Role(s) | Permission | Guard / policy | Notes |
|---|---|---|---|---|
| Submit publication profile | guest, admin | `publication_profile.submit` (future) | profile valid | Permission можно formalize позже |
| Create post | guest, admin | `feed.post.create` (future) | profile ready / payload valid | В Phase 1 можно оставить как doc-level mapping |
| Approve/reject publication profile | moderator, admin | `publication_profile.review` or `feed.moderate` | object exists | **Phase 1 enforcement point** |

### 5.2 Passenger / Taxi Order

| Decision point | Role(s) | Permission | Guard / policy | Notes |
|---|---|---|---|---|
| Create taxi order | passenger, admin | `taxi_order.create` | payload valid | Model fixed now, enforcement can deepen later |
| View own orders | passenger, admin | `taxi_order.view_own` (future) | ownership | Better suited for Phase 2 |

### 5.3 Driver / Operations

| Decision point | Role(s) | Permission | Guard / policy | Notes |
|---|---|---|---|---|
| Manage driver profile | driver, admin | `driver_profile.manage` (future) | profile exists | Can formalize later |
| Upload documents | driver, admin | `driver_document.upload` | payload valid | Candidate for later extension |
| Open shift / waybill | driver, admin | `driver.shift.open` | no active shift conflict | Candidate for Phase 2 |
| Go online | driver, admin | `driver.go_online` | eligibility / compliance / waybill | **Phase 1 enforcement point** |
| Accept order | driver, admin | `driver.accept_order` | eligibility / compliance / order constraints | **Phase 1 enforcement point** |

### 5.4 Moderator / Review

| Decision point | Role(s) | Permission | Guard / policy | Notes |
|---|---|---|---|---|
| Review guest profile | moderator, admin | `publication_profile.review` or `feed.moderate` | object exists | **Phase 1 enforcement point** |
| Review driver document | moderator, admin | `driver_document.review` | object exists | **Phase 1 enforcement point** |
| Reject with reason | moderator, admin | same as above | reason handling policy | reason policy remains outside RBAC |

### 5.5 Admin / Control

| Decision point | Role(s) | Permission | Guard / policy | Notes |
|---|---|---|---|---|
| Change user role | admin | `user.role.manage` | audit / target validation | Define now, enforce when endpoint exists |
| Change user status | admin | `user.status.manage` (future) | audit / target validation | Phase 2+ |
| Override sensitive action | admin | `system.override` (future) | explicit audit | Phase 2+ |

---

## 6. First enforcement points for code

Phase 1 intentionally starts with **4 critical integration points**.

### Enforcement point 1
**Guest profile approve/reject**

Current idea:
- replace ad hoc moderator check with centralized permission check

Target permission:
- `publication_profile.review` or `feed.moderate`

### Enforcement point 2
**Driver document approve/reject**

Target permission:
- `driver_document.review`

### Enforcement point 3
**Driver go-online**

Target permission:
- `driver.go_online`

Important:
- RBAC check happens first
- existing driver eligibility/compliance logic remains the policy layer

### Enforcement point 4
**Driver accept-order**

Target permission:
- `driver.accept_order`

Again:
- RBAC first
- policy/guard second

---

## 7. Proposed file structure

Recommended first implementation structure:

```text
app/security/
    roles.py
    permissions.py
    authorization.py
    exceptions.py
```

### `roles.py`
- canonical roles enum
- normalize helper

### `permissions.py`
- permission enum
- role → permission mapping

### `authorization.py`
- `has_role()`
- `has_permission()`
- `require_role()`
- `require_permission()`

### `exceptions.py`
- `AuthorizationDenied`
- `PermissionDenied`
- `PolicyDenied`

---

## 8. Integration order

### Step 1. Introduce security foundation
Create security files and make them importable.

### Step 2. Add transport-role to domain-role bridge
Current transport auth is not yet a full domain identity model.
A bridge layer must translate current request auth context into project roles.

### Step 3. Apply permission checks to 4 enforcement points
Do not rewrite all endpoints at once.

### Step 4. Keep compliance/eligibility logic intact
Current `DriverOperationService` / guard logic remains the second layer.

### Step 5. Update docs
At minimum:
- `docs/security/permissions_matrix.md`
- optional short note in `docs/canonical_scenarios.md`

---

## 9. Reason codes model

RBAC denials should be machine-readable.

Recommended codes:
- `permission_denied`
- `role_not_allowed`
- `moderator_required`
- `admin_required`
- `compliance_not_ready`
- `waybill_not_open`
- `document_expired`

Why this matters:
- API responses become consistent
- bot can reuse same signals
- UI can show precise reasons
- dashboard-auto can classify failures

---

## 10. Definition of success for Phase 1

Phase 1 is successful if:
- canonical roles are defined in code
- canonical permissions are defined in code
- authorization helpers exist
- 4 critical enforcement points use centralized permission checks
- existing driver eligibility remains intact
- permissions docs are updated

Phase 1 is **not** required to solve all authorization in the project.
It is the first controlled step.

---

## 11. Recommended next phase after Phase 1

### Phase 2
- integrate same authorization layer into Telegram bot
- extend permissions for passenger and publication actions
- add shift/open and document upload enforcement points
- improve domain role resolution

### Phase 3
- explicit policy layer extraction
- UI denial hints
- audit logging for sensitive admin/moderation actions

---

## 12. Related documents

- `docs/canonical_scenarios.md`
- `docs/security/permissions_matrix.md`
- `docs/project_operating_plan.md`
- `docs/operating_board.md`
- `docs/system_health_dashboard.md`

---

BazarDrive RBAC should grow from canonical scenarios and real decision points, not from isolated enums. This blueprint fixes that direction for Phase 1.
