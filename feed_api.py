import json
import os
import time
from math import ceil
from threading import Lock
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from db import (
    count_guest_feed_posts,
    create_guest_feed_post,
    init_db,
    list_approved_posts,
    list_guest_feed_posts,
    update_guest_feed_post,
)


class FeedAPIHandler(BaseHTTPRequestHandler):
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_MAX_POSTS_PER_IP = 8
    RATE_LIMIT_MAX_POSTS_PER_AUTHOR = 5
    RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = 30

    _rate_limit_lock = Lock()
    _rate_limit_timestamps: dict[str, list[float]] = {}
    _rate_limit_expire_at: dict[str, float] = {}
    _rate_limit_last_cleanup_at = 0.0

    @staticmethod
    def _isoformat_timestamp(value: object) -> object:
        if not isinstance(value, str):
            return value

        raw = value.strip()
        if not raw:
            return raw

        normalized = raw.replace(" ", "T")
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"

        parsed: datetime | None = None
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            try:
                parsed = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                return value

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.isoformat().replace("+00:00", "Z")

    def _serialize_feed_payload(self, payload: object) -> object:
        if isinstance(payload, dict):
            serialized: dict[str, object] = {}
            for key, value in payload.items():
                if key in {"created_at", "updated_at"}:
                    serialized[key] = self._isoformat_timestamp(value)
                else:
                    serialized[key] = self._serialize_feed_payload(value)
            return serialized
        if isinstance(payload, list):
            return [self._serialize_feed_payload(item) for item in payload]
        return payload

    @staticmethod
    def _normalize_author(author: str) -> str:
        return " ".join(author.casefold().split())

    @classmethod
    def _cleanup_rate_limit_locked(cls, now: float) -> None:
        if now - cls._rate_limit_last_cleanup_at < cls.RATE_LIMIT_CLEANUP_INTERVAL_SECONDS:
            return

        expired = [key for key, expires_at in cls._rate_limit_expire_at.items() if expires_at <= now]
        for key in expired:
            cls._rate_limit_expire_at.pop(key, None)
            cls._rate_limit_timestamps.pop(key, None)

        cls._rate_limit_last_cleanup_at = now

    @classmethod
    def _consume_rate_limit_token_locked(cls, key: str, limit: int, now: float) -> int:
        window = cls.RATE_LIMIT_WINDOW_SECONDS
        cutoff = now - window
        timestamps = [stamp for stamp in cls._rate_limit_timestamps.get(key, []) if stamp > cutoff]

        if len(timestamps) >= limit:
            retry_after = max(1, int(ceil(window - (now - timestamps[0]))))
            cls._rate_limit_timestamps[key] = timestamps
            cls._rate_limit_expire_at[key] = timestamps[-1] + window
            return retry_after

        timestamps.append(now)
        cls._rate_limit_timestamps[key] = timestamps
        cls._rate_limit_expire_at[key] = now + window
        return 0

    @classmethod
    def _check_rate_limit(cls, ip: str, author: str) -> int:
        author_key = cls._normalize_author(author)
        now = time.monotonic()

        with cls._rate_limit_lock:
            cls._cleanup_rate_limit_locked(now)
            ip_retry = cls._consume_rate_limit_token_locked(
                key=f"ip:{ip}",
                limit=cls.RATE_LIMIT_MAX_POSTS_PER_IP,
                now=now,
            )
            author_retry = 0
            if author_key:
                author_retry = cls._consume_rate_limit_token_locked(
                    key=f"author:{author_key}",
                    limit=cls.RATE_LIMIT_MAX_POSTS_PER_AUTHOR,
                    now=now,
                )

        return max(ip_retry, author_retry)

    def _send_json(self, status: int, payload: dict, extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(self._serialize_feed_payload(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/feed/posts":
            params = parse_qs(parsed.query)

            def _parse_int(name: str, default: int) -> int:
                raw = params.get(name, [str(default)])[0]
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return default

            limit = _parse_int("limit", 20)
            offset = _parse_int("offset", 0)

            limit = max(1, min(100, limit))
            offset = max(0, offset)

            posts = list_guest_feed_posts(limit=limit, offset=offset)
            total = count_guest_feed_posts()
            self._send_json(
                200,
                {
                    "items": posts,
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            )
            return

        if path == "/api/feed/approved":
            posts = list_approved_posts(limit=50, offset=0, include_ads=True)
            self._send_json(200, {"items": posts})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/feed/posts":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            raw_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raw_len = 0

        raw = self.rfile.read(raw_len) if raw_len > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Некорректный JSON"})
            return

        author = str(payload.get("author", "")).strip()
        text = str(payload.get("text", "")).strip()

        if not author or not text:
            self._send_json(400, {"error": "Поля author и text обязательны"})
            return

        if len(author) > 40 or len(text) > 500:
            self._send_json(400, {"error": "Превышена максимальная длина полей"})
            return

        client_ip = self.client_address[0] if self.client_address else "unknown"
        retry_after = self._check_rate_limit(client_ip, author)
        if retry_after > 0:
            self._send_json(
                429,
                {
                    "error": "Слишком много публикаций. Пожалуйста, подождите перед следующей отправкой.",
                    "retry_after": retry_after,
                },
                extra_headers={"Retry-After": str(retry_after)},
            )
            return

        item = create_guest_feed_post(author, text)
        self._send_json(201, item)

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        prefix = "/api/feed/posts/"
        if not path.startswith(prefix):
            self._send_json(404, {"error": "Not found"})
            return

        post_id_raw = path[len(prefix) :]
        if not post_id_raw.isdigit():
            self._send_json(400, {"error": "Некорректный id поста"})
            return

        post_id = int(post_id_raw)
        if post_id <= 0:
            self._send_json(400, {"error": "Некорректный id поста"})
            return

        try:
            raw_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raw_len = 0

        raw = self.rfile.read(raw_len) if raw_len > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Некорректный JSON"})
            return

        author = str(payload.get("author", "")).strip()
        text = str(payload.get("text", "")).strip()

        if not author or not text:
            self._send_json(400, {"error": "Поля author и text обязательны"})
            return

        try:
            updated = update_guest_feed_post(post_id=post_id, author=author, text=text)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return

        if not updated:
            self._send_json(404, {"error": "Пост не найден"})
            return

        self._send_json(200, updated)


def main() -> None:
    init_db()
    host = os.getenv("FEED_API_HOST", "0.0.0.0")
    port = int(os.getenv("FEED_API_PORT", "8001"))

    server = ThreadingHTTPServer((host, port), FeedAPIHandler)
    print(f"Feed API server started on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
