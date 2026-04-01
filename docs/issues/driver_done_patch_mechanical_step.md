# Driver `done` Patch Mechanical Step

Этот документ фиксирует **точный механический patch-step** для первого живого backend alignment change:

**перевести runtime/journal completion write path с legacy `completed` на canonical `done` в `app/services/driver_operation_service.py`.**

---

## Цель

Сделать так, чтобы:

- новые completion writes в journal использовали `done`;
- runtime `status` для `complete_order()` тоже был `done`;
- canonical `order_status = done` в API payload уже не расходился с persisted/runtime semantics.

---

## Файл

- `app/services/driver_operation_service.py`

---

## Точные изменения

### 1. Обновить supported runtime statuses

### Было

```python
class DriverOperationService:
    ORDER_STATUSES = {"assigned", "accepted", "completed", "canceled"}
```

### Должно стать

```python
class DriverOperationService:
    ORDER_STATUSES = {"assigned", "accepted", "done", "canceled"}
```

---

### 2. Обновить journal completion branch

### Было

```python
        if status == "completed":
            payload.setdefault("completed_at", now_iso)
            payload.setdefault("ride_completed_at_actual", now_iso)
```

### Должно стать

```python
        if status == "done":
            payload.setdefault("completed_at", now_iso)
            payload.setdefault("ride_completed_at_actual", now_iso)
```

Важно: поля `completed_at` и `ride_completed_at_actual` остаются без переименования на этом шаге.
Это rollout только по `order_status`, не по schema fields.

---

### 3. Обновить complete-order write path

### Было

```python
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="completed",
            details=details,
        )
```

### Должно стать

```python
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="done",
            details=details,
        )
```

---

### 4. Обновить runtime success status

### Было

```python
        return {
            "ok": True,
            "order_id": order_id,
            "status": "completed",
            "order_status": OrderStatus.DONE.value,
            "event_name": DriverEvent.ORDER_DONE.value,
            ...
        }
```

### Должно стать

```python
        return {
            "ok": True,
            "order_id": order_id,
            "status": "done",
            "order_status": OrderStatus.DONE.value,
            "event_name": DriverEvent.ORDER_DONE.value,
            ...
        }
```

---

## Что не менять этим patch-step

На этом шаге не делать:

- migration historical rows `completed -> done`;
- cleanup `assigned`;
- waybill/trip-sheet refactor;
- HTTP wiring;
- frontend gating updates.

Это intentionally narrow patch.

---

## Минимальная проверка после patch

- `complete_order()` больше не пишет `completed` в новый journal payload
- runtime `status` возвращается как `done`
- canonical `order_status` остаётся `done`
- код не ломает существующие timestamp fields

---

## Follow-up после этого patch-step

1. проверить repository readers на зависимость от `completed`
2. при необходимости ввести temporary read compatibility `completed -> done`
3. потом переходить к `assigned`
4. затем к HTTP wiring
