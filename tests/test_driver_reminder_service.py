import os
import tempfile
import unittest
from datetime import datetime, timedelta

from app.db import repository
from app.services.driver_reminder_service import DriverReminderService


class DriverReminderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.previous_db_path = os.environ.get("BAZAR_DB_PATH")
        os.environ["BAZAR_DB_PATH"] = self.temp_db.name

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("BAZAR_DB_PATH", None)
        else:
            os.environ["BAZAR_DB_PATH"] = self.previous_db_path
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_get_reminders_returns_empty_without_migrations(self) -> None:
        self.assertEqual(DriverReminderService.get_reminders("driver-main"), [])

    def test_get_reminders_returns_document_expiring_warning(self) -> None:
        repository.init_db()
        valid_until = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        repository.upsert_driver_document(
            profile_id="driver-main",
            doc_type="taxi_license",
            number="taxi-license-urgent",
            valid_until=valid_until,
            status="approved",
        )

        reminders = DriverReminderService.get_reminders("driver-main")

        reminder_types = {item.type for item in reminders}
        self.assertIn("document_expiring", reminder_types)


if __name__ == "__main__":
    unittest.main()
