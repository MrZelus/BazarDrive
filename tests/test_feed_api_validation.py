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
        os.environ.pop("APP_ENV", None)
        os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        os.environ.pop("API_AUTH_KEYS", None)
        os.environ.pop("API_AUTH_BEARER_TOKENS", None)

    def _get(self, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        conn.request("GET", path, headers=headers or {})
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, headers

    def _post(self, path: str, payload: dict, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        conn.request("POST", path, body=body, headers=request_headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, headers

    def _post_raw(self, path: str, body: bytes, headers: dict[str, str]) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        response_headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, response_headers

    def _patch(self, path: str, payload: dict, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        conn.request("PATCH", path, body=body, headers=request_headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        response_headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, response_headers

    def _delete(self, path: str, payload: dict, headers: dict[str, str] | None = None) -> tuple[int, dict, dict]:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        conn.request("DELETE", path, body=body, headers=request_headers)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        response_headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, parsed, response_headers

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

    def test_request_payload_too_large_returns_413(self) -> None:
        previous_limit = os.environ.get("MAX_REQUEST_BYTES")
        os.environ["MAX_REQUEST_BYTES"] = "64"
        try:
            body = json.dumps(
                {
                    "author": "Valid Author",
                    "text": "Это валидный текст, который превышает лимит в 64 байта",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            status, payload, _ = self._post_raw(
                "/api/feed/posts",
                body=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
            )
            self.assertEqual(status, 413)
            self.assertIn("error", payload)
            self.assertEqual(payload["error"].get("code"), "payload_too_large")
            self.assertEqual(payload["error"].get("max_request_bytes"), 64)
            self.assertIn("request_id", payload["error"])
        finally:
            if previous_limit is None:
                os.environ.pop("MAX_REQUEST_BYTES", None)
            else:
                os.environ["MAX_REQUEST_BYTES"] = previous_limit



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

    def test_driver_documents_payload_too_large_returns_413(self) -> None:
        previous_limit = os.environ.get("MAX_REQUEST_BYTES")
        os.environ["MAX_REQUEST_BYTES"] = "96"
        try:
            body = json.dumps(
                {
                    "profile_id": "driver-main",
                    "type": "passport",
                    "number": "4010 123456",
                    "valid_until": "2030-12-31",
                    "issued_by": "X" * 500,
                },
                ensure_ascii=False,
            ).encode("utf-8")
            status, payload, _ = self._post_raw(
                "/api/driver/documents",
                body=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
            )
            self.assertEqual(status, 413)
            self.assertEqual(payload.get("error", {}).get("code"), "payload_too_large")
            self.assertEqual(payload.get("error", {}).get("max_request_bytes"), 96)
        finally:
            if previous_limit is None:
                os.environ.pop("MAX_REQUEST_BYTES", None)
            else:
                os.environ["MAX_REQUEST_BYTES"] = previous_limit

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

    def test_publication_rules_endpoint_returns_structured_rules(self) -> None:
        status, payload, _ = self._get("/api/feed/publication-rules")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("version"), 1)
        self.assertIsInstance(payload.get("rules"), list)
        self.assertGreaterEqual(len(payload["rules"]), 3)

    def test_prod_requires_auth_for_write_endpoints(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["API_AUTH_KEYS"] = "secret-key"
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"

        status, payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Текст без авторизации должен быть отклонён"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload.get("error", {}).get("code"), "unauthorized")
        self.assertIn("request_id", payload.get("error", {}))

        authed_status, _, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Текст с авторизацией должен быть принят"},
            headers={"X-API-Key": "secret-key"},
        )
        self.assertEqual(authed_status, 201)

    def test_prod_supports_bearer_auth_for_write_endpoints(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["API_AUTH_BEARER_TOKENS"] = "prod-token"

        status, payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Проверка bearer auth"},
            headers={"Authorization": "Bearer prod-token"},
        )
        self.assertEqual(status, 201)
        self.assertIn("id", payload)

    def test_prod_blocks_non_whitelisted_origin(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["API_AUTH_KEYS"] = "secret-key"
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"

        status, payload, _ = self._get("/api/feed/posts", headers={"Origin": "https://evil.example.com"})
        self.assertEqual(status, 403)
        self.assertEqual(payload.get("error", {}).get("code"), "forbidden_origin")

        allowed_status, _, headers = self._get("/api/feed/posts", headers={"Origin": "https://app.example.com"})
        self.assertEqual(allowed_status, 200)
        self.assertEqual(headers.get("access-control-allow-origin"), "https://app.example.com")

    def test_dev_keeps_wildcard_cors(self) -> None:
        os.environ["APP_ENV"] = "dev"
        status, _, headers = self._get("/api/feed/posts", headers={"Origin": "https://any.example.com"})
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("access-control-allow-origin"), "*")

    def test_post_rejected_by_content_moderation_rules(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Valid Author",
                "text": "Казино и ставки здесь запрещены, но текст содержит стоп-слово",
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("правилами публикации", payload.get("error", ""))

    def test_post_rejected_by_spam_like_repeated_tokens(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Valid Author",
                "text": "скидка скидка скидка скидка скидка очень выгодно",
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload.get("error"), "Пост выглядит как спам: слишком много повторяющихся слов.")

    def test_comments_crud_happy_path(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Текст публикации для комментариев"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        create_status, create_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/comments",
            {"guest_profile_id": "guest-0001", "author": "Комментатор", "text": "Первый комментарий"},
        )
        self.assertEqual(create_status, 201)
        self.assertEqual(create_payload["post_id"], post_id)
        comment_id = create_payload["id"]

        list_status, list_payload, _ = self._get(f"/api/feed/posts/{post_id}/comments")
        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload["total"], 1)
        self.assertEqual(list_payload["items"][0]["id"], comment_id)

        patch_status, patch_payload, _ = self._patch(
            f"/api/feed/posts/{post_id}/comments/{comment_id}",
            {"guest_profile_id": "guest-0001", "text": "Обновлённый комментарий"},
        )
        self.assertEqual(patch_status, 200)
        self.assertEqual(patch_payload["text"], "Обновлённый комментарий")

        delete_status, delete_payload, _ = self._delete(
            f"/api/feed/posts/{post_id}/comments/{comment_id}",
            {"guest_profile_id": "guest-0001"},
        )
        self.assertEqual(delete_status, 200)
        self.assertTrue(delete_payload["ok"])

        list_after_delete_status, list_after_delete_payload, _ = self._get(f"/api/feed/posts/{post_id}/comments")
        self.assertEqual(list_after_delete_status, 200)
        self.assertEqual(list_after_delete_payload["items"], [])

    def test_comments_negative_400_403_404(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Базовый пост для негативных сценариев комментариев"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        not_found_post_status, _, _ = self._post(
            "/api/feed/posts/999999/comments",
            {"guest_profile_id": "guest-0001", "author": "Автор", "text": "text"},
        )
        self.assertEqual(not_found_post_status, 404)

        bad_request_status, bad_request_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/comments",
            {"guest_profile_id": "guest-0001", "author": "Автор", "text": "   "},
        )
        self.assertEqual(bad_request_status, 400)
        self.assertIn("error", bad_request_payload)

        create_status, create_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/comments",
            {"guest_profile_id": "guest-0001", "author": "Комментатор", "text": "Комментарий автора"},
        )
        self.assertEqual(create_status, 201)
        comment_id = create_payload["id"]

        forbidden_patch_status, _, _ = self._patch(
            f"/api/feed/posts/{post_id}/comments/{comment_id}",
            {"guest_profile_id": "guest-9999", "text": "Попытка изменить чужой комментарий"},
        )
        self.assertEqual(forbidden_patch_status, 403)

        forbidden_delete_status, _, _ = self._delete(
            f"/api/feed/posts/{post_id}/comments/{comment_id}",
            {"guest_profile_id": "guest-9999"},
        )
        self.assertEqual(forbidden_delete_status, 403)

        not_found_comment_status, _, _ = self._patch(
            f"/api/feed/posts/{post_id}/comments/999999",
            {"guest_profile_id": "guest-0001", "text": "missing"},
        )
        self.assertEqual(not_found_comment_status, 404)

    def test_delete_post_by_author_success_with_comment_cascade(self) -> None:
        created_post = repository.create_guest_feed_post(
            author="Post Author",
            text="Пост для удаления автором",
            guest_profile_id="guest-author-001",
        )
        post_id = created_post["id"]
        repository.create_guest_feed_comment(
            post_id=post_id,
            guest_profile_id="guest-author-001",
            author="Post Author",
            text="Комментарий будет удалён каскадом",
        )

        delete_status, delete_payload, _ = self._delete(
            f"/api/feed/posts/{post_id}",
            {"guest_profile_id": "guest-author-001"},
        )
        self.assertEqual(delete_status, 200)
        self.assertTrue(delete_payload.get("ok"))
        self.assertIsNone(repository.get_guest_feed_post(post_id))
        self.assertEqual(repository.list_guest_feed_comments(post_id=post_id), [])

    def test_delete_post_by_foreign_user_returns_403(self) -> None:
        created_post = repository.create_guest_feed_post(
            author="Owner",
            text="Чужой пост",
            guest_profile_id="guest-owner-001",
        )
        post_id = created_post["id"]

        status, payload, _ = self._delete(
            f"/api/feed/posts/{post_id}",
            {"guest_profile_id": "guest-other-001"},
        )
        self.assertEqual(status, 403)
        self.assertIn("error", payload)

    def test_delete_post_not_found_returns_404(self) -> None:
        status, payload, _ = self._delete(
            "/api/feed/posts/999999",
            {"guest_profile_id": "guest-author-001"},
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload.get("error"), "Пост не найден")

    def test_delete_post_invalid_id_returns_400(self) -> None:
        status, payload, _ = self._delete(
            "/api/feed/posts/not-a-number",
            {"guest_profile_id": "guest-author-001"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload.get("error"), "Некорректный id поста")

    def test_delete_post_by_moderator_success(self) -> None:
        repository.upsert_guest_profile(
            profile_id="guest-mod-001",
            display_name="Moderator",
            email="mod@example.com",
            role="moderator",
        )
        created_post = repository.create_guest_feed_post(
            author="Owner",
            text="Пост для удаления модератором",
            guest_profile_id="guest-owner-001",
        )
        post_id = created_post["id"]

        status, payload, _ = self._delete(
            f"/api/feed/posts/{post_id}",
            {"guest_profile_id": "guest-mod-001"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload.get("ok"))
        self.assertIsNone(repository.get_guest_feed_post(post_id))

    def test_delete_post_requires_auth_in_prod(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"
        os.environ["API_AUTH_KEYS"] = "secret-key"
        created_post = repository.create_guest_feed_post(
            author="Owner",
            text="Пост для проверки auth",
            guest_profile_id="guest-owner-001",
        )

        status, payload, _ = self._delete(
            f"/api/feed/posts/{created_post['id']}",
            {"guest_profile_id": "guest-owner-001"},
            headers={"Origin": "https://app.example.com"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload.get("error", {}).get("code"), "unauthorized")


    def test_reactions_happy_path_and_idempotency(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Пост для реакций"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        first_status, first_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-1", "type": "like"},
        )
        self.assertEqual(first_status, 200)
        self.assertEqual(first_payload["my_reaction"], "like")
        self.assertEqual(first_payload["likes"], 1)

        second_status, second_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-1", "type": "like"},
        )
        self.assertEqual(second_status, 200)
        self.assertEqual(second_payload["likes"], 1)

        replace_status, replace_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-1", "type": "dislike"},
        )
        self.assertEqual(replace_status, 200)
        self.assertEqual(replace_payload["my_reaction"], "dislike")
        self.assertEqual(replace_payload["likes"], 0)
        self.assertEqual(replace_payload["reactions"].get("dislike"), 1)

        list_status, list_payload, _ = self._get(f"/api/feed/posts?guest_profile_id=guest-react-1")
        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload["items"][0]["my_reaction"], "dislike")
        self.assertEqual(list_payload["items"][0]["likes"], 0)

        delete_status, delete_payload, _ = self._delete(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-1"},
        )
        self.assertEqual(delete_status, 200)
        self.assertIsNone(delete_payload["my_reaction"])
        self.assertEqual(delete_payload["reactions"], {})

    def test_reactions_negative_invalid_and_not_found(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Пост для негативных реакций"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        bad_status, bad_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-2", "type": "invalid"},
        )
        self.assertEqual(bad_status, 400)
        self.assertIn("Некорректный тип реакции", bad_payload.get("error", ""))

        not_found_status, _, _ = self._post(
            "/api/feed/posts/999999/react",
            {"guest_profile_id": "guest-react-2", "type": "like"},
        )
        self.assertEqual(not_found_status, 404)

    def test_reactions_concurrency_is_idempotent(self) -> None:
        post = repository.create_guest_feed_post(author="Owner", text="Concurrent post", guest_profile_id="owner-1")
        post_id = post["id"]

        statuses: list[int] = []

        def _send() -> None:
            status, _, _ = self._post(
                f"/api/feed/posts/{post_id}/react",
                {"guest_profile_id": "guest-react-3", "type": "like"},
            )
            statuses.append(status)

        threads = [threading.Thread(target=_send) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        self.assertEqual(statuses.count(200), 8)
        payload = FeedService.get_post_reactions(post_id=post_id, guest_profile_id="guest-react-3")
        self.assertEqual(payload["likes"], 1)
        self.assertEqual(payload["my_reaction"], "like")

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
