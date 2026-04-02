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
    def test_active_open_waybill_wins_over_historical_closed(self, mock_get_active_waybill, mock_list_driver_documents):
        mock_get_active_waybill.return_value = {
            "id": 20,
            "type": "waybill",
            "status": "open",
            "created_at": "2026-04-02 10:00:00",
        }
        mock_list_driver_documents.return_value = [
            {
                "id": 10,
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-01 18:00:00",
            },
            {
                "id": 20,
                "type": "waybill",
                "status": "open",
                "created_at": "2026-04-02 10:00:00",
            },
        ]

        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.OPEN)

    @patch("app.services.driver_trip_sheet_service.repository.list_driver_documents")
    @patch("app.services.driver_trip_sheet_service.repository.get_active_waybill")
    def test_last_waybill_closed_when_no_active_waybill(self, mock_get_active_waybill, mock_list_driver_documents):
        mock_get_active_waybill.return_value = None
        mock_list_driver_documents.return_value = [
            {
                "id": 30,
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-02 20:00:00",
            },
            {
                "id": 29,
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-01 18:00:00",
            },
        ]

        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.CLOSED)

    @patch("app.services.driver_trip_sheet_service.repository.list_driver_documents")
    @patch("app.services.driver_trip_sheet_service.repository.get_active_waybill")
    def test_fallback_uses_repository_ordering_not_raw_created_at_string_max(self, mock_get_active_waybill, mock_list_driver_documents):
        mock_get_active_waybill.return_value = None

        # Repository is expected to return docs already ordered by real datetime DESC.
        # Even if created_at strings mix formats, service should trust repository ordering
        # and take the first waybill, not run max(..., key=created_at_string).
        mock_list_driver_documents.return_value = [
            {
                "id": 41,
                "type": "waybill",
                "status": "closed",
                "created_at": "2026-04-02 10:00:00",
            },
            {
                "id": 40,
                "type": "waybill",
                "status": "open",
                "created_at": "2026-04-02T09:00:00",
            },
        ]

        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.CLOSED)


if __name__ == "__main__":
    unittest.main()
