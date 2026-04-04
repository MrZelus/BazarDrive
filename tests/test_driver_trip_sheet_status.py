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

    @patch("app.services.driver_trip_sheet_service.repository.get_driver_trip_sheet_status_signals")
    def test_get_trip_sheet_status_missing(self, mock_get_signals):
        mock_get_signals.return_value = {
            "has_waybill": False,
            "is_closed": False,
            "requires_closing": False,
        }
        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.MISSING)

    @patch("app.services.driver_trip_sheet_service.repository.get_driver_trip_sheet_status_signals")
    def test_get_trip_sheet_status_open(self, mock_get_signals):
        mock_get_signals.return_value = {
            "has_waybill": True,
            "is_closed": False,
            "requires_closing": False,
        }
        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.OPEN)

    @patch("app.services.driver_trip_sheet_service.repository.get_driver_trip_sheet_status_signals")
    def test_get_trip_sheet_status_requires_closing(self, mock_get_signals):
        mock_get_signals.return_value = {
            "has_waybill": True,
            "is_closed": False,
            "requires_closing": True,
        }
        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.REQUIRES_CLOSING)

    @patch("app.services.driver_trip_sheet_service.repository.get_driver_trip_sheet_status_signals")
    def test_get_trip_sheet_status_closed(self, mock_get_signals):
        mock_get_signals.return_value = {
            "has_waybill": True,
            "is_closed": True,
            "requires_closing": False,
        }
        status = DriverTripSheetService.get_trip_sheet_status("driver-main")
        self.assertEqual(status, TripSheetStatus.CLOSED)


if __name__ == "__main__":
    unittest.main()
