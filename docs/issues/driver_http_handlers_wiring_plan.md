# Driver HTTP Handlers Wiring Plan

Этот документ фиксирует точный короткий wiring-шаг для подключения canonical driver HTTP adapters в `app/api/http_handlers.py`.

Цель: не переписывать giant handler целиком, а заменить только несколько driver-specific payload blocks на вызовы adapter-функций.

## 1. Импорты

Добавить рядом с `from app.config import get_api_settings`:

```python
from app.api.driver_http_adapters import (
    adapt_accept_order_result,
    adapt_go_online_result,
    adapt_missing_order_id_error,
    adapt_order_transition_result,
    adapt_shift_close_invalid,
    adapt_shift_close_success,
    adapt_shift_open_conflict,
    adapt_shift_open_success,
    adapt_waybill_validation_error,
)
```

## 2. `_handle_driver_go_online`

### Было
- при blocked: inline dict с `ok/code/reason/actions`
- при success: прямой `result`

### Должно стать

```python
result = DriverOperationService.go_online(profile_id)
http_status, payload = adapt_go_online_result(result)
self._send_json(http_status, payload)
return
```

Для `except DriverNotAllowedError as e`:

```python
http_status, payload = adapt_go_online_result(
    {
        "ok": False,
        "code": e.code,
        "reason": e.reason,
        "actions": e.actions,
    }
)
self._send_json(http_status, payload)
```

## 3. `_handle_driver_accept_order`

### Было
- missing `order_id` -> `{ "error": "order_id required" }`
- blocked -> inline dict
- success -> прямой `result`

### Должно стать

Для missing `order_id`:

```python
http_status, payload = adapt_missing_order_id_error()
self._send_json(http_status, payload)
return
```

Для основного success/error:

```python
result = DriverOperationService.accept_order(order_id, profile_id)
http_status, payload = adapt_accept_order_result(result, order_id=order_id)
self._send_json(http_status, payload)
return
```

Для `except DriverNotAllowedError as e`:

```python
http_status, payload = adapt_accept_order_result(
    {
        "ok": False,
        "code": e.code,
        "reason": e.reason,
        "actions": e.actions,
    },
    order_id=order_id,
)
self._send_json(http_status, payload)
```

## 4. `_handle_driver_order_transition`

### Было
- missing `order_id` -> raw string error
- success -> raw `result`

### Должно стать

Для missing `order_id`:

```python
http_status, payload = adapt_missing_order_id_error()
self._send_json(http_status, payload)
return
```

Для success:

```python
http_status, response_payload = adapt_order_transition_result(
    result,
    order_id=order_id,
    fallback_status=status,
)
self._send_json(http_status, response_payload)
return
```

## 5. `_handle_driver_shift_open`

### Было
- success -> `{ "waybill_id": waybill_id }`
- conflict -> `{ "error": str(error) }`

### Должно стать

```python
http_status, response_payload = adapt_shift_open_success(waybill_id)
self._send_json(http_status, response_payload)
```

Для `ValueError`:

```python
http_status, response_payload = adapt_shift_open_conflict(str(error))
self._send_json(http_status, response_payload)
```

## 6. `_handle_driver_shift_close`

### Было
- validation -> raw `validation_error`
- success -> `{ "waybill_id": waybill_id }`
- invalid close -> raw `{ "error": str(error) }`

### Должно стать

Для validation:

```python
http_status, response_payload = adapt_waybill_validation_error(closure_errors)
self._send_json(http_status, response_payload)
return
```

Для success:

```python
http_status, response_payload = adapt_shift_close_success(waybill_id)
self._send_json(http_status, response_payload)
```

Для invalid close:

```python
http_status, response_payload = adapt_shift_close_invalid(str(error))
self._send_json(http_status, response_payload)
```

## 7. Минимальные endpoint-level tests после wiring

После подключения adapters в `http_handlers.py` добавить endpoint tests:

- `tests/test_driver_api_go_online_http_contract.py`
- `tests/test_driver_api_accept_order_http_contract.py`
- `tests/test_driver_api_shift_http_contract.py`

### Проверять
- `go-online` blocked -> `error.code`
- `go-online` success -> `shift_status`, `event_name`
- `accept-order` missing `order_id` -> `error.code == order_id_required`
- `accept-order` success -> `order_status`, `event_name`
- `shift/open` success -> `trip_sheet_status == open`
- `shift/close` success -> `trip_sheet_status == closed`
- `shift/close` validation -> `validation_error`

## 8. Почему это безопасно

Этот wiring не меняет feed/guest части и не переписывает giant handler структурно.
Он только:
- добавляет импорт adapters
- заменяет несколько inline payload dicts
- сохраняет существующий control flow

## 9. Связанные PR

- PR #356: backend contract skeleton
- PR #357: runtime service integration
- PR #358: canonical HTTP payload helpers
- PR #359: handler adapters for canonical payloads

## 10. Итог

После этого wiring-шагa driver HTTP layer начнёт отдавать canonical payloads без массового рефактора `http_handlers.py`.
