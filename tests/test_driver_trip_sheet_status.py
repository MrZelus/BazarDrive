import unittest

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


if __name__ == "__main__":
    unittest.main()
