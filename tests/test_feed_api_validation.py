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

    def _get(self, path: str) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, headers

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



    def test_driver_documents_crud_validation_and_list(self) -> None:
        bad_status, bad_payload, _ = self._post(
            "/api/driver/documents",
            {"profile_id": "driver-main", "type": "unknown", "number": "1", "valid_until": "bad-date"},
        )
        self.assertEqual(bad_status, 400)
        self.assertEqual(bad_payload.get("error"), "validation_error")
        self.assertIn("fields", bad_payload)

        ok_status, ok_payload, _ = self._post(
            "/api/driver/documents",
            {"profile_id": "driver-main", "type": "passport", "number": "4010 123456", "valid_until": "2030-12-31"},
        )
        self.assertEqual(ok_status, 201)
        self.assertIn("id", ok_payload)

        list_status, list_payload, _ = self._get("/api/driver/documents?profile_id=driver-main")
        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload.get("total"), 1)
        self.assertEqual(list_payload["items"][0]["id"], ok_payload["id"])

        duplicate_status, duplicate_payload, _ = self._post(
            "/api/driver/documents",
            {"profile_id": "driver-main", "type": "passport", "number": "4010 123456", "valid_until": "2030-12-31"},
        )
        self.assertEqual(duplicate_status, 409)
        self.assertEqual(duplicate_payload.get("error"), "duplicate_document")
        self.assertIn("fields", duplicate_payload)

    def test_driver_document_duplicate_check_ignores_case_and_spaces(self) -> None:
        first_status, first_payload, _ = self._post(
            "/api/driver/documents",
            {"profile_id": "driver-main", "type": "passport", "number": "AB 123 45"},
        )
        self.assertEqual(first_status, 201)
        self.assertIn("id", first_payload)

        duplicate_status, duplicate_payload, _ = self._post(
            "/api/driver/documents",
            {"profile_id": "driver-main", "type": "passport", "number": "ab12345"},
        )
        self.assertEqual(duplicate_status, 409)
        self.assertEqual(duplicate_payload.get("error"), "duplicate_document")

    def test_health_endpoint_returns_ok(self) -> None:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        conn.request("GET", "/health")
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        payload = json.loads(data) if data else {}
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()

        self.assertEqual(response.status, 200)
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("database"), "ok")
        self.assertIn("x-request-id", headers)

    def test_unexpected_error_returns_unified_json(self) -> None:
        original = repository.list_guest_feed_posts

        def _boom(limit: int, offset: int):
            raise RuntimeError("boom")

        repository.list_guest_feed_posts = _boom
        try:
            conn = HTTPConnection(self.host, self.port, timeout=5)
            conn.request("GET", "/api/feed/posts")
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            payload = json.loads(data) if data else {}
            conn.close()

            self.assertEqual(response.status, 500)
            self.assertIn("error", payload)
            self.assertEqual(payload["error"].get("code"), "internal_error")
            self.assertIn("request_id", payload["error"])
        finally:
            repository.list_guest_feed_posts = original


if __name__ == "__main__":
    unittest.main()
