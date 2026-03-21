import os
import sqlite3
from contextlib import closing
from typing import Any, Optional

DB_PATH_ENV_VAR = "BAZAR_DB_PATH"
DEFAULT_DB_PATH = "bot.db"


def get_db_path() -> str:
    return os.getenv(DB_PATH_ENV_VAR, DEFAULT_DB_PATH)


def init_db() -> None:
    from app.db.migrator import apply_migrations

    apply_migrations(get_db_path())


def add_user(tg_id: int, username: str, full_name: str) -> None:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO users (tg_id, username, full_name)
            VALUES (?, ?, ?)
            """,
            (tg_id, username, full_name),
        )
        conn.commit()


def create_taxi_request(user_tg_id: int, from_addr: str, to_addr: str, ride_time: str, comment: str) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO taxi_requests (user_tg_id, from_addr, to_addr, ride_time, comment)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_tg_id, from_addr, to_addr, ride_time, comment),
        )
        conn.commit()
        return cur.lastrowid


def create_ad(user_tg_id: int, title: str, text: str) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ads (user_tg_id, title, text)
            VALUES (?, ?, ?)
            """,
            (user_tg_id, title, text),
        )
        conn.commit()
        return cur.lastrowid


def create_post(user_tg_id: int, text: str) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO posts (user_tg_id, text)
            VALUES (?, ?)
            """,
            (user_tg_id, text),
        )
        conn.commit()
        return cur.lastrowid


def get_ad(ad_id: int) -> Optional[sqlite3.Row]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
        return cur.fetchone()


def get_post(post_id: int) -> Optional[sqlite3.Row]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return cur.fetchone()


def update_ad_status(ad_id: int, status: str) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE ads SET status = ? WHERE id = ?", (status, ad_id))
        conn.commit()
        return cur.rowcount > 0


def update_post_status(post_id: int, status: str) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
        conn.commit()
        return cur.rowcount > 0


def list_pending_content(limit: int = 20) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 'ad' AS kind, id, user_tg_id, title AS title, text, status, created_at
            FROM ads
            WHERE status = 'pending'
            UNION ALL
            SELECT 'post' AS kind, id, user_tg_id, '' AS title, text, status, created_at
            FROM posts
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def list_approved_posts(limit: int = 50, offset: int = 0, include_ads: bool = True) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if include_ads:
            cur.execute(
                """
                SELECT kind, id, user_tg_id, title, text, status, created_at
                FROM (
                    SELECT 'post' AS kind, id, user_tg_id, '' AS title, text, status, created_at
                    FROM posts
                    WHERE status = 'approved'
                    UNION ALL
                    SELECT 'ad' AS kind, id, user_tg_id, title, text, status, created_at
                    FROM ads
                    WHERE status = 'approved'
                )
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT 'post' AS kind, id, user_tg_id, '' AS title, text, status, created_at
                FROM posts
                WHERE status = 'approved'
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )

        return [dict(row) for row in cur.fetchall()]


def list_guest_feed_posts(limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [dict(row) for row in cur.fetchall()]


def count_guest_feed_posts() -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM guest_feed_posts")
        row = cur.fetchone()
        return int(row[0]) if row else 0


def create_guest_feed_post(author: str, text: str, image_url: Optional[str] = None, guest_profile_id: Optional[str] = None) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_feed_posts (author, text, image_url, guest_profile_id)
            VALUES (?, ?, ?, ?)
            """,
            (author, text, image_url, guest_profile_id),
        )
        conn.commit()
        new_id = cur.lastrowid

        cur.execute(
            """
            SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}


def update_guest_feed_post(post_id: int, author: str, text: str, image_url: Optional[str] = None, guest_profile_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE guest_feed_posts
            SET author = ?,
                text = ?,
                image_url = ?,
                guest_profile_id = COALESCE(?, guest_profile_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (author, text, image_url, guest_profile_id, post_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None

        conn.commit()
        cur.execute(
            """
            SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (post_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_guest_profile(
    profile_id: str,
    display_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    about: Optional[str] = None,
    role: str = "guest_author",
    status: str = "active",
    is_verified: bool = False,
) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_profiles (
                id,
                role,
                display_name,
                email,
                phone,
                about,
                is_verified,
                status,
                created_at,
                updated_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                role = excluded.role,
                display_name = excluded.display_name,
                email = excluded.email,
                phone = excluded.phone,
                about = excluded.about,
                is_verified = excluded.is_verified,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP,
                last_seen_at = CURRENT_TIMESTAMP
            """,
            (profile_id, role, display_name, email, phone, about, 1 if is_verified else 0, status),
        )
        conn.commit()

        cur.execute(
            """
            SELECT id, role, display_name, email, phone, about, is_verified, status, created_at, updated_at, last_seen_at
            FROM guest_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}


def get_guest_profile(profile_id: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, role, display_name, email, phone, about, is_verified, status, created_at, updated_at, last_seen_at
            FROM guest_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
