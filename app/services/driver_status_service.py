from __future__ import annotations

from app.models.driver_enums import (
    DocumentStatus,
    EligibilityStatus,
    OrderStatus,
    ProfileStatus,
    ShiftStatus,
    TripSheetStatus,
)
from app.models.driver_error_codes import DriverErrorCode
from app.services.driver_contracts import EligibilitySnapshot, TransitionResult
from app.services.driver_trip_sheet_service import DriverTripSheetService


class DriverStatusService:
    PROFILE_TRANSITIONS: dict[ProfileStatus, set[ProfileStatus]] = {
        ProfileStatus.DRAFT: {ProfileStatus.INCOMPLETE},
        ProfileStatus.INCOMPLETE: {ProfileStatus.PENDING_VERIFICATION},
        ProfileStatus.PENDING_VERIFICATION: {
            ProfileStatus.APPROVED,
            ProfileStatus.REJECTED,
        },
        ProfileStatus.REJECTED: {ProfileStatus.INCOMPLETE},
        ProfileStatus.APPROVED: {ProfileStatus.BLOCKED},
        ProfileStatus.BLOCKED: {ProfileStatus.INCOMPLETE},
    }

    DOCUMENT_TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
        DocumentStatus.MISSING: {DocumentStatus.UPLOADED},
        DocumentStatus.UPLOADED: {
            DocumentStatus.CHECKING,
            DocumentStatus.APPROVED,
        },
        DocumentStatus.CHECKING: {
            DocumentStatus.APPROVED,
            DocumentStatus.REJECTED,
        },
        DocumentStatus.APPROVED: {DocumentStatus.EXPIRED},
        DocumentStatus.REJECTED: {DocumentStatus.UPLOADED},
        DocumentStatus.EXPIRED: {DocumentStatus.UPLOADED},
    }

    TRIP_SHEET_TRANSITIONS: dict[TripSheetStatus, set[TripSheetStatus]] = {
        TripSheetStatus.MISSING: {TripSheetStatus.OPEN},
        TripSheetStatus.OPEN: {TripSheetStatus.REQUIRES_CLOSING},
        TripSheetStatus.REQUIRES_CLOSING: {TripSheetStatus.CLOSED},
        TripSheetStatus.CLOSED: {TripSheetStatus.OPEN},
    }

    SHIFT_TRANSITIONS: dict[ShiftStatus, set[ShiftStatus]] = {
        ShiftStatus.OFFLINE: {ShiftStatus.READY},
        ShiftStatus.READY: {ShiftStatus.ONLINE},
        ShiftStatus.ONLINE: {ShiftStatus.BUSY, ShiftStatus.ENDING},
        ShiftStatus.BUSY: {ShiftStatus.ONLINE},
        ShiftStatus.ENDING: {ShiftStatus.CLOSED},
        ShiftStatus.CLOSED: {ShiftStatus.READY},
    }

    ORDER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.CREATED: {OrderStatus.ACCEPTED, OrderStatus.CANCELED},
        OrderStatus.ACCEPTED: {OrderStatus.ARRIVING, OrderStatus.CANCELED},
        OrderStatus.ARRIVING: {OrderStatus.ONTRIP, OrderStatus.CANCELED},
        OrderStatus.ONTRIP: {OrderStatus.DONE, OrderStatus.CANCELED},
        OrderStatus.DONE: set(),
        OrderStatus.CANCELED: set(),
    }

    @classmethod
    def _validate_transition(
        cls,
        transition_map: dict,
        from_status: str,
        to_status: str,
        error_code: DriverErrorCode,
    ) -> TransitionResult:
        allowed_targets = transition_map.get(from_status, set())
        is_allowed = to_status in allowed_targets
        return TransitionResult(
            is_allowed=is_allowed,
            from_status=from_status,
            to_status=to_status,
            error_code=None if is_allowed else error_code.value,
            reason=None if is_allowed else f"Forbidden transition: {from_status} -> {to_status}",
        )

    @classmethod
    def validate_profile_transition(
        cls,
        from_status: ProfileStatus,
        to_status: ProfileStatus,
    ) -> TransitionResult:
        return cls._validate_transition(
            cls.PROFILE_TRANSITIONS,
            from_status,
            to_status,
            DriverErrorCode.INVALID_PROFILE_TRANSITION,
        )

    @classmethod
    def validate_document_transition(
        cls,
        from_status: DocumentStatus,
        to_status: DocumentStatus,
    ) -> TransitionResult:
        return cls._validate_transition(
            cls.DOCUMENT_TRANSITIONS,
            from_status,
            to_status,
            DriverErrorCode.INVALID_DOCUMENT_TRANSITION,
        )

    @classmethod
    def validate_trip_sheet_transition(
        cls,
        from_status: TripSheetStatus,
        to_status: TripSheetStatus,
    ) -> TransitionResult:
        return cls._validate_transition(
            cls.TRIP_SHEET_TRANSITIONS,
            from_status,
            to_status,
            DriverErrorCode.INVALID_TRIP_SHEET_TRANSITION,
        )

    @classmethod
    def validate_shift_transition(
        cls,
        from_status: ShiftStatus,
        to_status: ShiftStatus,
    ) -> TransitionResult:
        return cls._validate_transition(
            cls.SHIFT_TRANSITIONS,
            from_status,
            to_status,
            DriverErrorCode.INVALID_SHIFT_TRANSITION,
        )

    @classmethod
    def validate_order_transition(
        cls,
        from_status: OrderStatus,
        to_status: OrderStatus,
    ) -> TransitionResult:
        return cls._validate_transition(
            cls.ORDER_TRANSITIONS,
            from_status,
            to_status,
            DriverErrorCode.INVALID_ORDER_TRANSITION,
        )

    @staticmethod
    def is_trip_sheet_ready(trip_sheet_status: TripSheetStatus) -> bool:
        return trip_sheet_status == TripSheetStatus.OPEN

    @staticmethod
    def get_driver_trip_sheet_status(driver_profile_id: str) -> TripSheetStatus:
        return DriverTripSheetService.get_trip_sheet_status(driver_profile_id)

    @classmethod
    def compute_eligibility(
        cls,
        profile_status: ProfileStatus,
        has_valid_vehicle: bool,
        has_required_documents: bool,
        trip_sheet_status: TripSheetStatus,
        hard_blockers: list[str] | None = None,
    ) -> EligibilitySnapshot:
        blockers = list(hard_blockers or [])
        missing_items: list[str] = []

        trip_sheet_ok = cls.is_trip_sheet_ready(trip_sheet_status)

        if profile_status != ProfileStatus.APPROVED:
            missing_items.append("profile_not_approved")
        if not has_valid_vehicle:
            missing_items.append("vehicle_not_ready")
        if not has_required_documents:
            missing_items.append("required_documents_missing_or_invalid")
        if not trip_sheet_ok:
            missing_items.append("trip_sheet_not_ready")

        if blockers:
            status = EligibilityStatus.BLOCKED
        elif not missing_items:
            status = EligibilityStatus.READY
        elif len(missing_items) >= 3:
            status = EligibilityStatus.NOT_READY
        else:
            status = EligibilityStatus.PARTIALLY_READY

        return EligibilitySnapshot(
            status=status,
            profile_status=profile_status.value,
            has_valid_vehicle=has_valid_vehicle,
            has_required_documents=has_required_documents,
            trip_sheet_ok=trip_sheet_ok,
            hard_blockers=blockers,
            missing_items=missing_items,
        )
