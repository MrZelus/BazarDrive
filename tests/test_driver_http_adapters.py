import unittest

from app.api.driver_http_adapters import (
    adapt_accept_order_result,
    adapt_go_online_result,
    adapt_missing_order_id_error,
    adapt_shift_close_invalid,
    adapt_shift_close_success,
    adapt_shift_open_conflict,
    adapt_shift_open_success,
    adapt_waybill_validation_error,
)


class DriverHttpAdaptersTest(unittest.TestCase):
    def test_adapt_go_online_blocked(self):
        status, payload = adapt_go_online_result(
            {
                "ok": False,
                "code": "trip_sheet_required",
                "reason": "Нет открытого путевого листа",
                "actions": ["Открыть смену"],
            }
        )
        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "trip_sheet_required")

    def test_adapt_go_online_success(self):
        status, payload = adapt_go_online_result(
            {
                "ok": True,
                "status": "online",
                "shift_status": "online",
                "event_name": "shift_online",
            }
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["shift_status"], "online")

    def test_adapt_accept_order_success(self):
        status, payload = adapt_accept_order_result(
            {
                "ok": True,
                "order_id": 10,
                "status": "accepted",
                "order_status": "accepted",
                "event_name": "order_accepted",
            },
            order_id=10,
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["order_status"], "accepted")
        self.assertEqual(payload["event_name"], "order_accepted")

    def test_missing_order_id_error(self):
        status, payload = adapt_missing_order_id_error()
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "order_id_required")

    def test_shift_open_success(self):
        status, payload = adapt_shift_open_success(15)
        self.assertEqual(status, 200)
        self.assertEqual(payload["trip_sheet_status"], "open")

    def test_shift_close_success(self):
        status, payload = adapt_shift_close_success(15)
        self.assertEqual(status, 200)
        self.assertEqual(payload["trip_sheet_status"], "closed")

    def test_shift_open_conflict(self):
        status, payload = adapt_shift_open_conflict("already open")
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "shift_open_conflict")

    def test_shift_close_invalid(self):
        status, payload = adapt_shift_close_invalid("not found")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "trip_sheet_close_invalid")

    def test_waybill_validation_error(self):
        status, payload = adapt_waybill_validation_error({"odometer_end": "required"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["fields"]["odometer_end"], "required")


if __name__ == "__main__":
    unittest.main()
