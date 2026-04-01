# Driver `assigned` Semantics and Rollout Plan

Этот документ фиксирует следующий узкий шаг после `completed -> done`:

**разобрать семантику legacy runtime/journal value `assigned` и решить, это canonical order status, internal event, или transitional compatibility artifact.**

---

## 1. Почему это следующий узел

После `completed -> done` самым заметным статусным вопросом остаётся `assigned`.

Это более спорный случай, чем `completed`, потому что здесь неочевидно совпадение смыслов:

- canonical order contract использует `created`, `accepted`, `arriving`, `ontrip`, `done`, `canceled`;
- runtime/journal слой использует `assigned`, `accepted`, `completed`, `canceled`.

Если `completed -> done` почти прямой rename, то `assigned` может означать:

- open order before acceptance;
- internal dispatch event;
- driver-specific offer state;
- transition artifact from earlier implementation.

Поэтому здесь нельзя делать слепой rename без semantic audit.

---

## 2. Goal

Принять явное решение по `assigned`, чтобы он:

- либо исчез из persisted canonical truth;
- либо был ограничен как internal event only;
- либо был централизованно mapped к корректному canonical состоянию.

Итог должен исключать ситуацию, когда frontend/API получают двусмысленный `order_status`.

---

## 3. Known current state

### Canonical layer

Canonical order contract:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

### Runtime layer

`app/services/driver_operation_service.py` currently supports:

- `assigned`
- `accepted`
- `completed`
- `canceled`

### Confirmed problem

`assigned` currently exists in runtime/journal semantics, but no canonical `OrderStatus.ASSIGNED` exists.

This means one of the following is true:

1. `assigned` is incorrectly standing in for `created`
2. `assigned` is an internal event, not a canonical status
3. the current order flow is missing a clearer split between event history and canonical current status

---

## 4. Decision options

## Option A. `assigned` == `created`

### Use when

Choose this only if business meaning is:

- order exists and is available in driver flow
- no driver has accepted it yet
- no extra semantics beyond open/unaccepted order are intended

### Result

- cleanup `assigned -> created`
- stop writing `assigned` as persisted order status
- keep only canonical `created`

### Pros

- simplest contract
- easiest for API/frontend
- aligns directly with docs

### Risks

- may erase useful distinction if `assigned` actually means something narrower than `created`

---

## Option B. `assigned` is an internal event, not a canonical status

### Use when

Choose this if business meaning is:

- order was routed/shown/attached to a driver scope
- but current canonical order state is still really `created`

### Result

- `assigned` stays only in event/history semantics
- `assigned` is never exposed as canonical `order_status`
- canonical current status remains `created`

### Pros

- preserves event information
- avoids polluting API/frontend with non-canonical status
- models dispatch flow more honestly

### Risks

- requires clearer separation of `status` vs `event`
- may need light repository or payload restructuring

---

## Option C. `assigned` is a real domain state and contract must evolve

### Use when

Choose this only if there is strong product/backend evidence that:

- `assigned` is a real stable domain state distinct from `created`
- it must be visible outside backend internals
- it affects permissions, routing, and UI logic distinctly

### Result

- canonical contract would need explicit expansion
- docs, enums, services, and API tests all need updates

### Why this is least preferred

This increases contract surface and should not be chosen unless the business case is clearly stronger than current canonical contract simplicity.

---

## 5. Recommended default direction

**Default recommendation: treat `assigned` as internal event or transitional artifact until proven otherwise.**

That means:

- do not expose `assigned` as canonical `order_status`
- do not let frontend/UI depend on it
- prefer either:
  - cleanup to `created`, or
  - internal-event-only handling

This preserves the clean canonical order ladder:

- `created`
- `accepted`
- `arriving`
- `ontrip`
- `done`
- `canceled`

---

## 6. Audit checklist

Before changing code, answer these questions.

### 6.1. Write-path audit

- [ ] where exactly is `assigned` written today;
- [ ] is it written only to `order_journal_records` or elsewhere too;
- [ ] is it used as current status or as historical marker;
- [ ] can new rows still be produced with `assigned` after the desired cleanup.

### 6.2. Read-path audit

- [ ] which repository readers interpret `assigned`;
- [ ] do any API payloads expose `assigned` directly or indirectly;
- [ ] do any filters/reports depend on `assigned`;
- [ ] do any UI-facing functions branch on `assigned`.

### 6.3. Semantic audit

- [ ] does `assigned` happen before acceptance;
- [ ] can multiple drivers observe the same order while it is `assigned`;
- [ ] is `assigned` driver-specific or order-global;
- [ ] does `assigned` imply ownership;
- [ ] is there already another event name that better represents assignment/routing.

---

## 7. Preferred rollout by branch of decision

## 7.1. If Option A wins (`assigned` == `created`)

### Rollout

- [ ] replace new writes of `assigned` with `created`;
- [ ] add temporary read compatibility `assigned -> created` for historical rows;
- [ ] optionally migrate old rows later;
- [ ] ensure API only returns `created`.

## 7.2. If Option B wins (`assigned` is internal event only)

### Rollout

- [ ] stop treating `assigned` as canonical `order_status`;
- [ ] keep it only in event/history interpretation if truly needed;
- [ ] add explicit mapping so any read of `assigned` yields canonical current state `created` or other correct state;
- [ ] ensure API/frontend never receive `assigned` as the main status.

## 7.3. If Option C wins (contract expansion)

### Rollout

- [ ] update docs first;
- [ ] update enums and services;
- [ ] update API contract tests;
- [ ] update frontend gating rules;
- [ ] only then expose `assigned` outward.

This branch should require stronger evidence than the others.

---

## 8. Testing requirements

Whichever option wins, add or update tests that prove the chosen meaning.

### Minimum test expectations

- [ ] `assigned` does not leak ambiguously into canonical API status
- [ ] `accepted` remains distinct and correct
- [ ] downstream reads interpret legacy `assigned` consistently
- [ ] no frontend-facing contract requires understanding `assigned`

### If cleaned to `created`

- [ ] legacy `assigned` row reads as canonical `created`
- [ ] new writes use `created`

### If kept as internal event only

- [ ] event/history can still retain assignment semantics
- [ ] main status returned outward remains canonical

---

## 9. Acceptance criteria

- [ ] semantic meaning of `assigned` explicitly decided
- [ ] chosen option documented: cleanup, internal event only, or contract expansion
- [ ] new writes follow the chosen rule
- [ ] historical reads are compatible if needed
- [ ] API/frontend do not receive ambiguous non-canonical order status
- [ ] this decision is complete before broader HTTP wiring depends on order-status stability

---

## 10. Follow-up after this decision

Once `assigned` is resolved, the next practical status-alignment steps are:

1. finalize waybill -> trip-sheet adapter
2. define `requires_closing` behavior
3. re-check backend services against final status rules
4. apply HTTP wiring
5. activate API contract tests
6. move to frontend gating

This keeps the ladder clean: first remove semantic fog at the persisted/runtime layer, then let HTTP and UI ride on stable rails.
