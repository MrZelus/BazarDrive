import unittest

from app.models.driver_enums import OrderStatus, ProfileStatus
from app.models.driver_error_codes import DriverErrorCode
from app.services.driver_status_service import DriverStatusService


class DriverStatusTransitionsContractTest(unittest.TestCase):
    def test_profile_draft_to_incomplete_allowed(self):
        result = DriverStatusService.validate_profile_transition(
            ProfileStatus.DRAFT,
            ProfileStatus.INCOMPLETE,
        )
        self.assertTrue(result.is_allowed)
        self.assertIsNone(result.error_code)

    def test_profile_draft_to_approved_forbidden(self):
        result = DriverStatusService.validate_profile_transition(
            ProfileStatus.DRAFT,
            ProfileStatus.APPROVED,
        )
        self.assertFalse(result.is_allowed)
        self.assertEqual(
            result.error_code,
            DriverErrorCode.INVALID_PROFILE_TRANSITION.value,
        )

    def test_order_created_to_accepted_allowed(self):
        result = DriverStatusService.validate_order_transition(
            OrderStatus.CREATED,
            OrderStatus.ACCEPTED,
        )
        self.assertTrue(result.is_allowed)

    def test_order_accepted_to_done_forbidden(self):
        result = DriverStatusService.validate_order_transition(
            OrderStatus.ACCEPTED,
            OrderStatus.DONE,
        )
        self.assertFalse(result.is_allowed)
        self.assertEqual(
            result.error_code,
            DriverErrorCode.INVALID_ORDER_TRANSITION.value,
        )


if __name__ == "__main__":
    unittest.main()
