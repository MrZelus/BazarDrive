from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.db.repository import get_db_path


@dataclass
class DriverReminder:
    type: str
    message: str
    severity: str  # info / warning / critical
    action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "severity": self.severity,
            "action": self.action,
        }


class DriverReminderService:
    EXPIRY_WARNING_DAYS = 1
    WAYBILL_OPEN_TOO_LONG_HOURS = 12

    @classmethod
    def get_reminders(cls, profile_id: str) -> list[DriverReminder]:
        now = datetime.utcnow()
        reminders: list[DriverReminder] = []

        with closing(sqlite3.connect(get_db_path())) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT type, valid_until
                    FROM driver_documents
                    WHERE profile_id = ?
                      AND valid_until IS NOT NULL
                    """,
                    (profile_id,),
                )
                for row in cur.fetchall():
                    valid_until = str(row["valid_until"] or "").strip()
                    if not valid_until:
                        continue

                    try:
                        dt = datetime.fromisoformat(valid_until[:19])
                    except ValueError:
                        try:
                            dt = datetime.fromisoformat(valid_until[:10] + "T00:00:00")
                        except ValueError:
                            continue

                    if dt <= now:
                        reminders.append(
                            DriverReminder(
                                type="document_expired",
                                message=f"Документ {row['type']} уже просрочен",
                                severity="critical",
                                action="Обновить документы",
                            )
                        )
                    elif dt - now <= timedelta(days=cls.EXPIRY_WARNING_DAYS):
                        reminders.append(
                            DriverReminder(
                                type="document_expiring",
                                message=f"Документ {row['type']} истекает скоро",
                                severity="warning",
                                action="Проверить документы",
                            )
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
                    (profile_id,),
                )
                row = cur.fetchone()
                if row:
                    created_at = str(row["created_at"] or "").strip()
                    try:
                        created_dt = datetime.fromisoformat(created_at[:19])
                    except ValueError:
                        created_dt = None

                    if created_dt and now - created_dt > timedelta(hours=cls.WAYBILL_OPEN_TOO_LONG_HOURS):
                        reminders.append(
                            DriverReminder(
                                type="waybill_open_too_long",
                                message="Смена долго не закрыта",
                                severity="warning",
                                action="Закрыть смену",
                            )
                        )
            except sqlite3.OperationalError:
                return []

        return reminders

    @classmethod
    def get_reminders_as_dicts(cls, profile_id: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in cls.get_reminders(profile_id)]
