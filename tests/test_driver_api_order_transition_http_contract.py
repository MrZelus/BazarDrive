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


class DriverOrderTransitionHttpContractTest(unittest.TestCase):
    def test_complete_order_missing_order_id_returns_canonical_error(self):
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_complete_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "order_id_required")

    @patch("app.api.http_handlers.DriverOperationService.complete_order")
    def test_complete_order_success_returns_canonical_success_shape(self, complete_order):
        complete_order.return_value = {
            "ok": True,
            "order_id": 123,
            "status": "done",
            "order_status": "done",
            "event_name": "order_done",
            "notification_plan": {"channels": ["telegram", "in_app"]},
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: (
            {"profile_id": "driver-main", "order_id": 123},
            None,
            200,
        )

        harness.handler._handle_driver_complete_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["order_id"], 123)
        self.assertEqual(payload["order_status"], "done")
        self.assertEqual(payload["status"], "done")
        self.assertEqual(payload["event_name"], "order_done")

    def test_cancel_order_missing_order_id_returns_canonical_error(self):
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_cancel_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "order_id_required")

    @patch("app.api.http_handlers.DriverOperationService.cancel_order")
    def test_cancel_order_success_returns_canonical_success_shape(self, cancel_order):
        cancel_order.return_value = {
            "ok": True,
            "order_id": 123,
            "status": "canceled",
            "order_status": "canceled",
            "event_name": "order_canceled",
            "notification_plan": {"channels": ["telegram", "in_app"]},
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: (
            {"profile_id": "driver-main", "order_id": 123},
            None,
            200,
        )

        harness.handler._handle_driver_cancel_order()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["order_id"], 123)
        self.assertEqual(payload["order_status"], "canceled")
        self.assertEqual(payload["status"], "canceled")
        self.assertEqual(payload["event_name"], "order_canceled")


if __name__ == "__main__":
    unittest.main()
