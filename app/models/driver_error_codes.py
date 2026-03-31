from __future__ import annotations

from enum import StrEnum


class DriverErrorCode(StrEnum):
    PERMISSION_DENIED = "permission_denied"
    OWNERSHIP_REQUIRED = "ownership_required"
    DRIVER_NOT_ELIGIBLE = "driver_not_eligible"
    PROFILE_BLOCKED = "profile_blocked"
    ACTIVE_SHIFT_CONFLICT = "active_shift_conflict"
    ACTIVE_ORDER_CONFLICT = "active_order_conflict"
    ADMIN_OVERRIDE_REQUIRED = "admin_override_required"

    INVALID_PROFILE_TRANSITION = "invalid_profile_transition"
    INVALID_DOCUMENT_TRANSITION = "invalid_document_transition"
    INVALID_TRIP_SHEET_TRANSITION = "invalid_trip_sheet_transition"
    INVALID_SHIFT_TRANSITION = "invalid_shift_transition"
    INVALID_ORDER_TRANSITION = "invalid_order_transition"

    ELIGIBILITY_BLOCKED = "eligibility_blocked"
    REQUIRED_DOCUMENT_MISSING = "required_document_missing"
    TRIP_SHEET_REQUIRED = "trip_sheet_required"
