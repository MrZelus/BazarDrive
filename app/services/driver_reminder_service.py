from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil
from typing import Any, Callable

from app.db.repository import get_db_path


@dataclass
class DriverReminder:
    type: str
    message: str
    severity: str  # info / warning / critical
    action: str | None = None
    threshold_key: str | None = None
    entity_key: str | None = None
    last_notified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "severity": self.severity,
            "action": self.action,
            "threshold_key": self.threshold_key,
            "entity_key": self.entity_key,
            "last_notified_at": self.last_notified_at,
        }


class DriverReminderService:
    DEFAULT_EXPIRY_WARNING_THRESHOLDS_DAYS = (30, 14, 7, 1)
    WAYBILL_OPEN_TOO_LONG_HOURS = 12

    @classmethod
    def _parse_thresholds(cls) -> tuple[int, ...]:
        raw = os.getenv("DRIVER_REMINDER_THRESHOLDS_DAYS", "")
        if not raw.strip():
            return cls.DEFAULT_EXPIRY_WARNING_THRESHOLDS_DAYS

        values: list[int] = []
        for item in raw.split(","):
            token = item.strip()
            if not token:
                continue
            try:
                day = int(token)
            except ValueError:
                continue
            if day > 0:
                values.append(day)

        if not values:
            return cls.DEFAULT_EXPIRY_WARNING_THRESHOLDS_DAYS

        return tuple(sorted(set(values), reverse=True))

    @classmethod
    def _resolve_threshold_key(cls, delta: timedelta) -> str | None:
        total_seconds = delta.total_seconds()
        if total_seconds <= 0:
            return None

        days_left = max(1, ceil(total_seconds / 86400))
        for threshold in sorted(cls._parse_thresholds()):
            if days_left <= threshold:
                return f"d{threshold}"

        return None

    @staticmethod
    def _normalize_datetime(raw_value: str) -> datetime | None:
        normalized = str(raw_value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.fromisoformat(normalized[:19])
        except ValueError:
            try:
                return datetime.fromisoformat(normalized[:10] + "T00:00:00")
            except ValueError:
                return None

    @classmethod
    def _load_last_notifications(cls, conn: sqlite3.Connection, profile_id: str) -> dict[tuple[str, str, str], str]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT reminder_type, entity_key, threshold_key, last_notified_at
            FROM driver_reminder_notifications
            WHERE profile_id = ?
            """,
            (profile_id,),
        )
        return {
            (str(row["reminder_type"]), str(row["entity_key"]), str(row["threshold_key"])): str(row["last_notified_at"])
            for row in cur.fetchall()
        }

    @classmethod
    def _upsert_notification_log(cls, conn: sqlite3.Connection, profile_id: str, reminder: DriverReminder) -> None:
        if not reminder.entity_key or not reminder.threshold_key:
            return

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO driver_reminder_notifications (
                profile_id,
                reminder_type,
                entity_key,
                threshold_key,
                last_notified_at
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(profile_id, reminder_type, entity_key, threshold_key)
            DO UPDATE SET
                last_notified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """,
            (profile_id, reminder.type, reminder.entity_key, reminder.threshold_key),
        )

    @classmethod
    def _collect_document_reminders(
        cls,
        conn: sqlite3.Connection,
        profile_id: str,
        now: datetime,
        notifications_map: dict[tuple[str, str, str], str],
    ) -> list[DriverReminder]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type, valid_until
            FROM driver_documents
            WHERE profile_id = ?
              AND valid_until IS NOT NULL
            """,
            (profile_id,),
        )
        reminders: list[DriverReminder] = []
        for row in cur.fetchall():
            doc_type = str(row["type"])
            dt = cls._normalize_datetime(str(row["valid_until"] or ""))
            if not dt:
                continue

            entity_key = f"document:{doc_type}"
            if dt <= now:
                threshold_key = "expired"
                reminders.append(
                    DriverReminder(
                        type="document_expired",
                        message=f"Документ {doc_type} уже просрочен",
                        severity="critical",
                        action="Обновить документы",
                        threshold_key=threshold_key,
                        entity_key=entity_key,
                        last_notified_at=notifications_map.get(("document_expired", entity_key, threshold_key)),
                    )
                )
                continue

            delta = dt - now
            threshold_key = cls._resolve_threshold_key(delta)
            if not threshold_key:
                continue

            days_left = max(1, ceil(delta.total_seconds() / 86400))
            reminders.append(
                DriverReminder(
                    type="document_expiring",
                    message=f"Документ {doc_type} истекает через {days_left} дн.",
                    severity="warning",
                    action="Проверить документы",
                    threshold_key=threshold_key,
                    entity_key=entity_key,
                    last_notified_at=notifications_map.get(("document_expiring", entity_key, threshold_key)),
                )
            )

        return reminders

    @classmethod
    def _collect_waybill_reminder(
        cls,
        conn: sqlite3.Connection,
        profile_id: str,
        now: datetime,
        notifications_map: dict[tuple[str, str, str], str],
    ) -> list[DriverReminder]:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, created_at
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
        if not row:
            return []

        created_dt = cls._normalize_datetime(str(row["created_at"] or ""))
        if not created_dt or now - created_dt <= timedelta(hours=cls.WAYBILL_OPEN_TOO_LONG_HOURS):
            return []

        entity_key = f"waybill:{int(row['id'])}"
        threshold_key = "h12"
        return [
            DriverReminder(
                type="waybill_open_too_long",
                message="Смена долго не закрыта",
                severity="warning",
                action="Закрыть смену",
                threshold_key=threshold_key,
                entity_key=entity_key,
                last_notified_at=notifications_map.get(("waybill_open_too_long", entity_key, threshold_key)),
            )
        ]

    @classmethod
    def get_reminders(cls, profile_id: str) -> list[DriverReminder]:
        now = datetime.utcnow()

        with closing(sqlite3.connect(get_db_path())) as conn:
            conn.row_factory = sqlite3.Row
            try:
                notifications_map = cls._load_last_notifications(conn, profile_id)
                reminders = cls._collect_document_reminders(conn, profile_id, now, notifications_map)
                reminders.extend(cls._collect_waybill_reminder(conn, profile_id, now, notifications_map))
                return reminders
            except sqlite3.OperationalError:
                return []

    @classmethod
    def get_new_reminders(cls, profile_id: str) -> list[DriverReminder]:
        reminders = cls.get_reminders(profile_id)
        fresh = [item for item in reminders if not item.last_notified_at]
        if not fresh:
            return []

        with closing(sqlite3.connect(get_db_path())) as conn:
            try:
                for reminder in fresh:
                    cls._upsert_notification_log(conn, profile_id, reminder)
                conn.commit()
            except sqlite3.OperationalError:
                conn.rollback()
                return []

        return fresh

    @classmethod
    def get_reminders_as_dicts(cls, profile_id: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in cls.get_reminders(profile_id)]

    @classmethod
    def send_new_reminders_to_bot(
        cls,
        profile_id: str,
        sender: Callable[[int, str], None],
    ) -> int:
        enabled = os.getenv("DRIVER_REMINDER_BOT_NOTIFICATIONS_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        chat_id_raw = os.getenv("DRIVER_REMINDER_BOT_CHAT_ID", "").strip()
        if not enabled or not chat_id_raw:
            return 0

        try:
            chat_id = int(chat_id_raw)
        except ValueError:
            return 0

        reminders = cls.get_new_reminders(profile_id)
        for reminder in reminders:
            sender(chat_id, f"🔔 [{profile_id}] {reminder.message}")
        return len(reminders)
