import unittest

from app.models.driver_enums import EligibilityStatus, OrderStatus, ProfileStatus
from app.models.driver_error_codes import DriverErrorCode
from app.services.driver_permissions_service import DriverPermissionsService


class DriverPermissionsContractTest(unittest.TestCase):
    def test_driver_cannot_edit_foreign_profile(self):
        result = DriverPermissionsService.can_edit_profile(
            actor_id="driver-1",
            owner_id="driver-2",
            is_admin=False,
        )
        self.assertFalse(result.is_allowed)
        self.assertEqual(result.error_code, DriverErrorCode.OWNERSHIP_REQUIRED.value)

    def test_driver_cannot_go_online_when_blocked(self):
        result = DriverPermissionsService.can_go_online(
            actor_id="driver-1",
            owner_id="driver-1",
            eligibility_status=EligibilityStatus.READY,
            profile_status=ProfileStatus.BLOCKED,
            is_admin=False,
        )
        self.assertFalse(result.is_allowed)
        self.assertEqual(result.error_code, DriverErrorCode.PROFILE_BLOCKED.value)

    def test_driver_can_accept_created_order_when_ready(self):
        result = DriverPermissionsService.can_accept_order(
            actor_id="driver-1",
            owner_id="driver-1",
            eligibility_status=EligibilityStatus.READY,
            order_status=OrderStatus.CREATED,
            is_admin=False,
        )
        self.assertTrue(result.is_allowed)

    def test_driver_cannot_accept_non_created_order(self):
        result = DriverPermissionsService.can_accept_order(
            actor_id="driver-1",
            owner_id="driver-1",
            eligibility_status=EligibilityStatus.READY,
            order_status=OrderStatus.ACCEPTED,
            is_admin=False,
        )
        self.assertFalse(result.is_allowed)
        self.assertEqual(
            result.error_code,
            DriverErrorCode.INVALID_ORDER_TRANSITION.value,
        )


if __name__ == "__main__":
    unittest.main()
