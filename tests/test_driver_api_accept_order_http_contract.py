import unittest
from unittest.mock import patch

from app.api.http_handlers import FeedAPIHandler


class _HandlerHarness:
    def __init__(self):
        self.handler = object.__new__(FeedAPIHandler)
        self.sent = []
        self.handler._send_json = self._send_json
        self.handler._require_permission = lambda permission: True

    def _send_json(self, status, payload, extra_headers=None):
        self.sent.append((status, payload, extra_headers))


class DriverAcceptOrderHttpContractTest(unittest.TestCase):
    def test_accept_order_missing_order_id_returns_canonical_error(self):
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_accept_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "order_id_required")

    @patch("app.api.http_handlers.DriverOperationService.accept_order")
    def test_accept_order_blocked_returns_canonical_error_shape(self, accept_order):
        accept_order.return_value = {
            "ok": False,
            "code": "driver_not_eligible",
            "reason": "Нельзя принимать заказы",
            "actions": ["Заполнить профиль"],
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main", "order_id": 123}, None, 200)

        harness.handler._handle_driver_accept_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "driver_not_eligible")
        self.assertEqual(payload["error"]["actions"], ["Заполнить профиль"])

    @patch("app.api.http_handlers.DriverOperationService.accept_order")
    def test_accept_order_success_returns_canonical_success_shape(self, accept_order):
        accept_order.return_value = {
            "ok": True,
            "order_id": 123,
            "status": "accepted",
            "order_status": "accepted",
            "event_name": "order_accepted",
            "notification_plan": {"channels": ["telegram", "in_app"]},
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main", "order_id": 123}, None, 200)

        harness.handler._handle_driver_accept_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["order_id"], 123)
        self.assertEqual(payload["order_status"], "accepted")
        self.assertEqual(payload["event_name"], "order_accepted")
        self.assertIn("notification_plan", payload)


if __name__ == "__main__":
    unittest.main()
