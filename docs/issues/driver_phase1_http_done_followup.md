# Driver Phase 1 follow-up: HTTP done cleanup

## Goal
Align the HTTP layer and feed API validation tests with the already merged `completed -> done` cleanup in `app/services/driver_operation_service.py`.

This follow-up is intentionally narrow.

It should:
- remove lingering `completed` transition handling in `app/api/http_handlers.py`
- update validation tests that still assert `completed`
- keep `assigned` semantics out of scope for now unless they directly block this cleanup
- avoid trip-sheet, frontend, or broader HTTP wiring changes

---

## Why this follow-up exists

Phase 1 code cleanup already landed in `DriverOperationService`.

Current repository search still shows remaining tails:

- `app/api/http_handlers.py`
  - `_handle_driver_order_transition("completed")`
  - `elif status == "completed"`
- `tests/test_feed_api_validation.py`
  - expects `"completed"`
  - includes `"completed"` in status sets
  - filters by `order_status == "completed"`

That means the operation layer has moved to canonical `done`, but parts of the HTTP/test layer still speak legacy `completed`.

---

## Scope

### 1. `app/api/http_handlers.py`
Replace `completed` order-transition handling with `done` where it reflects the operation-layer completion transition.

Targeted cleanup:
- `_handle_driver_order_transition("completed")` -> `_handle_driver_order_transition("done")`
- `elif status == "completed":` -> `elif status == "done":`

Important:
- do not expand this into general `assigned` semantics cleanup
- do not mix in adapter-layer refactors
- do not widen the patch beyond the existing completion path

### 2. `tests/test_feed_api_validation.py`
Update expectations that still assert legacy `completed`.

Targeted cleanup:
- `complete_payload.get("status") == "completed"` -> `== "done"`
- status set assertions should include `done` instead of `completed`
- filtered payload assertions should expect canonical completion status instead of legacy completion literal

---

## Out of scope

- resolving `assigned` semantics
- trip-sheet / waybill canonicalization
- frontend gating
- new HTTP adapters or wiring
- migration of historical rows

---

## Acceptance criteria

- no lingering completion transition path in `http_handlers.py` still points to `completed`
- feed API validation tests no longer expect `completed` as the completion status literal
- the cleanup remains limited to `done` completion alignment
- `assigned` is not reinterpreted in this patch

---

## Result

After this follow-up, the operation layer and immediate HTTP/test surface stop disagreeing about the completion literal.

That keeps Phase 1 moving toward a backend that speaks one language before broader HTTP wiring begins.
