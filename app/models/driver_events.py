from __future__ import annotations

from enum import StrEnum


class DriverEvent(StrEnum):
    PROFILE_STATUS_CHANGED = "profile_status_changed"
    DOCUMENT_STATUS_CHANGED = "document_status_changed"
    TRIP_SHEET_STATUS_CHANGED = "trip_sheet_status_changed"
    ELIGIBILITY_CHANGED = "eligibility_changed"
    SHIFT_STATUS_CHANGED = "shift_status_changed"
    ORDER_STATUS_CHANGED = "order_status_changed"

    PROFILE_SUBMITTED_FOR_VERIFICATION = "profile_submitted_for_verification"
    PROFILE_APPROVED = "profile_approved"
    PROFILE_REJECTED = "profile_rejected"
    PROFILE_BLOCKED = "profile_blocked"
    PROFILE_UNBLOCKED = "profile_unblocked"

    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_UNDER_REVIEW = "document_under_review"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"
    DOCUMENT_EXPIRING_SOON = "document_expiring_soon"
    DOCUMENT_EXPIRED = "document_expired"

    TRIP_SHEET_REQUIRED_BEFORE_SHIFT = "trip_sheet_required_before_shift"
    TRIP_SHEET_OPENED = "trip_sheet_opened"
    TRIP_SHEET_REQUIRES_CLOSING = "trip_sheet_requires_closing"
    TRIP_SHEET_CLOSED = "trip_sheet_closed"

    ELIGIBILITY_READY = "eligibility_ready"
    ELIGIBILITY_PARTIALLY_READY = "eligibility_partially_ready"
    ELIGIBILITY_BLOCKED = "eligibility_blocked"
    ELIGIBILITY_RESTORED = "eligibility_restored"

    SHIFT_READY = "shift_ready"
    SHIFT_ONLINE = "shift_online"
    SHIFT_BUSY = "shift_busy"
    SHIFT_ENDING_STARTED = "shift_ending_started"
    SHIFT_CLOSE_BLOCKED = "shift_close_blocked"
    SHIFT_CLOSED = "shift_closed"

    ORDER_OFFER_AVAILABLE = "order_offer_available"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_ARRIVING = "order_arriving"
    ORDER_ONTRIP = "order_ontrip"
    ORDER_DONE = "order_done"
    ORDER_CANCELED_BEFORE_ACCEPT = "order_canceled_before_accept"
    ORDER_CANCELED_AFTER_ACCEPT = "order_canceled_after_accept"
    SCHEDULED_ORDER_REMINDER = "scheduled_order_reminder"
