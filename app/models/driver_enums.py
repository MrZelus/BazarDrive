from __future__ import annotations

from enum import StrEnum


class ProfileStatus(StrEnum):
    DRAFT = "draft"
    INCOMPLETE = "incomplete"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class DocumentStatus(StrEnum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    CHECKING = "checking"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TripSheetStatus(StrEnum):
    MISSING = "missing"
    OPEN = "open"
    REQUIRES_CLOSING = "requires_closing"
    CLOSED = "closed"


class EligibilityStatus(StrEnum):
    NOT_READY = "not_ready"
    PARTIALLY_READY = "partially_ready"
    READY = "ready"
    BLOCKED = "blocked"


class ShiftStatus(StrEnum):
    OFFLINE = "offline"
    READY = "ready"
    ONLINE = "online"
    BUSY = "busy"
    ENDING = "ending"
    CLOSED = "closed"


class OrderStatus(StrEnum):
    CREATED = "created"
    ACCEPTED = "accepted"
    ARRIVING = "arriving"
    ONTRIP = "ontrip"
    DONE = "done"
    CANCELED = "canceled"


class NotificationPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    IN_APP = "in_app"
    INTERNAL = "internal"
