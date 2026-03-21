import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from app.api.http_handlers import FeedAPIHandler
from app.db import repository
from app.services.feed_service import FeedService


class FeedAPIValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FeedAPIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.previous_db_path = os.environ.get("BAZAR_DB_PATH")
        os.environ["BAZAR_DB_PATH"] = self.temp_db.name
        repository.init_db()

        FeedService._rate_limit_timestamps.clear()
        FeedService._rate_limit_expire_at.clear()
        FeedService._rate_limit_last_cleanup_at = 0.0

        self.old_ip_limit = FeedService.RATE_LIMIT_MAX_POSTS_PER_IP
        self.old_author_limit = FeedService.RATE_LIMIT_MAX_POSTS_PER_AUTHOR
        FeedService.RATE_LIMIT_MAX_POSTS_PER_IP = 100
        FeedService.RATE_LIMIT_MAX_POSTS_PER_AUTHOR = 1

    def tearDown(self) -> None:
        FeedService.RATE_LIMIT_MAX_POSTS_PER_IP = self.old_ip_limit
        FeedService.RATE_LIMIT_MAX_POSTS_PER_AUTHOR = self.old_author_limit

        if self.previous_db_path is None:
            os.environ.pop("BAZAR_DB_PATH", None)
        else:
            os.environ["BAZAR_DB_PATH"] = self.previous_db_path
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def _post(self, path: str, payload: dict) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, headers

    def test_profile_validation_returns_400(self) -> None:
        status, payload, _ = self._post("/api/feed/profiles", {"id": "short", "display_name": "A"})
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_post_validation_returns_400_for_invalid_author_and_image(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {"author": "A", "text": "abcd", "image_url": "ftp://broken.example/img.jpg"},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_post_creation_201_and_rate_limit_429(self) -> None:
        ok_status, ok_payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Valid Author",
                "text": "Это валидный текст публикации",
                "image_base64": "aGVsbG8=",
                "image_mime_type": "image/png",
            },
        )
        self.assertEqual(ok_status, 201)
        self.assertIn("id", ok_payload)
        self.assertTrue(str(ok_payload.get("image_url", "")).startswith("/uploads/feed/"))

        limited_status, limited_payload, limited_headers = self._post(
            "/api/feed/posts",
            {
                "author": "Valid Author",
                "text": "Вторая попытка с тем же автором должна попасть под лимит",
                "image_url": "https://example.com/image.png",
            },
        )
        self.assertEqual(limited_status, 429)
        self.assertIn("retry_after", limited_payload)
        self.assertIn("retry-after", limited_headers)


if __name__ == "__main__":
    unittest.main()
