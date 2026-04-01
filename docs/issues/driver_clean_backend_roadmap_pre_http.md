# Driver Clean Backend Roadmap Before HTTP

Этот документ фиксирует **цельную дорожную карту “чистого backend”** для driver domain перед выходом в HTTP wiring.

Идея простая:

**до HTTP backend должен стать единым источником смысла, а не смесью canonical и legacy интерпретаций.**

---

## 1. North Star

К моменту перехода в HTTP backend должен уметь делать одно хорошо:

- брать persisted факты
- превращать их в canonical backend meaning
- отдавать устойчивые service-level результаты

То есть правильная цепочка должна выглядеть так:

**persisted facts -> backend interpretation -> canonical service result -> HTTP payload**

А не так:

**persisted facts -> HTTP improvisation -> UI guesses**

---

## 2. Цель дорожной карты

Перед HTTP очистить backend от тех мест, где ещё живут:

- legacy status values
- смешение runtime status и canonical status
- дублирующиеся источники истины
- размытая интерпретация waybill/trip-sheet semantics

Итоговое состояние:

- backend services согласованы друг с другом
- operation layer не противоречит canonical contract
- trip-sheet truth идёт из одного backend source
- HTTP становится mechanical translation layer, а не местом принятия бизнес-решений

---

## 3. Принципы “чистого backend”

### 3.1. Canonical language first

Все service-level outward semantics должны говорить на canonical языке:

- `order_status`
- `shift_status`
- `trip_sheet_status`
- `error.code`
- `event_name`

### 3.2. One source of meaning per concept

На каждый смысл должен быть один главный backend source:

- current order meaning
- trip-sheet meaning
- readiness meaning
- permission meaning

### 3.3. Legacy may exist, but must be contained

Legacy значения могут временно существовать в persistence/history, но:

- не должны течь наружу как canonical truth
- не должны дублироваться в нескольких слоях
- должны либо cleanup-иться, либо централизованно адаптироваться

### 3.4. HTTP must not invent semantics

HTTP later can:

- normalise
- package
- expose

Но не должен:

- сам решать, что означает `assigned`
- сам склеивать `completed` и `done`
- сам вычислять `trip_sheet_status` из сырых waybill fields по кускам

---

## 4. Что уже cleaned enough

На текущем этапе уже достаточно хорошо очищены:

### 4.1. Contract direction

Зафиксированы:

- canonical status ladders
- canonical event direction
- canonical error field direction
- expected HTTP language

### 4.2. Non-blocking services

Service-layer re-check already suggests:

- `driver_status_service.py` is largely aligned
- `driver_permissions_service.py` is largely aligned
- `driver_notifications_service.py` is aligned enough

### 4.3. Scope discipline

Также уже cleaned enough:

- frontend не тащится в ту же волну
- giant schema redesign не мешается в pre-HTTP stage
- HTTP рассматривается как integration step, not research step

---

## 5. Что ещё нужно очистить

## Stage A. Stabilize `driver_operation_service.py`

Это первый и самый прямой remaining blocker.

### Почему

Этот файл пока всё ещё смешивает:

- legacy runtime/persistence semantics
- canonical outward semantics

### Что очистить

#### A1. `completed -> done`

Нужно завершить status alignment так, чтобы:

- новые completion writes не использовали `completed`
- outward completion response не использовал `completed`
- canonical `order_status = done` не конфликтовал с runtime `status`

#### A2. Resolve outward `status` semantics

Нужно решить и зафиксировать правило:

- outward `status` не должен противоречить canonical `order_status`
- если canonical field уже есть, runtime field не должен жить своей жизнью

#### A3. Contain `assigned`

До финального semantic decision:

- `assigned` не должен течь наружу как молчаливый canonical current state
- он должен быть либо internal marker, либо cleanup candidate, либо explicitly expanded contract later

### Критерий завершения Stage A

- `driver_operation_service.py` больше не создаёт явный status drift
- file-level outward responses совместимы с будущим HTTP contract

---

## Stage B. Stabilize one backend source for `trip_sheet_status`

Это второй remaining blocker.

### Почему

Сейчас persisted reality по waybill живёт в `driver_documents`, а наружу нужен уже canonical trip-sheet смысл.

Без одного backend source later layers начнут по-разному интерпретировать:

- missing waybill
- open waybill
- closed waybill
- close-required state

### Что очистить

#### B1. One backend place only

Должно быть одно backend place, которое отвечает за:

- waybill facts in
- canonical `trip_sheet_status` out

#### B2. Explicit mapping

Нужно явно определить backend rules для:

- `missing`
- `open`
- `closed`
- `requires_closing`

#### B3. No UI reconstruction

Frontend later must not reconstruct trip-sheet semantics from raw persisted fields.

### Критерий завершения Stage B

- backend already has one stable source for `trip_sheet_status`
- waybill meaning is no longer scattered across layers

---

## Stage C. Final backend re-check

После Stage A и Stage B нужен короткий контрольный re-check.

### Проверить

- `driver_status_service.py`
- `driver_permissions_service.py`
- `driver_notifications_service.py`
- stabilized `driver_operation_service.py`
- the chosen `trip_sheet_status` backend source

### Что хотим подтвердить

- no service leaks unresolved legacy semantics
- no service depends on an ambiguous interpretation to produce future HTTP truth
- backend now has a clean enough canonical path for HTTP adapters

### Критерий завершения Stage C

- service-layer verdict becomes effectively GO

---

## Stage D. Only then transition to HTTP

Когда backend clean enough, только тогда:

1. apply HTTP wiring
2. activate API contract tests
3. inspect failures as actual contract problems, not backend fog
4. only after that move to frontend gating

---

## 6. Stop signs on this roadmap

До HTTP нельзя считать backend clean enough, если:

- `driver_operation_service.py` still says two different truths at once
- `assigned` still leaks outward ambiguously
- `trip_sheet_status` still has no single backend source
- legacy persistence values can still escape into canonical payload meaning uncontrolled

---

## 7. Green-light rule

“Зелёный свет” на HTTP появляется, когда одновременно true:

- Stage A done
- Stage B done
- Stage C confirms no major service-level contradictions remain

И тогда архитектурно это означает:

- backend knows the truth
- HTTP only transports and shapes it
- UI only renders it

---

## 8. Practical roadmap in one list

### Step 1
Stabilize `driver_operation_service.py`

### Step 2
Stabilize one backend source for `trip_sheet_status`

### Step 3
Do final backend services re-check

### Step 4
Move into HTTP wiring

### Step 5
Activate API contract tests

### Step 6
Only then move toward frontend gating

---

## 9. One-line summary

**A clean backend before HTTP means: one canonical language, one backend source of meaning per concept, and no unresolved legacy semantics leaking into outward service results.**
