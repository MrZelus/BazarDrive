import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from db import (
    count_guest_feed_posts,
    create_guest_feed_post,
    init_db,
    list_approved_posts,
    list_guest_feed_posts,
)


class FeedAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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

        item = create_guest_feed_post(author, text)
        self._send_json(201, item)


def main() -> None:
    init_db()
    host = os.getenv("FEED_API_HOST", "0.0.0.0")
    port = int(os.getenv("FEED_API_PORT", "8001"))

    server = ThreadingHTTPServer((host, port), FeedAPIHandler)
    print(f"Feed API server started on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
