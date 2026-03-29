from datetime import datetime, timezone

from app.db import repository
from app.services.driver_guard_service import DriverGuardService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError


class DriverOperationService:
    ORDER_STATUSES = {"assigned", "accepted", "completed", "canceled"}

    @staticmethod
    def _record_order_status_transition(
        *,
        order_id: object,
        driver_profile_id: str,
        status: str,
        details: dict[str, object] | None = None,
    ) -> None:
        if status not in DriverOperationService.ORDER_STATUSES:
            raise ValueError("unsupported order status")
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = dict(details or {})
        payload.setdefault("order_number", str(order_id))
        payload.setdefault("source_request_id", order_id if isinstance(order_id, int) else None)
        payload.setdefault("order_status", status)
        payload.setdefault("event_at", now_iso)
        payload.setdefault("profile_id", driver_profile_id)
        payload.setdefault("pickup_address", str(payload.get("pickup_address", "Не указано")))
        payload.setdefault("dropoff_address", str(payload.get("dropoff_address", "Не указано")))
        if status == "accepted":
            payload.setdefault("accepted_at", now_iso)
        if status == "completed":
            payload.setdefault("completed_at", now_iso)
            payload.setdefault("ride_completed_at_actual", now_iso)
        repository.create_order_journal_record(payload)

    @staticmethod
    def go_online(driver_profile_id: str) -> dict[str, object]:
        try:
            DriverGuardService.ensure_can_go_online(driver_profile_id)
        except DriverOfflineBlockedError as error:
            return {
                "ok": False,
                "code": error.code,
                "reason": error.reason,
                "actions": error.actions,
            }

        return {
            "ok": True,
            "status": "online",
        }

    @staticmethod
    def accept_order(order_id: object, driver_profile_id: str) -> dict[str, object]:
        try:
            DriverGuardService.ensure_can_accept_order(driver_profile_id)
        except DriverOrderBlockedError as error:
            return {
                "ok": False,
                "code": error.code,
                "reason": error.reason,
                "actions": error.actions,
            }
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="accepted",
        )

        return {
            "ok": True,
            "order_id": order_id,
            "status": "accepted",
        }

    @staticmethod
    def assign_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="assigned",
            details=details,
        )
        return {"ok": True, "order_id": order_id, "status": "assigned"}

    @staticmethod
    def complete_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="completed",
            details=details,
        )
        return {"ok": True, "order_id": order_id, "status": "completed"}

    @staticmethod
    def cancel_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="canceled",
            details=details,
        )
        return {"ok": True, "order_id": order_id, "status": "canceled"}
