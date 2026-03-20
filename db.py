import sqlite3
from contextlib import closing
from typing import Any, Optional
from urllib.parse import urlparse

DB_PATH = "bot.db"
MAX_GUEST_FEED_IMAGE_URL_LENGTH = 2048


def _validate_guest_feed_image_url(image_url: Optional[str]) -> Optional[str]:
    if image_url is None:
        return None

    image_url_clean = image_url.strip()
    if not image_url_clean:
        return None

    if len(image_url_clean) > MAX_GUEST_FEED_IMAGE_URL_LENGTH:
        raise ValueError(
            f"Ссылка на изображение слишком длинная (максимум {MAX_GUEST_FEED_IMAGE_URL_LENGTH} символов)"
        )

    parsed = urlparse(image_url_clean)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Некорректный формат image_url: поддерживаются только http/https URL")

    return image_url_clean


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS taxi_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER,
                from_addr TEXT,
                to_addr TEXT,
                ride_time TEXT,
                comment TEXT,
                status TEXT DEFAULT 'new',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER,
                title TEXT,
                text TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_tg_id INTEGER,
                text TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_feed_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                text TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
            """
        )

        cur.execute("PRAGMA table_info(guest_feed_posts)")
        guest_feed_columns = {row[1] for row in cur.fetchall()}
        if "updated_at" not in guest_feed_columns:
            cur.execute("ALTER TABLE guest_feed_posts ADD COLUMN updated_at DATETIME")
        if "image_url" not in guest_feed_columns:
            cur.execute("ALTER TABLE guest_feed_posts ADD COLUMN image_url TEXT")

        conn.commit()


def add_user(tg_id: int, username: str, full_name: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
        return cur.fetchone()


def get_post(post_id: int) -> Optional[sqlite3.Row]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return cur.fetchone()


def update_ad_status(ad_id: int, status: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE ads SET status = ? WHERE id = ?", (status, ad_id))
        conn.commit()
        return cur.rowcount > 0


def update_post_status(post_id: int, status: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
        conn.commit()
        return cur.rowcount > 0


def list_pending_content(limit: int = 20) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
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




def list_approved_posts(
    limit: int = 50,
    offset: int = 0,
    include_ads: bool = True,
) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
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
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, author, text, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [dict(row) for row in cur.fetchall()]


def count_guest_feed_posts() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM guest_feed_posts")
        row = cur.fetchone()
        return int(row[0]) if row else 0


def create_guest_feed_post(author: str, text: str, image_url: Optional[str] = None) -> dict[str, Any]:
    image_url_clean = _validate_guest_feed_image_url(image_url)

    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_feed_posts (author, text, image_url)
            VALUES (?, ?, ?)
            """,
            (author, text, image_url_clean),
        )
        conn.commit()
        new_id = cur.lastrowid

        cur.execute(
            """
            SELECT id, author, text, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}


def update_guest_feed_post(
    post_id: int, author: str, text: str, image_url: Optional[str] = None
) -> Optional[dict[str, Any]]:
    author_clean = author.strip()
    text_clean = text.strip()
    image_url_clean = _validate_guest_feed_image_url(image_url)

    if len(author_clean) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")
    if len(text_clean) < 5:
        raise ValueError("Сообщение должно содержать минимум 5 символов")
    if len(author_clean) > 40 or len(text_clean) > 500:
        raise ValueError("Превышена максимальная длина полей")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE guest_feed_posts
            SET author = ?, text = ?, image_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (author_clean, text_clean, image_url_clean, post_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None

        conn.commit()
        cur.execute(
            """
            SELECT id, author, text, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (post_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
