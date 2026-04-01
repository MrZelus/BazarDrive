# Driver assigned semantics audit (post completion alignment)

## Goal

Take `assigned` as a separate, narrow semantic slice after `completed -> done` alignment.

The purpose is not to immediately rewrite behavior, but to:
- map where `assigned` is used
- distinguish internal vs outward meaning
- prevent `assigned` from leaking as an implicit canonical truth into HTTP

---

## Why this exists

After aligning completion to `done`, the main remaining semantic ambiguity is around `assigned`:

- it appears in operation service writes
- it appears in HTTP handlers
- it is asserted in tests

But it is unclear whether it is:
- a true canonical order status
- an internal transition marker
- a UI-facing state

---

## Scope

### 1. Operation layer
- identify where `assigned` is written
- check if it is persisted or just emitted
- verify if it is part of `ORDER_STATUSES`

### 2. HTTP layer
- identify where `assigned` is returned in payloads
- check if it is treated as current state vs transitional event

### 3. Tests
- locate expectations tied to `assigned`
- identify if tests treat it as canonical or transitional

---

## Key questions

1. Is `assigned` a canonical order status or a transition event?
2. Should it appear in outward API responses as a stable `status`?
3. Should it be replaced or wrapped into a clearer state model (e.g., `accepted` as first stable state)?

---

## Out of scope

- trip-sheet / waybill logic
- frontend gating changes
- full HTTP contract redesign

---

## Acceptance criteria

- a clear classification of `assigned` (canonical vs transitional)
- identified read/write points across backend
- no immediate refactor required, but a clear next decision point

---

## Result

This audit isolates the last major semantic ambiguity before moving toward a clean backend ready for HTTP wiring.