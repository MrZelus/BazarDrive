from __future__ import annotations

from typing import Any


def driver_error_payload(
    *,
    code: str,
    message: str,
    reason: str | None = None,
    actions: list[str] | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if reason is not None:
        error["reason"] = reason
    if actions:
        error["actions"] = list(actions)
    if fields:
        error["fields"] = dict(fields)
    return {
        "ok": False,
        "error": error,
    }


def driver_success_payload(**payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": True}
    result.update(payload)
    return result


def driver_go_online_success_payload(
    *,
    status: str,
    shift_status: str,
    event_name: str,
    notification_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = driver_success_payload(
        status=status,
        shift_status=shift_status,
        event_name=event_name,
    )
    if notification_plan is not None:
        payload["notification_plan"] = notification_plan
    return payload


def driver_order_success_payload(
    *,
    order_id: object,
    status: str,
    order_status: str | None = None,
    event_name: str | None = None,
    notification_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = driver_success_payload(
        order_id=order_id,
        status=status,
    )
    if order_status is not None:
        payload["order_status"] = order_status
    if event_name is not None:
        payload["event_name"] = event_name
    if notification_plan is not None:
        payload["notification_plan"] = notification_plan
    return payload


def driver_shift_success_payload(
    *,
    waybill_id: object,
    trip_sheet_status: str,
    event_name: str,
) -> dict[str, Any]:
    return driver_success_payload(
        waybill_id=waybill_id,
        trip_sheet_status=trip_sheet_status,
        event_name=event_name,
    )


def driver_validation_error_payload(
    *,
    fields: dict[str, Any],
    message: str = "validation_error",
) -> dict[str, Any]:
    return driver_error_payload(
        code="validation_error",
        message=message,
        fields=fields,
    )
