from datetime import datetime, timezone

from app.db import repository
from app.models.driver_enums import OrderStatus, ShiftStatus
from app.models.driver_events import DriverEvent
from app.services.driver_guard_service import DriverGuardService
from app.services.driver_notifications_service import DriverNotificationsService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError


class DriverOperationService:
    ORDER_STATUSES = {"accepted", "done", "canceled"}

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
        if status == "done":
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
            "shift_status": ShiftStatus.ONLINE.value,
            "event_name": DriverEvent.SHIFT_ONLINE.value,
            "notification_plan": DriverNotificationsService.build_notification_plan(
                event_name=DriverEvent.SHIFT_ONLINE,
                recipient_id=driver_profile_id,
                entity_id=driver_profile_id,
                state_version=ShiftStatus.ONLINE.value,
                payload={"profile_id": driver_profile_id},
            ).__dict__,
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
            "order_status": OrderStatus.ACCEPTED.value,
            "event_name": DriverEvent.ORDER_ACCEPTED.value,
            "notification_plan": DriverNotificationsService.build_notification_plan(
                event_name=DriverEvent.ORDER_ACCEPTED,
                recipient_id=driver_profile_id,
                entity_id=str(order_id),
                state_version=OrderStatus.ACCEPTED.value,
                payload={"profile_id": driver_profile_id, "order_id": order_id},
            ).__dict__,
        }

    @staticmethod
    def assign_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="accepted",
            details=details,
        )
        return {
            "ok": True,
            "order_id": order_id,
            "status": "accepted",
            "event_name": DriverEvent.ORDER_STATUS_CHANGED.value,
        }

    @staticmethod
    def complete_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="done",
            details=details,
        )
        return {
            "ok": True,
            "order_id": order_id,
            "status": "done",
            "order_status": OrderStatus.DONE.value,
            "event_name": DriverEvent.ORDER_DONE.value,
            "notification_plan": DriverNotificationsService.build_notification_plan(
                event_name=DriverEvent.ORDER_DONE,
                recipient_id=driver_profile_id,
                entity_id=str(order_id),
                state_version=OrderStatus.DONE.value,
                payload={"profile_id": driver_profile_id, "order_id": order_id},
            ).__dict__,
        }

    @staticmethod
    def cancel_order(order_id: object, driver_profile_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        DriverOperationService._record_order_status_transition(
            order_id=order_id,
            driver_profile_id=driver_profile_id,
            status="canceled",
            details=details,
        )
        return {
            "ok": True,
            "order_id": order_id,
            "status": "canceled",
            "order_status": OrderStatus.CANCELED.value,
            "event_name": DriverEvent.ORDER_CANCELED_AFTER_ACCEPT.value,
            "notification_plan": DriverNotificationsService.build_notification_plan(
                event_name=DriverEvent.ORDER_CANCELED_AFTER_ACCEPT,
                recipient_id=driver_profile_id,
                entity_id=str(order_id),
                state_version=OrderStatus.CANCELED.value,
                payload={"profile_id": driver_profile_id, "order_id": order_id},
            ).__dict__,
        }
