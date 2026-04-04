from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from app.api.driver_http_contract import (
    driver_error_payload,
    driver_go_online_success_payload,
    driver_order_success_payload,
    driver_shift_success_payload,
    driver_validation_error_payload,
)


LEGACY_DRIVER_ERROR_CODE_MAP = {
    "trip_sheet_required": "WAYBILL_REQUIRED",
    "required_document_missing": "DOC_EXPIRED",
    "driver_not_eligible": "PROFILE_INCOMPLETE",
    "profile_blocked": "DRIVER_NOT_ALLOWED",
    "driver_not_allowed": "DRIVER_NOT_ALLOWED",
}


def _canonical_driver_error_code(code: object) -> str:
    normalized = str(code or "driver_not_allowed").strip()
    if not normalized:
        normalized = "driver_not_allowed"
    return normalized.lower()


def _normalize_driver_error_code(code: object) -> str:
    normalized = str(code or "driver_not_allowed").strip()
    if not normalized:
        normalized = "driver_not_allowed"
    return LEGACY_DRIVER_ERROR_CODE_MAP.get(normalized.lower(), normalized.upper())


def _serialize_notification_plan(plan: Any) -> dict[str, Any] | None:
    if plan is None:
        return None
    if is_dataclass(plan):
        return asdict(plan)
    if isinstance(plan, dict):
        return plan
    if hasattr(plan, "__dict__"):
        return dict(plan.__dict__)
    return None


def adapt_go_online_result(result: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    if not result.get("ok"):
        canonical_code = _canonical_driver_error_code(result.get("code"))
        legacy_code = _normalize_driver_error_code(canonical_code)
        payload = driver_error_payload(
            code=canonical_code,
            message="Нет допуска к выходу на линию",
            reason=str(result.get("reason", "Нет допуска к выходу на линию")),
            actions=list(result.get("actions", [])),
        )
        payload["code"] = legacy_code
        return 403, payload
    return 200, driver_go_online_success_payload(
        status=str(result.get("status", "online")),
        shift_status=str(result.get("shift_status", result.get("status", "online"))),
        event_name=str(result.get("event_name", "shift_online")),
        notification_plan=_serialize_notification_plan(result.get("notification_plan")),
    )


def adapt_accept_order_result(result: dict[str, Any], order_id: object) -> tuple[int, dict[str, Any]]:
    if not result.get("ok"):
        canonical_code = _canonical_driver_error_code(result.get("code"))
        legacy_code = _normalize_driver_error_code(canonical_code)
        payload = driver_error_payload(
            code=canonical_code,
            message="Нельзя принимать заказы",
            reason=str(result.get("reason", "Нельзя принимать заказы")),
            actions=list(result.get("actions", [])),
        )
        payload["code"] = legacy_code
        return 403, payload
    return 200, driver_order_success_payload(
        order_id=result.get("order_id", order_id),
        status=str(result.get("status", "accepted")),
        order_status=str(result.get("order_status", result.get("status", "accepted"))),
        event_name=str(result.get("event_name", "order_accepted")),
        notification_plan=_serialize_notification_plan(result.get("notification_plan")),
    )


def adapt_order_transition_result(result: dict[str, Any], order_id: object, fallback_status: str) -> tuple[int, dict[str, Any]]:
    return 200, driver_order_success_payload(
        order_id=result.get("order_id", order_id),
        status=str(result.get("status", fallback_status)),
        order_status=result.get("order_status"),
        event_name=result.get("event_name"),
        notification_plan=_serialize_notification_plan(result.get("notification_plan")),
    )


def adapt_shift_open_success(waybill_id: object) -> tuple[int, dict[str, Any]]:
    return 200, driver_shift_success_payload(
        waybill_id=waybill_id,
        trip_sheet_status="open",
        event_name="trip_sheet_opened",
    )


def adapt_shift_close_success(waybill_id: object) -> tuple[int, dict[str, Any]]:
    return 200, driver_shift_success_payload(
        waybill_id=waybill_id,
        trip_sheet_status="closed",
        event_name="trip_sheet_closed",
    )


def adapt_missing_order_id_error() -> tuple[int, dict[str, Any]]:
    return 400, {"ok": False, "error": "order_id required", "code": "order_id_required"}


def adapt_shift_open_conflict(message: str) -> tuple[int, dict[str, Any]]:
    return 409, driver_error_payload(code="shift_open_conflict", message=message)


def adapt_shift_close_invalid(message: str) -> tuple[int, dict[str, Any]]:
    return 404, driver_error_payload(code="trip_sheet_close_invalid", message=message)


def adapt_waybill_validation_error(fields: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return 400, driver_validation_error_payload(fields=fields)
