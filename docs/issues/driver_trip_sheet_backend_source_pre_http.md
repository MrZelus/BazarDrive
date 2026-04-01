# Driver Trip Sheet Backend Source Before HTTP

Этот документ фиксирует **второй оставшийся backend blocker перед переходом к HTTP wiring**:

**зафиксировать один устойчивый backend source для canonical `trip_sheet_status` на основе persisted waybill data.**

---

## 1. Почему это осталось blocker-ом

После pre-HTTP re-check стало видно, что кроме `driver_operation_service.py` есть ещё один маленький, но важный узел:

- canonical HTTP layer later will want to expose `trip_sheet_status`
- canonical backend contract already expects trip-sheet ladder:
  - `missing`
  - `open`
  - `requires_closing`
  - `closed`
- persisted reality currently lives inside `driver_documents` as waybill rows

Пока нет одного явного backend source, future HTTP layer рискует начать собирать `trip_sheet_status` из полуявных правил в разных местах.

---

## 2. Цель

Сделать так, чтобы до HTTP было понятно:

- где именно backend получает trip-sheet truth
- как persisted waybill rows превращаются в canonical `TripSheetStatus`
- где живёт правило для `requires_closing`
- какой backend place later feeds `trip_sheet_status` into HTTP payloads

---

## 3. Minimal rule to achieve before HTTP

До перехода к HTTP нужно иметь **one backend place only**, которое отвечает за trip-sheet interpretation.

Это место должно:

- читать persisted waybill facts
- возвращать canonical `TripSheetStatus`
- при необходимости возвращать вспомогательные readiness flags

---

## 4. Recommended canonical source shape

### Input

Persisted facts from waybill persistence in `driver_documents`, at minimum:

- `type = 'waybill'`
- `status`
- relevant validity / closure fields
- current-day / active-shift context if needed

### Output

At minimum:

- `trip_sheet_status`

Optionally:

- `trip_sheet_ok`
- `trip_sheet_requires_action`
- `trip_sheet_reason`

---

## 5. Required mapping rules

### 5.1. `missing`

Return `missing` when:

- no usable current waybill row exists for the required work context

### 5.2. `open`

Return `open` when:

- persisted waybill row exists
- `type = 'waybill'`
- status semantics indicate active/open sheet

### 5.3. `closed`

Return `closed` when:

- persisted waybill row exists
- close flow completed
- persisted semantics indicate fully closed sheet

### 5.4. `requires_closing`

Return `requires_closing` when:

- backend close-required condition is met
- but trip sheet is not yet fully closed

Important:

`requires_closing` should not be left as UI-only interpretation.
It must be decided on backend side before HTTP.

---

## 6. What must be decided explicitly

Before HTTP, backend must answer these questions:

- [ ] what exactly counts as “usable current waybill row”
- [ ] does `requires_closing` depend on shift-end state
- [ ] does `requires_closing` depend on missing closure fields
- [ ] does `requires_closing` depend on completed work in the current period
- [ ] should `closed` remain directly mapped from persisted waybill close flow

---

## 7. Preferred placement

The source should live in one backend place only, for example:

- dedicated adapter/helper next to driver status layer
- or a small backend service used by `driver_status_service.py` and later HTTP adapters

Avoid:

- duplicating the logic in repository and again in HTTP
- duplicating the logic in backend and UI
- letting frontend infer `trip_sheet_status` from raw waybill fields

---

## 8. Minimal acceptance criteria before HTTP

- [ ] one backend place for trip-sheet interpretation is named
- [ ] `missing/open/closed` mapping is explicit
- [ ] `requires_closing` has a backend-side rule, even if provisional
- [ ] later HTTP layer can consume `trip_sheet_status` from that source directly
- [ ] frontend will not need to reconstruct trip-sheet semantics itself

---

## 9. Follow-up after this is fixed

Once both remaining blockers are narrowed enough:

1. stabilize `driver_operation_service.py`
2. stabilize one backend source for `trip_sheet_status`
3. re-check pre-HTTP readiness one more time
4. move to HTTP wiring
5. activate API contract tests

That is the last clean bridge before HTTP stops being speculative and becomes mechanical integration.
