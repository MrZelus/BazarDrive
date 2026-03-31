from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.driver_enums import (
    EligibilityStatus,
    NotificationChannel,
    NotificationPriority,
)


@dataclass(slots=True)
class TransitionResult:
    is_allowed: bool
    from_status: str
    to_status: str
    error_code: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class PermissionCheckResult:
    is_allowed: bool
    error_code: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class EligibilitySnapshot:
    status: EligibilityStatus
    profile_status: str
    has_valid_vehicle: bool
    has_required_documents: bool
    trip_sheet_ok: bool
    hard_blockers: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NotificationDispatchPlan:
    event_name: str
    recipient_id: str
    channels: list[NotificationChannel]
    priority: NotificationPriority
    dedupe_key: str
    payload: dict[str, Any] = field(default_factory=dict)
