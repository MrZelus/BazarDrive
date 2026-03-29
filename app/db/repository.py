import os
import sqlite3
import unicodedata
from contextlib import closing
from typing import Any, Optional

DB_PATH_ENV_VAR = "BAZAR_DB_PATH"
DEFAULT_DB_PATH = "bot.db"



VERIFICATION_STATES = {"unverified", "pending_verification", "verified", "rejected", "expired"}
VERIFICATION_TRANSITIONS: dict[str, set[str]] = {
    "submit": {"unverified", "rejected", "expired"},
    "approve": {"pending_verification"},
    "reject": {"pending_verification"},
}
VERIFICATION_TARGET_STATES = {
    "submit": "pending_verification",
    "approve": "verified",
    "reject": "rejected",
}

def get_db_path() -> str:
    return os.getenv(DB_PATH_ENV_VAR, DEFAULT_DB_PATH)


def _normalize_guest_feed_search_value(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).casefold()


def _register_unicode_casefold(conn: sqlite3.Connection) -> None:
    conn.create_function(
        "unicode_casefold",
        1,
        _normalize_guest_feed_search_value,
        deterministic=True,
    )


def _build_guest_feed_search_clause(search_query: Optional[str]) -> tuple[str, tuple[str, ...]]:
    normalized_query = _normalize_guest_feed_search_value(search_query).strip()
    if not normalized_query:
        return "", ()
    clause = (
        "instr(unicode_casefold(COALESCE(author, '')), ?) > 0 "
        "OR instr(unicode_casefold(COALESCE(text, '')), ?) > 0"
    )
    return clause, (normalized_query, normalized_query)


def init_db() -> None:
    from app.db.migrator import apply_migrations

    apply_migrations(get_db_path())


def check_db_health() -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        row = cur.fetchone()
        return bool(row and row[0] == 1)


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


def list_guest_feed_posts(limit: int = 20, offset: int = 0, search_query: Optional[str] = None) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        _register_unicode_casefold(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        search_clause, search_params = _build_guest_feed_search_clause(search_query)
        if search_clause:
            cur.execute(
                """
                SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                FROM guest_feed_posts
                WHERE """
                + search_clause
                + """
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (*search_params, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                FROM guest_feed_posts
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        posts = [dict(row) for row in cur.fetchall()]
        return _attach_guest_feed_post_media(conn, posts)


def list_guest_feed_posts_by_cursor(
    limit: int = 20,
    cursor_created_at: Optional[str] = None,
    cursor_id: Optional[int] = None,
    search_query: Optional[str] = None,
) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        _register_unicode_casefold(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        search_clause, search_params = _build_guest_feed_search_clause(search_query)
        if cursor_created_at is None or cursor_id is None:
            if search_clause:
                cur.execute(
                    """
                    SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                    FROM guest_feed_posts
                    WHERE """
                    + search_clause
                    + """
                    ORDER BY datetime(created_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (*search_params, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                    FROM guest_feed_posts
                    ORDER BY datetime(created_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
        else:
            if search_clause:
                cur.execute(
                    """
                    SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                    FROM guest_feed_posts
                    WHERE ("""
                    + search_clause
                    + """)
                      AND (
                        datetime(created_at) < datetime(?)
                        OR (datetime(created_at) = datetime(?) AND id < ?)
                      )
                    ORDER BY datetime(created_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (*search_params, cursor_created_at, cursor_created_at, cursor_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
                    FROM guest_feed_posts
                    WHERE datetime(created_at) < datetime(?)
                       OR (datetime(created_at) = datetime(?) AND id < ?)
                    ORDER BY datetime(created_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (cursor_created_at, cursor_created_at, cursor_id, limit),
                )
        posts = [dict(row) for row in cur.fetchall()]
        return _attach_guest_feed_post_media(conn, posts)


def count_guest_feed_posts(search_query: Optional[str] = None) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        _register_unicode_casefold(conn)
        cur = conn.cursor()
        search_clause, search_params = _build_guest_feed_search_clause(search_query)
        if search_clause:
            cur.execute(
                "SELECT COUNT(*) FROM guest_feed_posts WHERE " + search_clause,
                search_params,
            )
        else:
            cur.execute("SELECT COUNT(*) FROM guest_feed_posts")
        row = cur.fetchone()
        return int(row[0]) if row else 0


def create_guest_feed_post(
    author: str,
    text: str,
    image_url: Optional[str] = None,
    guest_profile_id: Optional[str] = None,
    media: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
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
        new_id = cur.lastrowid
        if media:
            replace_guest_feed_post_media(post_id=new_id, media=media, conn=conn)
        conn.commit()

        cur.execute(
            """
            SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        item = dict(row) if row else {}
        return _attach_guest_feed_post_media(conn, [item])[0] if item else {}


def get_guest_feed_post(post_id: int) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, author, text, guest_profile_id, likes, image_url, created_at, updated_at
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (post_id,),
        )
        row = cur.fetchone()
        item = dict(row) if row else None
        if not item:
            return None
        return _attach_guest_feed_post_media(conn, [item])[0]


def get_guest_feed_post_owner_id(post_id: int) -> Optional[str]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT guest_profile_id
            FROM guest_feed_posts
            WHERE id = ?
            """,
            (post_id,),
        )
        row = cur.fetchone()
        return str(row[0]).strip() if row and row[0] is not None else None


def delete_guest_feed_post(post_id: int) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("DELETE FROM guest_feed_posts WHERE id = ?", (post_id,))
        conn.commit()
        return cur.rowcount > 0


def update_guest_feed_post(
    post_id: int,
    author: str,
    text: str,
    image_url: Optional[str] = None,
    guest_profile_id: Optional[str] = None,
    media: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
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
        if media is not None:
            replace_guest_feed_post_media(post_id=post_id, media=media, conn=conn)

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
        item = dict(row) if row else None
        if not item:
            return None
        return _attach_guest_feed_post_media(conn, [item])[0]


def list_guest_feed_post_media(post_id: int, conn: Optional[sqlite3.Connection] = None) -> list[dict[str, Any]]:
    owns_connection = conn is None
    target_conn = conn or sqlite3.connect(get_db_path())
    try:
        target_conn.row_factory = sqlite3.Row
        cur = target_conn.cursor()
        cur.execute(
            """
            SELECT id, post_id, media_type, url, position, created_at
            FROM guest_feed_post_media
            WHERE post_id = ?
            ORDER BY position ASC, id ASC
            """,
            (post_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        if owns_connection:
            target_conn.close()


def create_guest_feed_post_media(
    post_id: int,
    media_type: str,
    url: str,
    position: int,
    conn: Optional[sqlite3.Connection] = None,
) -> dict[str, Any]:
    owns_connection = conn is None
    target_conn = conn or sqlite3.connect(get_db_path())
    try:
        target_conn.row_factory = sqlite3.Row
        cur = target_conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_feed_post_media (post_id, media_type, url, position)
            VALUES (?, ?, ?, ?)
            """,
            (post_id, media_type, url, position),
        )
        if owns_connection:
            target_conn.commit()
        media_id = cur.lastrowid
        cur.execute(
            """
            SELECT id, post_id, media_type, url, position, created_at
            FROM guest_feed_post_media
            WHERE id = ?
            """,
            (media_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        if owns_connection:
            target_conn.close()


def delete_guest_feed_post_media(post_id: int, conn: Optional[sqlite3.Connection] = None) -> int:
    owns_connection = conn is None
    target_conn = conn or sqlite3.connect(get_db_path())
    try:
        cur = target_conn.cursor()
        cur.execute("DELETE FROM guest_feed_post_media WHERE post_id = ?", (post_id,))
        deleted_count = cur.rowcount
        if owns_connection:
            target_conn.commit()
        return deleted_count
    finally:
        if owns_connection:
            target_conn.close()


def replace_guest_feed_post_media(
    post_id: int,
    media: list[dict[str, Any]],
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict[str, Any]]:
    owns_connection = conn is None
    target_conn = conn or sqlite3.connect(get_db_path())
    try:
        delete_guest_feed_post_media(post_id=post_id, conn=target_conn)
        created: list[dict[str, Any]] = []
        for index, item in enumerate(media):
            created.append(
                create_guest_feed_post_media(
                    post_id=post_id,
                    media_type=str(item.get("media_type", "image")),
                    url=str(item.get("url", "")),
                    position=int(item.get("position", index)),
                    conn=target_conn,
                )
            )
        if owns_connection:
            target_conn.commit()
        return created
    finally:
        if owns_connection:
            target_conn.close()


def _list_guest_feed_media_for_posts(conn: sqlite3.Connection, post_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    normalized_ids = [int(post_id) for post_id in post_ids if int(post_id) > 0]
    if not normalized_ids:
        return {}
    conn.row_factory = sqlite3.Row
    placeholders = ",".join(["?"] * len(normalized_ids))
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT id, post_id, media_type, url, position, created_at
        FROM guest_feed_post_media
        WHERE post_id IN ({placeholders})
        ORDER BY post_id ASC, position ASC, id ASC
        """,
        tuple(normalized_ids),
    )
    grouped: dict[int, list[dict[str, Any]]] = {post_id: [] for post_id in normalized_ids}
    for row in cur.fetchall():
        payload = dict(row)
        grouped.setdefault(int(payload["post_id"]), []).append(payload)
    return grouped


def _attach_guest_feed_post_media(conn: sqlite3.Connection, posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not posts:
        return posts
    post_ids = [int(post.get("id", 0)) for post in posts if int(post.get("id", 0)) > 0]
    media_by_post = _list_guest_feed_media_for_posts(conn, post_ids)
    for post in posts:
        post_id = int(post.get("id", 0))
        media = media_by_post.get(post_id, [])
        if not media:
            raw_legacy_image_url = post.get("image_url")
            legacy_image_url = str(raw_legacy_image_url).strip() if raw_legacy_image_url is not None else ""
            if legacy_image_url and legacy_image_url.lower() not in {"none", "null"}:
                media = [
                    {
                        "id": 0,
                        "post_id": post_id,
                        "media_type": "image",
                        "url": legacy_image_url,
                        "position": 0,
                        "created_at": post.get("created_at"),
                    }
                ]
        post["media"] = media
    return posts




def set_guest_feed_reaction(post_id: int, guest_profile_id: str, reaction_type: str) -> None:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_feed_reactions (post_id, guest_profile_id, reaction_type)
            VALUES (?, ?, ?)
            ON CONFLICT(post_id, guest_profile_id) DO UPDATE SET
                reaction_type = excluded.reaction_type
            """,
            (post_id, guest_profile_id, reaction_type),
        )
        conn.commit()


def delete_guest_feed_reaction(post_id: int, guest_profile_id: str) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM guest_feed_reactions
            WHERE post_id = ? AND guest_profile_id = ?
            """,
            (post_id, guest_profile_id),
        )
        conn.commit()
        return cur.rowcount > 0


def aggregate_guest_feed_reactions(post_ids: list[int]) -> dict[int, dict[str, int]]:
    normalized_ids = [int(post_id) for post_id in post_ids if int(post_id) > 0]
    if not normalized_ids:
        return {}

    placeholders = ",".join(["?"] * len(normalized_ids))
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT post_id, reaction_type, COUNT(*) AS total
            FROM guest_feed_reactions
            WHERE post_id IN ({placeholders})
            GROUP BY post_id, reaction_type
            """,
            tuple(normalized_ids),
        )
        rows = cur.fetchall()

    result: dict[int, dict[str, int]] = {post_id: {} for post_id in normalized_ids}
    for row in rows:
        post_id = int(row["post_id"])
        reaction_type = str(row["reaction_type"])
        total = int(row["total"])
        result.setdefault(post_id, {})[reaction_type] = total
    return result


def get_guest_feed_my_reactions(post_ids: list[int], guest_profile_id: str) -> dict[int, str]:
    normalized_profile_id = guest_profile_id.strip()
    normalized_ids = [int(post_id) for post_id in post_ids if int(post_id) > 0]
    if not normalized_profile_id or not normalized_ids:
        return {}

    placeholders = ",".join(["?"] * len(normalized_ids))
    params = (normalized_profile_id, *normalized_ids)

    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT post_id, reaction_type
            FROM guest_feed_reactions
            WHERE guest_profile_id = ?
              AND post_id IN ({placeholders})
            """,
            params,
        )
        rows = cur.fetchall()

    return {int(row["post_id"]): str(row["reaction_type"]) for row in rows}


def get_guest_feed_post_my_reaction(post_id: int, guest_profile_id: str) -> Optional[str]:
    normalized_profile_id = guest_profile_id.strip()
    if not normalized_profile_id:
        return None

    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT reaction_type
            FROM guest_feed_reactions
            WHERE post_id = ? AND guest_profile_id = ?
            LIMIT 1
            """,
            (post_id, normalized_profile_id),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None
def list_guest_feed_comments(post_id: int, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, post_id, guest_profile_id, author, text, created_at, updated_at
            FROM guest_feed_comments
            WHERE post_id = ?
            ORDER BY datetime(created_at) ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            (post_id, limit, offset),
        )
        return [dict(row) for row in cur.fetchall()]


def count_guest_feed_comments(post_id: int) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM guest_feed_comments
            WHERE post_id = ?
            """,
            (post_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0


def create_guest_feed_comment(
    post_id: int,
    guest_profile_id: Optional[str],
    author: str,
    text: str,
) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO guest_feed_comments (post_id, guest_profile_id, author, text)
            VALUES (?, ?, ?, ?)
            """,
            (post_id, guest_profile_id, author, text),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.execute(
            """
            SELECT id, post_id, guest_profile_id, author, text, created_at, updated_at
            FROM guest_feed_comments
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}


def get_guest_feed_comment(comment_id: int) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, post_id, guest_profile_id, author, text, created_at, updated_at
            FROM guest_feed_comments
            WHERE id = ?
            """,
            (comment_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_guest_feed_comment_owner_id(comment_id: int) -> Optional[str]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT guest_profile_id
            FROM guest_feed_comments
            WHERE id = ?
            """,
            (comment_id,),
        )
        row = cur.fetchone()
        return str(row[0]).strip() if row and row[0] is not None else None


def update_guest_feed_comment(comment_id: int, text: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE guest_feed_comments
            SET text = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text, comment_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        cur.execute(
            """
            SELECT id, post_id, guest_profile_id, author, text, created_at, updated_at
            FROM guest_feed_comments
            WHERE id = ?
            """,
            (comment_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def delete_guest_feed_comment(comment_id: int) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM guest_feed_comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cur.rowcount > 0


def upsert_guest_profile(
    profile_id: str,
    display_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    about: Optional[str] = None,
    role: str = "guest_author",
    status: str = "active",
    is_verified: bool = False,
    verification_state: str | None = None,
) -> dict[str, Any]:
    normalized_state = str(verification_state or "").strip().lower()
    if not normalized_state:
        normalized_state = "verified" if is_verified else "unverified"
    if normalized_state not in VERIFICATION_STATES:
        normalized_state = "verified" if is_verified else "unverified"

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
                verification_state,
                created_at,
                updated_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                role = excluded.role,
                display_name = excluded.display_name,
                email = excluded.email,
                phone = excluded.phone,
                about = excluded.about,
                is_verified = excluded.is_verified,
                status = excluded.status,
                verification_state = excluded.verification_state,
                updated_at = CURRENT_TIMESTAMP,
                last_seen_at = CURRENT_TIMESTAMP
            """,
            (profile_id, role, display_name, email, phone, about, 1 if is_verified else 0, status, normalized_state),
        )
        conn.commit()

        cur.execute(
            """
            SELECT id, role, display_name, email, phone, about, is_verified, status, verification_state, verification_rejection_reason, verification_decided_at, verification_decided_by, created_at, updated_at, last_seen_at
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
            SELECT id, role, display_name, email, phone, about, is_verified, status, verification_state, verification_rejection_reason, verification_decided_at, verification_decided_by, created_at, updated_at, last_seen_at
            FROM guest_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None



def get_guest_profile_verification_history(profile_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, profile_id, from_state, to_state, action, reason, actor, created_at
            FROM guest_profile_verification_history
            WHERE profile_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (profile_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]


def get_guest_profile_verification_metrics(profile_id: str) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            """
            SELECT action, COUNT(*) AS total
            FROM guest_profile_verification_history
            WHERE profile_id = ?
            GROUP BY action
            ORDER BY action ASC
            """,
            (profile_id,),
        )
        actions = {str(row["action"]): int(row["total"]) for row in cur.fetchall()}

        cur.execute(
            """
            SELECT to_state, COUNT(*) AS total
            FROM guest_profile_verification_history
            WHERE profile_id = ?
            GROUP BY to_state
            ORDER BY to_state ASC
            """,
            (profile_id,),
        )
        states = {str(row["to_state"]): int(row["total"]) for row in cur.fetchall()}

        cur.execute(
            """
            SELECT COUNT(*)
            FROM guest_profile_verification_history
            WHERE profile_id = ? AND action = 'reject' AND COALESCE(TRIM(reason), '') <> ''
            """,
            (profile_id,),
        )
        rejected_with_reason = int((cur.fetchone() or [0])[0])

        cur.execute(
            """
            SELECT COUNT(*)
            FROM guest_profile_verification_history
            WHERE profile_id = ?
            """,
            (profile_id,),
        )
        total_events = int((cur.fetchone() or [0])[0])

        return {
            "profile_id": profile_id,
            "total_events": total_events,
            "actions": actions,
            "states": states,
            "rejected_with_reason": rejected_with_reason,
        }


def apply_guest_profile_verification_action(
    profile_id: str,
    action: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any] | None:
    normalized_action = str(action).strip().lower()
    if normalized_action not in VERIFICATION_TRANSITIONS:
        raise ValueError("Некорректное действие верификации")

    cleaned_reason = str(reason or "").strip() or None

    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, verification_state, is_verified
            FROM guest_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        current_state = str(row["verification_state"] or "").strip().lower() or ("verified" if row["is_verified"] else "unverified")
        allowed_from = VERIFICATION_TRANSITIONS[normalized_action]
        if current_state not in allowed_from:
            raise ValueError("Переход состояния верификации запрещён")

        if normalized_action == "reject" and not cleaned_reason:
            raise ValueError("Для отклонения требуется указать reason")

        next_state = VERIFICATION_TARGET_STATES[normalized_action]
        is_verified = 1 if next_state == "verified" else 0
        rejection_reason = cleaned_reason if normalized_action == "reject" else None

        cur.execute(
            """
            UPDATE guest_profiles
            SET verification_state = ?,
                verification_rejection_reason = ?,
                verification_decided_at = CURRENT_TIMESTAMP,
                verification_decided_by = ?,
                is_verified = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (next_state, rejection_reason, actor, is_verified, profile_id),
        )
        cur.execute(
            """
            INSERT INTO guest_profile_verification_history (profile_id, from_state, to_state, action, reason, actor)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (profile_id, current_state, next_state, normalized_action, cleaned_reason, actor),
        )
        conn.commit()

        cur.execute(
            """
            SELECT id, role, display_name, email, phone, about, is_verified, status, verification_state, verification_rejection_reason, verification_decided_at, verification_decided_by, created_at, updated_at, last_seen_at
            FROM guest_profiles
            WHERE id = ?
            """,
            (profile_id,),
        )
        updated = cur.fetchone()
        return dict(updated) if updated else None


def list_driver_documents(profile_id: str = "driver-main") -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status,
                   postshift_medical_at, postshift_medical_result, actual_return_at,
                   odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                   stops_info, notes, closed_at,
                   created_at, updated_at
            FROM driver_documents
            WHERE profile_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (profile_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def create_driver_document(
    profile_id: str,
    type: str,
    number: str,
    valid_until: Optional[str] = None,
    file_url: Optional[str] = None,
    status: str = "uploaded",
    postshift_medical_at: Optional[str] = None,
    postshift_medical_result: Optional[str] = None,
    actual_return_at: Optional[str] = None,
    odometer_end: Optional[int] = None,
    distance_km: Optional[float] = None,
    fuel_spent_liters: Optional[float] = None,
    vehicle_condition: Optional[str] = None,
    stops_info: Optional[str] = None,
    notes: Optional[str] = None,
    closed_at: Optional[str] = None,
) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO driver_documents (
                profile_id, type, number, valid_until, file_url, status,
                postshift_medical_at, postshift_medical_result, actual_return_at,
                odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                stops_info, notes, closed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id, type, number, valid_until, file_url, status,
                postshift_medical_at, postshift_medical_result, actual_return_at,
                odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                stops_info, notes, closed_at,
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status,
                   verified_by, verified_at, rejection_reason, updated_by, issued_at, is_required,
                   postshift_medical_at, postshift_medical_result, actual_return_at,
                   odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                   stops_info, notes, closed_at,
                   created_at, updated_at
            FROM driver_documents
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}


def find_driver_document_duplicate(profile_id: str, type: str, number: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status,
                   verified_by, verified_at, rejection_reason, updated_by, issued_at, is_required,
                   postshift_medical_at, postshift_medical_result, actual_return_at,
                   odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                   stops_info, notes, closed_at,
                   created_at, updated_at
            FROM driver_documents
            WHERE profile_id = ?
              AND type = ?
              AND lower(replace(number, ' ', '')) = lower(replace(?, ' ', ''))
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT 1
            """,
            (profile_id, type, number),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_driver_document(
    doc_id: int,
    type: str,
    number: str,
    valid_until: Optional[str] = None,
    file_url: Optional[str] = None,
    status: str = "uploaded",
    postshift_medical_at: Optional[str] = None,
    postshift_medical_result: Optional[str] = None,
    actual_return_at: Optional[str] = None,
    odometer_end: Optional[int] = None,
    distance_km: Optional[float] = None,
    fuel_spent_liters: Optional[float] = None,
    vehicle_condition: Optional[str] = None,
    stops_info: Optional[str] = None,
    notes: Optional[str] = None,
    closed_at: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE driver_documents
            SET type = ?,
                number = ?,
                valid_until = ?,
                file_url = ?,
                status = ?,
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
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                type, number, valid_until, file_url, status,
                postshift_medical_at, postshift_medical_result, actual_return_at,
                odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                stops_info, notes, closed_at,
                doc_id,
            ),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status,
                   verified_by, verified_at, rejection_reason, updated_by, issued_at, is_required,
                   postshift_medical_at, postshift_medical_result, actual_return_at,
                   odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                   stops_info, notes, closed_at,
                   created_at, updated_at
            FROM driver_documents
            WHERE id = ?
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def delete_driver_document(doc_id: int) -> bool:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM driver_documents WHERE id = ?", (doc_id,))
        conn.commit()
        return cur.rowcount > 0


def close_driver_waybill(doc_id: int, closure_payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, type, profile_id
            FROM driver_documents
            WHERE id = ?
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        if str(row["type"]).strip() != "waybill":
            raise ValueError("Закрытие доступно только для документов типа waybill")

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
                closed_at = COALESCE(?, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                closure_payload.get("postshift_medical_at"),
                closure_payload.get("postshift_medical_result"),
                closure_payload.get("actual_return_at"),
                closure_payload.get("odometer_end"),
                closure_payload.get("distance_km"),
                closure_payload.get("fuel_spent_liters"),
                closure_payload.get("vehicle_condition"),
                closure_payload.get("stops_info"),
                closure_payload.get("notes"),
                closure_payload.get("closed_at"),
                doc_id,
            ),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status,
                   verified_by, verified_at, rejection_reason, updated_by, issued_at, is_required,
                   postshift_medical_at, postshift_medical_result, actual_return_at,
                   odometer_end, distance_km, fuel_spent_liters, vehicle_condition,
                   stops_info, notes, closed_at,
                   created_at, updated_at
            FROM driver_documents
            WHERE id = ?
            """,
            (doc_id,),
        )
        updated = cur.fetchone()
        return dict(updated) if updated else None


def apply_driver_document_verification_action(
    doc_id: int,
    action: str,
    actor: str,
    rejection_reason: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    normalized_action = str(action).strip().lower()
    if normalized_action not in {"approve", "reject"}:
        raise ValueError("Некорректное действие верификации документа")

    cleaned_actor = str(actor).strip() or "system"
    cleaned_reason = str(rejection_reason or "").strip()
    if normalized_action == "reject" and not cleaned_reason:
        raise ValueError("Для отклонения документа укажите причину")

    target_status = "approved" if normalized_action == "approve" else "rejected"
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_documents
            WHERE id = ?
            """,
            (doc_id,),
        )
        current = cur.fetchone()
        if not current:
            return None
        if str(current["status"]).strip() != "checking":
            raise ValueError("Смена статуса разрешена только из состояния checking")

        verified_at_value = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        cur.execute(
            """
            UPDATE driver_documents
            SET status = ?,
                verified_by = ?,
                verified_at = ?,
                rejection_reason = ?,
                updated_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                target_status,
                cleaned_actor,
                verified_at_value,
                cleaned_reason if normalized_action == "reject" else None,
                cleaned_actor,
                doc_id,
            ),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        cur.execute(
            """
            SELECT *
            FROM driver_documents
            WHERE id = ?
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
from datetime import date, datetime


def get_driver_legal_profile(driver_id: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_legal_profile
            WHERE driver_id = ?
            """,
            (driver_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_driver_legal_profile(driver_id: str, payload: dict[str, Any]) -> None:
    allowed_fields = {
        "legal_entity_type",
        "inn",
        "ogrnip",
        "company_name",
        "tax_regime",
        "registration_address",
        "status",
        "status_reason",
        "approved_by",
        "approved_at",
    }
    filtered = {k: v for k, v in payload.items() if k in allowed_fields}

    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO driver_legal_profile (driver_id)
            VALUES (?)
            """,
            (driver_id,),
        )
        if filtered:
            assignments = ", ".join(f"{field} = ?" for field in filtered.keys())
            values = list(filtered.values())
            values.extend([driver_id])
            cur.execute(
                f"""
                UPDATE driver_legal_profile
                SET {assignments},
                    updated_at = CURRENT_TIMESTAMP
                WHERE driver_id = ?
                """,
                values,
            )
        conn.commit()


def get_vehicle_compliance(driver_id: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM vehicle_compliance
            WHERE driver_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (driver_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_vehicle_compliance(driver_id: str, payload: dict[str, Any]) -> None:
    allowed_fields = {
        "vehicle_id",
        "status",
        "status_reason",
        "inspection_expires_at",
        "insurance_expires_at",
        "permit_expires_at",
        "verified_by",
        "verified_at",
    }
    filtered = {k: v for k, v in payload.items() if k in allowed_fields}
    if not filtered:
        return

    columns = ", ".join(["driver_id", *filtered.keys()])
    placeholders = ", ".join(["?", *(["?"] * len(filtered))])
    values = [driver_id, *filtered.values()]

    update_assignments = ", ".join(f"{field} = excluded.{field}" for field in filtered.keys())

    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO vehicle_compliance ({columns})
            VALUES ({placeholders})
            ON CONFLICT(driver_id) DO UPDATE SET
                {update_assignments},
                updated_at = CURRENT_TIMESTAMP
            """,
            values,
        )
        conn.commit()


def create_compliance_check(driver_id: str, payload: dict[str, Any]) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO compliance_checks (
                driver_id,
                check_type,
                status,
                block_reason,
                details,
                checked_by,
                checked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                driver_id,
                payload.get("check_type"),
                payload.get("status", "queued"),
                payload.get("block_reason"),
                payload.get("details"),
                payload.get("checked_by"),
                payload.get("checked_at"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_compliance_checks(driver_id: str, status: Optional[str] = None) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if status:
            cur.execute(
                """
                SELECT *
                FROM compliance_checks
                WHERE driver_id = ? AND status = ?
                ORDER BY datetime(created_at) DESC, id DESC
                """,
                (driver_id, status),
            )
        else:
            cur.execute(
                """
                SELECT *
                FROM compliance_checks
                WHERE driver_id = ?
                ORDER BY datetime(created_at) DESC, id DESC
                """,
                (driver_id,),
            )
        return [dict(row) for row in cur.fetchall()]


def get_driver_compliance_profile(profile_id: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_compliance_profiles
            WHERE profile_id = ?
            """,
            (profile_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_driver_compliance_profile(profile_id: str, payload: dict[str, Any]) -> None:
    allowed_fields = {
        "last_name",
        "first_name",
        "middle_name",
        "phone",
        "email",
        "driver_license_category",
        "driving_experience_years",
        "has_medical_contraindications",
        "criminal_record_cleared",
        "unpaid_fines_count",
        "employment_type",
        "inn",
        "ogrnip",
        "registration_date",
        "tax_regime",
        "activity_region",
        "vehicle_make",
        "vehicle_model",
        "vehicle_license_plate",
        "has_checker_pattern",
        "has_roof_light",
        "has_taximeter",
        "two_factor_enabled",
        "compliance_status",
        "compliance_reason",
    }
    filtered = {k: v for k, v in payload.items() if k in allowed_fields}
    if not filtered:
        return

    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO driver_compliance_profiles (profile_id)
            VALUES (?)
            """,
            (profile_id,),
        )

        assignments = ", ".join(f"{field} = ?" for field in filtered.keys())
        values = list(filtered.values())
        values.extend([profile_id])

        cur.execute(
            f"""
            UPDATE driver_compliance_profiles
            SET {assignments},
                updated_at = CURRENT_TIMESTAMP
            WHERE profile_id = ?
            """,
            values,
        )
        conn.commit()


def list_driver_documents(profile_id: str) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_documents
            WHERE profile_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (profile_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_driver_document(profile_id: str, doc_type: str) -> Optional[dict[str, Any]]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_documents
            WHERE profile_id = ? AND type = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id, doc_type),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_driver_document(
    profile_id: str,
    doc_type: str,
    number: str,
    valid_until: Optional[str] = None,
    file_url: Optional[str] = None,
    status: str = "uploaded",
    issued_at: Optional[str] = None,
    rejection_reason: Optional[str] = None,
    verified_by: Optional[str] = None,
    verified_at: Optional[str] = None,
    is_required: int = 1,
    updated_by: Optional[str] = None,
) -> int:
    existing = get_driver_document(profile_id, doc_type)

    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()

        if existing:
            cur.execute(
                """
                UPDATE driver_documents
                SET number = ?,
                    valid_until = ?,
                    file_url = ?,
                    status = ?,
                    issued_at = ?,
                    rejection_reason = ?,
                    verified_by = ?,
                    verified_at = ?,
                    is_required = ?,
                    updated_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    number,
                    valid_until,
                    file_url,
                    status,
                    issued_at,
                    rejection_reason,
                    verified_by,
                    verified_at,
                    is_required,
                    updated_by,
                    existing["id"],
                ),
            )
            conn.commit()
            return int(existing["id"])

        cur.execute(
            """
            INSERT INTO driver_documents (
                profile_id,
                type,
                number,
                valid_until,
                file_url,
                status,
                issued_at,
                rejection_reason,
                verified_by,
                verified_at,
                is_required,
                updated_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                doc_type,
                number,
                valid_until,
                file_url,
                status,
                issued_at,
                rejection_reason,
                verified_by,
                verified_at,
                is_required,
                updated_by,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_active_waybill(profile_id: str, target_date: Optional[str] = None) -> Optional[dict[str, Any]]:
    target_date = target_date or date.today().isoformat()
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM driver_documents
            WHERE profile_id = ?
              AND type = 'waybill'
              AND status = 'open'
              AND (
                COALESCE(valid_until, '') = ''
                OR substr(valid_until, 1, 10) >= ?
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id, target_date),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_driver_compliance_status(profile_id: str, status: str, reason: str) -> None:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO driver_compliance_profiles (
                profile_id,
                compliance_status,
                compliance_reason
            )
            VALUES (?, ?, ?)
            """,
            (profile_id, status, reason),
        )
        cur.execute(
            """
            UPDATE driver_compliance_profiles
            SET compliance_status = ?,
                compliance_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE profile_id = ?
            """,
            (status, reason, profile_id),
        )
        conn.commit()


def create_order_journal_record(payload: dict[str, Any]) -> int:
    with closing(sqlite3.connect(get_db_path())) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO order_journal_records (
                order_number,
                source_request_id,
                order_status,
                event_at,
                accepted_at,
                completed_at,
                pickup_address,
                dropoff_address,
                vehicle_make,
                vehicle_model,
                vehicle_license_plate,
                driver_full_name,
                eta_planned,
                arrived_at_actual,
                ride_completed_at_actual,
                order_source,
                passenger_phone,
                passenger_requirements,
                profile_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("order_number"),
                payload.get("source_request_id"),
                payload.get("order_status"),
                payload.get("event_at"),
                payload.get("accepted_at"),
                payload.get("completed_at"),
                payload.get("pickup_address"),
                payload.get("dropoff_address"),
                payload.get("vehicle_make"),
                payload.get("vehicle_model"),
                payload.get("vehicle_license_plate"),
                payload.get("driver_full_name"),
                payload.get("eta_planned"),
                payload.get("arrived_at_actual"),
                payload.get("ride_completed_at_actual"),
                payload.get("order_source"),
                payload.get("passenger_phone"),
                payload.get("passenger_requirements"),
                payload.get("profile_id"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_order_journal_records(
    profile_id: str,
    *,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    normalized_limit = max(1, min(int(limit), 200))
    normalized_offset = max(0, int(offset))
    clauses = ["profile_id = ?"]
    values: list[Any] = [profile_id]

    if status:
        clauses.append("order_status = ?")
        values.append(status)
    if date_from:
        clauses.append("substr(COALESCE(event_at, created_at), 1, 10) >= ?")
        values.append(date_from)
    if date_to:
        clauses.append("substr(COALESCE(event_at, created_at), 1, 10) <= ?")
        values.append(date_to)

    where_clause = " AND ".join(clauses)
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT *
            FROM order_journal_records
            WHERE {where_clause}
            ORDER BY COALESCE(event_at, created_at) DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*values, normalized_limit, normalized_offset),
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]
