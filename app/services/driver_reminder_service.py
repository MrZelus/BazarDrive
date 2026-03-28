from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from typing import Any

from app.db.repository import get_db_path


class DriverReminderService:
    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    @staticmethod
    def get_reminders(profile_id: str) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        reminders: list[dict[str, Any]] = []

        normalized_profile_id = str(profile_id or "driver-main").strip() or "driver-main"

        with closing(sqlite3.connect(get_db_path())) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                """
                SELECT type, valid_until
                FROM driver_documents
                WHERE profile_id = ?
                  AND valid_until IS NOT NULL
                """,
                (normalized_profile_id,),
            )

            for row in cur.fetchall():
                valid_until_dt = DriverReminderService._parse_datetime(row["valid_until"])
                if not valid_until_dt:
                    continue

                delta = valid_until_dt - now
                if timedelta(seconds=0) <= delta < timedelta(days=1):
                    reminders.append(
                        {
                            "type": "document_expiring",
                            "message": f"{row['type']} истекает скоро",
                        }
                    )

            cur.execute(
                """
                SELECT created_at
                FROM driver_documents
                WHERE profile_id = ?
                  AND type = 'waybill'
                  AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_profile_id,),
            )

            waybill_row = cur.fetchone()
            if waybill_row:
                created_at = DriverReminderService._parse_datetime(waybill_row["created_at"])
                if created_at and now - created_at > timedelta(hours=12):
                    reminders.append(
                        {
                            "type": "waybill_open_too_long",
                            "message": "Смена не закрыта",
                        }
                    )

        return reminders
