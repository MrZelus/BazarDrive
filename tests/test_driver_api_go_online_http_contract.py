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


class DriverGoOnlineHttpContractTest(unittest.TestCase):
    @patch("app.api.http_handlers.DriverOperationService.go_online")
    def test_go_online_blocked_returns_canonical_error_shape(self, go_online):
        go_online.return_value = {
            "ok": False,
            "code": "trip_sheet_required",
            "reason": "Нет открытого путевого листа",
            "actions": ["Открыть смену"],
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_go_online()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "trip_sheet_required")
        self.assertEqual(payload["error"]["reason"], "Нет открытого путевого листа")
        self.assertEqual(payload["error"]["actions"], ["Открыть смену"])

    @patch("app.api.http_handlers.DriverOperationService.go_online")
    def test_go_online_success_returns_canonical_success_shape(self, go_online):
        go_online.return_value = {
            "ok": True,
            "status": "online",
            "shift_status": "online",
            "event_name": "shift_online",
            "notification_plan": {"channels": ["in_app"]},
        }
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_go_online()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "online")
        self.assertEqual(payload["shift_status"], "online")
        self.assertEqual(payload["event_name"], "shift_online")
        self.assertIn("notification_plan", payload)


if __name__ == "__main__":
    unittest.main()
