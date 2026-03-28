from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Optional

from app.db.repository import get_db_path


class WaybillService:
    @staticmethod
    def _expire_outdated_open_waybills(profile_id: str, conn: sqlite3.Connection) -> None:
        updated_at = datetime.utcnow().isoformat()
        conn.execute(
            """
            UPDATE driver_documents
            SET status = 'expired',
                closed_at = COALESCE(closed_at, ?),
                updated_at = ?
            WHERE profile_id = ?
              AND type = 'waybill'
              AND status = 'open'
              AND COALESCE(valid_until, '') != ''
              AND substr(valid_until, 1, 10) < date('now')
            """,
            (updated_at, updated_at, profile_id),
        )

    @staticmethod
    def open_shift(profile_id: str, vehicle_condition: str) -> int:
        normalized_profile_id = str(profile_id or "driver-main").strip() or "driver-main"
        normalized_vehicle_condition = str(vehicle_condition or "").strip() or None

        with closing(sqlite3.connect(get_db_path())) as conn:
            WaybillService._expire_outdated_open_waybills(normalized_profile_id, conn)
            cur = conn.cursor()

            cur.execute(
                """
                SELECT id
                FROM driver_documents
                WHERE profile_id = ?
                  AND type = 'waybill'
                  AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_profile_id,),
            )

            if cur.fetchone():
                raise ValueError("Смена уже открыта")

            created_at = datetime.utcnow().isoformat()
            waybill_number = f"WB-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

            cur.execute(
                """
                INSERT INTO driver_documents (
                    profile_id,
                    type,
                    number,
                    status,
                    vehicle_condition,
                    created_at,
                    updated_at
                )
                VALUES (?, 'waybill', ?, 'open', ?, ?, ?)
                """,
                (
                    normalized_profile_id,
                    waybill_number,
                    normalized_vehicle_condition,
                    created_at,
                    created_at,
                ),
            )

            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def close_shift(profile_id: str, data: dict[str, Any]) -> int:
        normalized_profile_id = str(profile_id or "driver-main").strip() or "driver-main"

        with closing(sqlite3.connect(get_db_path())) as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT id
                FROM driver_documents
                WHERE profile_id = ?
                  AND type = 'waybill'
                  AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_profile_id,),
            )

            row = cur.fetchone()
            if not row:
                raise ValueError("Нет открытого путевого листа")

            waybill_id = int(row[0])
            closed_at = datetime.utcnow().isoformat()

            cur.execute(
                """
                UPDATE driver_documents
                SET status = 'closed',
                    postshift_medical_at = ?,
                    postshift_medical_result = ?,
                    actual_return_at = ?,
                    odometer_end = ?,
                    distance_km = ?,
                    fuel_spent_liters = ?,
                    vehicle_condition = ?,
                    stops_info = ?,
                    notes = ?,
                    closed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    data.get("postshift_medical_at"),
                    data.get("postshift_medical_result"),
                    data.get("actual_return_at"),
                    data.get("odometer_end"),
                    data.get("distance_km"),
                    data.get("fuel_spent_liters"),
                    data.get("vehicle_condition"),
                    data.get("stops_info"),
                    data.get("notes"),
                    closed_at,
                    closed_at,
                    waybill_id,
                ),
            )

            conn.commit()
            return waybill_id

    @staticmethod
    def get_active_waybill(profile_id: str) -> Optional[dict[str, Any]]:
        normalized_profile_id = str(profile_id or "driver-main").strip() or "driver-main"

        with closing(sqlite3.connect(get_db_path())) as conn:
            WaybillService._expire_outdated_open_waybills(normalized_profile_id, conn)
            conn.commit()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM driver_documents
                WHERE profile_id = ?
                  AND type = 'waybill'
                  AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_profile_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
