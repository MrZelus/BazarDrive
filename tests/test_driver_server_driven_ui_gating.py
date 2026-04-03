import unittest

from tests import test_feed_api_validation as feed_api_validation


class DriverServerDrivenUiGatingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        feed_api_validation.FeedAPIValidationTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls) -> None:
        feed_api_validation.FeedAPIValidationTests.tearDownClass.__func__(cls)

    def setUp(self) -> None:
        feed_api_validation.FeedAPIValidationTests.setUp(self)

    def tearDown(self) -> None:
        feed_api_validation.FeedAPIValidationTests.tearDown(self)

    def _get(self, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        return feed_api_validation.FeedAPIValidationTests._get(self, path, headers)

    def _post(self, path: str, payload: dict, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        return feed_api_validation.FeedAPIValidationTests._post(self, path, payload, headers)

    def _seed_driver_ready_profile(self, profile_id: str = "driver-main") -> None:
        feed_api_validation.FeedAPIValidationTests._seed_driver_ready_profile(self, profile_id)

    def test_summary_red_when_trip_sheet_missing(self) -> None:
        status, payload, _ = self._get("/api/driver/summary?profile_id=driver-main")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("level"), "red")
        self.assertIn("Нет открытого путевого листа", payload.get("problems", []))
        self.assertIn("Открыть смену", payload.get("actions", []))

    def test_summary_green_when_driver_ready(self) -> None:
        self._seed_driver_ready_profile("driver-main")
        open_status, _, _ = self._post(
            "/api/driver/shift/open",
            {"profile_id": "driver-main", "vehicle_condition": "Исправен"},
        )
        self.assertEqual(open_status, 200)

        status, payload, _ = self._get("/api/driver/summary?profile_id=driver-main")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("level"), "green")
        self.assertEqual(payload.get("title"), "✅ Можно работать")
        self.assertEqual(payload.get("actions"), [])

    def test_go_online_block_payload_contains_corrective_actions(self) -> None:
        profile_id = "driver-waybill-block"
        self._seed_driver_ready_profile(profile_id)

        status, payload, _ = self._post("/api/driver/go-online", {"profile_id": profile_id})
        self.assertEqual(status, 403)
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("code"), "WAYBILL_REQUIRED")
        self.assertEqual(payload.get("reason"), "Нет открытого путевого листа")
        self.assertEqual(payload.get("actions"), ["Открыть смену"])

    def test_order_done_is_terminal_in_journal_surface(self) -> None:
        self._seed_driver_ready_profile("driver-main")
        open_status, _, _ = self._post(
            "/api/driver/shift/open",
            {"profile_id": "driver-main", "vehicle_condition": "Исправен"},
        )
        self.assertEqual(open_status, 200)

        order_id = 20001
        self._post(
            "/api/driver/assign-order",
            {
                "profile_id": "driver-main",
                "order_id": order_id,
                "pickup_address": "Москва, ул. Ленина, 1",
                "dropoff_address": "Москва, ул. Тверская, 10",
            },
        )
        self._post("/api/driver/accept-order", {"profile_id": "driver-main", "order_id": order_id})
        complete_status, complete_payload, _ = self._post(
            "/api/driver/complete-order",
            {
                "profile_id": "driver-main",
                "order_id": order_id,
                "pickup_address": "Москва, ул. Ленина, 1",
                "dropoff_address": "Москва, ул. Тверская, 10",
            },
        )

        self.assertEqual(complete_status, 200)
        self.assertEqual(complete_payload.get("status"), "done")
        self.assertEqual(complete_payload.get("order_status"), "done")

    def test_order_canceled_is_terminal_in_journal_surface(self) -> None:
        self._seed_driver_ready_profile("driver-main")
        open_status, _, _ = self._post(
            "/api/driver/shift/open",
            {"profile_id": "driver-main", "vehicle_condition": "Исправен"},
        )
        self.assertEqual(open_status, 200)

        order_id = 20002
        cancel_status, cancel_payload, _ = self._post(
            "/api/driver/cancel-order",
            {
                "profile_id": "driver-main",
                "order_id": order_id,
                "pickup_address": "Москва, пр. Мира, 2",
                "dropoff_address": "Москва, пр. Мира, 20",
            },
        )

        self.assertEqual(cancel_status, 200)
        self.assertEqual(cancel_payload.get("status"), "canceled")
        self.assertEqual(cancel_payload.get("order_status"), "canceled")


if __name__ == "__main__":
    unittest.main()
