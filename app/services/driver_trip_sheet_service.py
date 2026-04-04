from app.db import repository
from app.models.driver_enums import TripSheetStatus


class DriverTripSheetService:
    @staticmethod
    def compute_trip_sheet_status(
        *,
        has_waybill: bool,
        is_closed: bool,
        requires_closing: bool,
    ) -> TripSheetStatus:
        if not has_waybill:
            return TripSheetStatus.MISSING

        if is_closed:
            return TripSheetStatus.CLOSED

        if requires_closing:
            return TripSheetStatus.REQUIRES_CLOSING

        return TripSheetStatus.OPEN

    @staticmethod
    def get_trip_sheet_status(driver_profile_id: str) -> TripSheetStatus:
        signals = repository.get_driver_trip_sheet_status_signals(driver_profile_id)
        has_waybill = bool(signals.get("has_waybill"))
        is_closed = bool(signals.get("is_closed"))
        requires_closing = bool(signals.get("requires_closing"))

        return DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=has_waybill,
            is_closed=is_closed,
            requires_closing=requires_closing,
        )
