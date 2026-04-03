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


class DriverShiftHttpContractTest(unittest.TestCase):
    @patch("app.api.http_handlers.WaybillService.open_shift")
    def test_shift_open_success_returns_canonical_success_shape(self, open_shift):
        open_shift.return_value = 15
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main", "vehicle_condition": "ok"}, None, 200)

        harness.handler._handle_driver_shift_open()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["waybill_id"], 15)
        self.assertEqual(payload["trip_sheet_status"], "open")
        self.assertEqual(payload["event_name"], "trip_sheet_opened")

    @patch("app.api.http_handlers.WaybillService.open_shift")
    def test_shift_open_conflict_returns_canonical_error(self, open_shift):
        open_shift.side_effect = ValueError("already open")
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main", "vehicle_condition": "ok"}, None, 200)

        harness.handler._handle_driver_shift_open()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 409)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "shift_open_conflict")

    @patch("app.api.http_handlers.FeedService.validate_waybill_close_payload")
    def test_shift_close_validation_returns_canonical_error(self, validate_waybill_close_payload):
        validate_waybill_close_payload.return_value = ({}, {"odometer_end": "required"})
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main"}, None, 200)

        harness.handler._handle_driver_shift_close()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["fields"]["odometer_end"], "required")

    @patch("app.api.http_handlers.FeedService.validate_waybill_close_payload")
    @patch("app.api.http_handlers.WaybillService.close_shift")
    def test_shift_close_success_returns_canonical_success_shape(self, close_shift, validate_waybill_close_payload):
        validate_waybill_close_payload.return_value = ({"odometer_end": 100}, {})
        close_shift.return_value = 15
        harness = _HandlerHarness()
        harness.handler._parse_feed_request_payload = lambda: ({"profile_id": "driver-main", "odometer_end": 100}, None, 200)

        harness.handler._handle_driver_shift_close()

        status, payload, _ = harness.sent[-1]
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["waybill_id"], 15)
        self.assertEqual(payload["trip_sheet_status"], "closed")
        self.assertEqual(payload["event_name"], "trip_sheet_closed")


if __name__ == "__main__":
    unittest.main()
