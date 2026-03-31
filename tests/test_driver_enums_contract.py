import unittest

from app.models.driver_enums import (
    DocumentStatus,
    EligibilityStatus,
    OrderStatus,
    ProfileStatus,
    ShiftStatus,
    TripSheetStatus,
)


class DriverEnumsContractTest(unittest.TestCase):
    def test_profile_status_values(self):
        self.assertEqual(ProfileStatus.DRAFT.value, "draft")
        self.assertEqual(ProfileStatus.APPROVED.value, "approved")
        self.assertEqual(ProfileStatus.BLOCKED.value, "blocked")

    def test_document_status_values(self):
        self.assertEqual(DocumentStatus.MISSING.value, "missing")
        self.assertEqual(DocumentStatus.EXPIRED.value, "expired")

    def test_trip_sheet_status_values(self):
        self.assertEqual(TripSheetStatus.OPEN.value, "open")
        self.assertEqual(TripSheetStatus.CLOSED.value, "closed")

    def test_eligibility_status_values(self):
        self.assertEqual(EligibilityStatus.READY.value, "ready")
        self.assertEqual(EligibilityStatus.BLOCKED.value, "blocked")

    def test_shift_status_values(self):
        self.assertEqual(ShiftStatus.OFFLINE.value, "offline")
        self.assertEqual(ShiftStatus.BUSY.value, "busy")

    def test_order_status_values(self):
        self.assertEqual(OrderStatus.CREATED.value, "created")
        self.assertEqual(OrderStatus.DONE.value, "done")


if __name__ == "__main__":
    unittest.main()
