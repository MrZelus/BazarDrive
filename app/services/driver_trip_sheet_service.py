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
        active_waybill = repository.get_active_waybill(driver_profile_id)
        documents = repository.list_driver_documents(driver_profile_id)

        has_waybill = active_waybill is not None or any(
            doc.get("type") == "waybill" for doc in documents
        )

        is_closed = any(
            doc.get("type") == "waybill" and doc.get("status") == "closed"
            for doc in documents
        )

        # TODO:
        # replace this with a real backend signal when the project
        # defines the exact closure-required condition.
        requires_closing = False

        return DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=has_waybill,
            is_closed=is_closed,
            requires_closing=requires_closing,
        )
