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
        self.previous_thresholds = os.environ.get("DRIVER_REMINDER_THRESHOLDS_DAYS")
        os.environ["BAZAR_DB_PATH"] = self.temp_db.name

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("BAZAR_DB_PATH", None)
        else:
            os.environ["BAZAR_DB_PATH"] = self.previous_db_path

        if self.previous_thresholds is None:
            os.environ.pop("DRIVER_REMINDER_THRESHOLDS_DAYS", None)
        else:
            os.environ["DRIVER_REMINDER_THRESHOLDS_DAYS"] = self.previous_thresholds

        os.environ.pop("DRIVER_REMINDER_BOT_NOTIFICATIONS_ENABLED", None)
        os.environ.pop("DRIVER_REMINDER_BOT_CHAT_ID", None)

        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_get_reminders_returns_empty_without_migrations(self) -> None:
        self.assertEqual(DriverReminderService.get_reminders("driver-main"), [])

    def test_get_reminders_uses_default_thresholds(self) -> None:
        repository.init_db()
        valid_until = (datetime.utcnow() + timedelta(days=10)).isoformat()
        repository.upsert_driver_document(
            profile_id="driver-main",
            doc_type="taxi_license",
            number="taxi-license-urgent",
            valid_until=valid_until,
            status="approved",
        )

        reminders = DriverReminderService.get_reminders("driver-main")

        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0].type, "document_expiring")
        self.assertEqual(reminders[0].threshold_key, "d14")

    def test_get_reminders_uses_env_thresholds(self) -> None:
        os.environ["DRIVER_REMINDER_THRESHOLDS_DAYS"] = "21,5"
        repository.init_db()
        valid_until = (datetime.utcnow() + timedelta(days=4)).isoformat()
        repository.upsert_driver_document(
            profile_id="driver-main",
            doc_type="insurance",
            number="insurance-short",
            valid_until=valid_until,
            status="approved",
        )

        reminders = DriverReminderService.get_reminders("driver-main")

        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0].threshold_key, "d5")

    def test_get_new_reminders_deduplicates_by_threshold(self) -> None:
        repository.init_db()
        valid_until = (datetime.utcnow() + timedelta(days=6)).isoformat()
        repository.upsert_driver_document(
            profile_id="driver-main",
            doc_type="sts",
            number="sts-1",
            valid_until=valid_until,
            status="approved",
        )

        first = DriverReminderService.get_new_reminders("driver-main")
        second = DriverReminderService.get_new_reminders("driver-main")

        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].threshold_key, "d7")
        self.assertEqual(second, [])


if __name__ == "__main__":
    unittest.main()
