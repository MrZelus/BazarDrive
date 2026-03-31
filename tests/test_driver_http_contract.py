import unittest

from app.api.driver_http_contract import (
    driver_error_payload,
    driver_go_online_success_payload,
    driver_order_success_payload,
    driver_shift_success_payload,
    driver_validation_error_payload,
)


class DriverHttpContractTest(unittest.TestCase):
    def test_driver_error_payload_shape(self):
        payload = driver_error_payload(
            code="trip_sheet_required",
            message="Нет допуска к выходу на линию",
            reason="Нет открытого путевого листа",
            actions=["Открыть смену"],
        )
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "trip_sheet_required")
        self.assertEqual(payload["error"]["reason"], "Нет открытого путевого листа")
        self.assertEqual(payload["error"]["actions"], ["Открыть смену"])

    def test_go_online_success_payload_shape(self):
        payload = driver_go_online_success_payload(
            status="online",
            shift_status="online",
            event_name="shift_online",
            notification_plan={"channels": ["in_app"]},
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "online")
        self.assertEqual(payload["shift_status"], "online")
        self.assertEqual(payload["event_name"], "shift_online")
        self.assertIn("notification_plan", payload)

    def test_order_success_payload_shape(self):
        payload = driver_order_success_payload(
            order_id=123,
            status="accepted",
            order_status="accepted",
            event_name="order_accepted",
            notification_plan={"channels": ["telegram", "in_app"]},
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["order_id"], 123)
        self.assertEqual(payload["order_status"], "accepted")
        self.assertEqual(payload["event_name"], "order_accepted")

    def test_shift_success_payload_shape(self):
        payload = driver_shift_success_payload(
            waybill_id=15,
            trip_sheet_status="closed",
            event_name="trip_sheet_closed",
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["waybill_id"], 15)
        self.assertEqual(payload["trip_sheet_status"], "closed")
        self.assertEqual(payload["event_name"], "trip_sheet_closed")

    def test_validation_error_payload_shape(self):
        payload = driver_validation_error_payload(fields={"vehicle_condition": "required"})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["fields"]["vehicle_condition"], "required")


if __name__ == "__main__":
    unittest.main()
