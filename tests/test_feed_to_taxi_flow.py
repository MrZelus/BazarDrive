import os
import tempfile
import unittest

from app.db import repository
from app.services.driver_operation_service import DriverOperationService


class FeedToTaxiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.previous_db_path = os.environ.get("BAZAR_DB_PATH")
        os.environ["BAZAR_DB_PATH"] = self.temp_db.name
        repository.init_db()

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("BAZAR_DB_PATH", None)
        else:
            os.environ["BAZAR_DB_PATH"] = self.previous_db_path
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_assign_order_persists_prefilled_pickup_dropoff_and_promo_note(self) -> None:
        DriverOperationService.assign_order(
            order_id="feed-card-123",
            driver_profile_id="driver-main",
            details={
                "pickup_address": "Москва, ул. Ленина, 1",
                "dropoff_address": "Москва, ул. Тверская, 10",
                "passenger_requirements": "promo=SPRING25; source=feed",
            },
        )

        records = repository.list_order_journal_records(profile_id="driver-main", limit=10)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["pickup_address"], "Москва, ул. Ленина, 1")
        self.assertEqual(records[0]["dropoff_address"], "Москва, ул. Тверская, 10")
        self.assertIn("promo=SPRING25", records[0]["passenger_requirements"])


if __name__ == "__main__":
    unittest.main()
