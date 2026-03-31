import unittest
from unittest.mock import patch

from app.models.driver_enums import OrderStatus, ShiftStatus
from app.models.driver_events import DriverEvent
from app.services.driver_operation_service import DriverOperationService


class DriverOperationContractIntegrationTest(unittest.TestCase):
    @patch("app.services.driver_operation_service.DriverGuardService.ensure_can_go_online")
    def test_go_online_returns_canonical_fields(self, ensure_can_go_online):
        ensure_can_go_online.return_value = object()
        result = DriverOperationService.go_online("driver-1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["shift_status"], ShiftStatus.ONLINE.value)
        self.assertEqual(result["event_name"], DriverEvent.SHIFT_ONLINE.value)

    @patch("app.services.driver_operation_service.DriverGuardService.ensure_can_accept_order")
    @patch("app.services.driver_operation_service.repository.create_order_journal_record")
    def test_accept_order_returns_canonical_fields(self, create_order_journal_record, ensure_can_accept_order):
        ensure_can_accept_order.return_value = object()
        result = DriverOperationService.accept_order(order_id=123, driver_profile_id="driver-1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["order_status"], OrderStatus.ACCEPTED.value)
        self.assertEqual(result["event_name"], DriverEvent.ORDER_ACCEPTED.value)
        create_order_journal_record.assert_called_once()


if __name__ == "__main__":
    unittest.main()
