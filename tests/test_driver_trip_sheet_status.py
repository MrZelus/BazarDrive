import unittest
from unittest.mock import patch

from app.models.driver_enums import TripSheetStatus
from app.services.driver_trip_sheet_service import DriverTripSheetService


class DriverTripSheetServiceTest(unittest.TestCase):
    def test_missing_when_no_waybill(self):
        status = DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=False,
            is_closed=False,
            requires_closing=False,
        )
        self.assertEqual(status, TripSheetStatus.MISSING)

    def test_open_when_waybill_exists_and_not_closed(self):
        status = DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=True,
            is_closed=False,
            requires_closing=False,
        )
        self.assertEqual(status, TripSheetStatus.OPEN)

    def test_closed_when_waybill_closed(self):
        status = DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=True,
            is_closed=True,
            requires_closing=False,
        )
        self.assertEqual(status, TripSheetStatus.CLOSED)

    def test_requires_closing_when_flagged(self):
        status = DriverTripSheetService.compute_trip_sheet_status(
            has_waybill=True,
            is_closed=False,
            requires_closing=True,
        )
        self.assertEqual(status, TripSheetStatus.REQUIRES_CLOSING)

    @patch("app.services.driver_trip_sheet_service.repository.list_driver_documents")
    @patch("app.services.driver_trip_sheet_service.repository.get_active_waybill")
    def test_get_trip_sheet_status_prioritizes_active_waybill_over_closed_history(
        self,
        mock_get_active_waybill,
        mock_list_driver_documents,
    ):
        mock_get_active_waybill.return_value = {
            "type": "waybill",
            "status": "open",
            "created_at": "2026-04-02T10:00:00Z",
        }
        mock_list_driver_documents.return_value = [
            {
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-01T10:00:00Z",
            }
        ]

        status = DriverTripSheetService.get_trip_sheet_status("driver-1")

        self.assertEqual(status, TripSheetStatus.OPEN)

    @patch("app.services.driver_trip_sheet_service.repository.list_driver_documents")
    @patch("app.services.driver_trip_sheet_service.repository.get_active_waybill")
    def test_get_trip_sheet_status_closed_when_latest_waybill_closed_and_no_active(
        self,
        mock_get_active_waybill,
        mock_list_driver_documents,
    ):
        mock_get_active_waybill.return_value = None
        mock_list_driver_documents.return_value = [
            {
                "type": "waybill",
                "status": "open",
                "created_at": "2026-03-30T09:00:00Z",
            },
            {
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-01T09:00:00Z",
            },
        ]

        status = DriverTripSheetService.get_trip_sheet_status("driver-1")

        self.assertEqual(status, TripSheetStatus.CLOSED)


if __name__ == "__main__":
    unittest.main()
