from __future__ import annotations

from app.models.driver_enums import NotificationChannel, NotificationPriority
from app.models.driver_events import DriverEvent
from app.services.driver_contracts import NotificationDispatchPlan


class DriverNotificationsService:
    PRIORITY_MAP = {
        DriverEvent.PROFILE_BLOCKED: NotificationPriority.CRITICAL,
        DriverEvent.ELIGIBILITY_BLOCKED: NotificationPriority.CRITICAL,
        DriverEvent.PROFILE_APPROVED: NotificationPriority.HIGH,
        DriverEvent.PROFILE_REJECTED: NotificationPriority.HIGH,
        DriverEvent.DOCUMENT_REJECTED: NotificationPriority.HIGH,
        DriverEvent.DOCUMENT_EXPIRED: NotificationPriority.HIGH,
        DriverEvent.TRIP_SHEET_REQUIRES_CLOSING: NotificationPriority.HIGH,
        DriverEvent.ORDER_OFFER_AVAILABLE: NotificationPriority.HIGH,
        DriverEvent.ORDER_ACCEPTED: NotificationPriority.HIGH,
        DriverEvent.ORDER_CANCELED_AFTER_ACCEPT: NotificationPriority.HIGH,
        DriverEvent.SCHEDULED_ORDER_REMINDER: NotificationPriority.HIGH,
    }

    @classmethod
    def get_priority(cls, event_name: DriverEvent) -> NotificationPriority:
        return cls.PRIORITY_MAP.get(event_name, NotificationPriority.MEDIUM)

    @classmethod
    def choose_channels(
        cls,
        event_name: DriverEvent,
    ) -> list[NotificationChannel]:
        priority = cls.get_priority(event_name)
        if priority in {NotificationPriority.CRITICAL, NotificationPriority.HIGH}:
            return [NotificationChannel.TELEGRAM, NotificationChannel.IN_APP]
        return [NotificationChannel.IN_APP]

    @staticmethod
    def build_dedupe_key(
        recipient_id: str,
        event_name: str,
        entity_id: str,
        state_version: str,
    ) -> str:
        return f"{recipient_id}:{event_name}:{entity_id}:{state_version}"

    @classmethod
    def build_notification_plan(
        cls,
        event_name: DriverEvent,
        recipient_id: str,
        entity_id: str,
        state_version: str,
        payload: dict | None = None,
    ) -> NotificationDispatchPlan:
        return NotificationDispatchPlan(
            event_name=event_name.value,
            recipient_id=recipient_id,
            channels=cls.choose_channels(event_name),
            priority=cls.get_priority(event_name),
            dedupe_key=cls.build_dedupe_key(
                recipient_id=recipient_id,
                event_name=event_name.value,
                entity_id=entity_id,
                state_version=state_version,
            ),
            payload=payload or {},
        )
