import os
import sqlite3
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


def _register_unicode_casefold(conn: sqlite3.Connection) -> None:
    conn.create_function(
        "unicode_casefold",
        1,
        lambda value: str(value or "").casefold(),
        deterministic=True,
    )


def _build_guest_feed_search_clause(search_query: Optional[str]) -> tuple[str, tuple[str, ...]]:
    normalized_query = str(search_query or "").strip().casefold()
    if not normalized_query:
        return "", ()
    like_pattern = f"%{normalized_query}%"
    clause = "unicode_casefold(author) LIKE ? OR unicode_casefold(text) LIKE ?"
    return clause, (like_pattern, like_pattern)


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
            SELECT id, profile_id, type, number, valid_until, file_url, status, created_at, updated_at
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
) -> dict[str, Any]:
    with closing(sqlite3.connect(get_db_path())) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO driver_documents (profile_id, type, number, valid_until, file_url, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (profile_id, type, number, valid_until, file_url, status),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status, created_at, updated_at
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
            SELECT id, profile_id, type, number, valid_until, file_url, status, created_at, updated_at
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
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (type, number, valid_until, file_url, status, doc_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        cur.execute(
            """
            SELECT id, profile_id, type, number, valid_until, file_url, status, created_at, updated_at
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
