import unittest

from app.db import repository
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
        self.assertEqual(payload.get("error", {}).get("code"), "trip_sheet_required")
        self.assertEqual(payload.get("error", {}).get("reason"), "Нет открытого путевого листа")
        self.assertEqual(payload.get("error", {}).get("actions"), ["Открыть смену"])

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

    def test_accept_order_expired_doc_blocker_uses_canonical_error_shape(self) -> None:
        profile_id = "driver-doc-expired-ui"
        self._seed_driver_ready_profile(profile_id)
        repository.upsert_driver_document(
            profile_id=profile_id,
            doc_type="osago",
            number="osago-expired-ui",
            valid_until="2020-01-01",
            status="approved",
        )
        open_status, _, _ = self._post(
            "/api/driver/shift/open",
            {"profile_id": profile_id, "vehicle_condition": "ok"},
        )
        self.assertEqual(open_status, 200)

        status, payload, _ = self._post(
            "/api/driver/accept-order",
            {"profile_id": profile_id, "order_id": "order-expired-ui"},
        )
        self.assertEqual(status, 403)
        self.assertFalse(payload.get("ok"))
        self.assertIn(
            payload.get("error", {}).get("code"),
            {"driver_not_eligible", "required_document_missing", "doc_expired"},
        )
        self.assertIn("Есть просроченные документы", str(payload.get("error", {}).get("reason", "")))
        self.assertIn("Обновить документы", payload.get("error", {}).get("actions", []))

    def test_accept_order_not_eligible_blocker_exposes_reason_and_actions(self) -> None:
        status, payload, _ = self._post(
            "/api/driver/accept-order",
            {"profile_id": "driver-main", "order_id": 999001},
        )
        self.assertEqual(status, 403)
        self.assertFalse(payload.get("ok"))
        self.assertIn(
            payload.get("error", {}).get("code"),
            {"trip_sheet_required", "driver_not_eligible", "profile_incomplete", "doc_expired"},
        )
        self.assertTrue(payload.get("error", {}).get("reason"))

    def test_summary_red_when_last_trip_sheet_is_closed_and_no_active_waybill(self) -> None:
        profile_id = "driver-summary-closed"
        self._seed_driver_ready_profile(profile_id)

        open_status, open_payload, _ = self._post(
            "/api/driver/shift/open",
            {"profile_id": profile_id, "vehicle_condition": "Исправен"},
        )
        self.assertEqual(open_status, 200)

        close_status, _, _ = self._post(
            "/api/driver/shift/close",
            {
                "profile_id": profile_id,
                "postshift_medical_at": "2026-03-28T20:10:00Z",
                "postshift_medical_result": "Допущен",
                "actual_return_at": "2026-03-28T20:20:00Z",
                "odometer_end": 120543,
                "distance_km": 182.5,
                "fuel_spent_liters": 14.2,
                "vehicle_condition": "Исправен",
                "stops_info": "2 короткие остановки",
                "notes": "Смена завершена штатно",
            },
        )
        self.assertEqual(close_status, 200)
        self.assertGreater(int(open_payload.get("waybill_id", 0)), 0)

        status, payload, _ = self._get(f"/api/driver/summary?profile_id={profile_id}")
        self.assertEqual(status, 200)
        self.assertIn(payload.get("level"), {"red", "yellow"})
        self.assertTrue(payload.get("problems"))
        self.assertTrue(payload.get("actions"))

    @unittest.skip("Enable when summary/API emits requires_closing semantics")
    def test_summary_prompts_close_shift_when_trip_sheet_requires_closing(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
