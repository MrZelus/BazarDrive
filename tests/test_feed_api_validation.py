import json
import os
import tempfile
import threading
import unittest
from base64 import urlsafe_b64encode
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
        os.environ.pop("MODERATOR_API_KEYS", None)
        os.environ.pop("MODERATOR_BEARER_TOKENS", None)

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

    def test_verification_workflow_submit_approve_reject_and_history(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/profiles",
            {
                "id": "guest-verify-001",
                "display_name": "Водитель Тест",
                "email": "driver@example.com",
                "verification_state": "unverified",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload.get("verification_state"), "unverified")

        submit_status, submit_payload, _ = self._post(
            "/api/feed/profiles/guest-verify-001/verification/submit",
            {"actor": "guest-verify-001"},
        )
        self.assertEqual(submit_status, 200)
        self.assertEqual(submit_payload.get("verification_state"), "pending_verification")

        reject_status, reject_payload, _ = self._post(
            "/api/feed/profiles/guest-verify-001/verification/reject",
            {"actor": "moderator-1", "reason": "Фото документа размыто"},
        )
        self.assertEqual(reject_status, 200)
        self.assertEqual(reject_payload.get("verification_state"), "rejected")
        self.assertEqual(reject_payload.get("verification_rejection_reason"), "Фото документа размыто")

        resubmit_status, resubmit_payload, _ = self._post(
            "/api/feed/profiles/guest-verify-001/verification/submit",
            {"actor": "guest-verify-001"},
        )
        self.assertEqual(resubmit_status, 200)
        self.assertEqual(resubmit_payload.get("verification_state"), "pending_verification")

        approve_status, approve_payload, _ = self._post(
            "/api/feed/profiles/guest-verify-001/verification/approve",
            {"actor": "moderator-2"},
        )
        self.assertEqual(approve_status, 200)
        self.assertEqual(approve_payload.get("verification_state"), "verified")
        self.assertTrue(bool(approve_payload.get("is_verified")))

        profile_status, profile_payload, _ = self._get("/api/feed/profiles/guest-verify-001")
        self.assertEqual(profile_status, 200)
        self.assertEqual(profile_payload.get("verification_state"), "verified")
        self.assertIn("verification_history", profile_payload)
        self.assertGreaterEqual(len(profile_payload.get("verification_history", [])), 4)

    def test_verification_reject_requires_reason_and_enforces_state_transitions(self) -> None:
        created_status, _, _ = self._post(
            "/api/feed/profiles",
            {"id": "guest-verify-002", "display_name": "Тестовый", "phone": "+70000000000"},
        )
        self.assertEqual(created_status, 201)

        reject_without_submit_status, _, _ = self._post(
            "/api/feed/profiles/guest-verify-002/verification/reject",
            {"actor": "moderator-1", "reason": "Нет данных"},
        )
        self.assertEqual(reject_without_submit_status, 409)

        submit_status, _, _ = self._post(
            "/api/feed/profiles/guest-verify-002/verification/submit",
            {"actor": "guest-verify-002"},
        )
        self.assertEqual(submit_status, 200)

        reject_without_reason_status, reject_without_reason_payload, _ = self._post(
            "/api/feed/profiles/guest-verify-002/verification/reject",
            {"actor": "moderator-1"},
        )
        self.assertEqual(reject_without_reason_status, 409)
        self.assertIn("error", reject_without_reason_payload)

    def test_verification_metrics_endpoint_returns_aggregates(self) -> None:
        created_status, _, _ = self._post(
            "/api/feed/profiles",
            {"id": "guest-verify-003", "display_name": "Тестовый 3", "email": "verify3@example.com"},
        )
        self.assertEqual(created_status, 201)

        submit_status, _, _ = self._post(
            "/api/feed/profiles/guest-verify-003/verification/submit",
            {"actor": "guest-verify-003"},
        )
        self.assertEqual(submit_status, 200)

        reject_status, _, _ = self._post(
            "/api/feed/profiles/guest-verify-003/verification/reject",
            {"actor": "moderator-1", "reason": "Недостаточно данных"},
        )
        self.assertEqual(reject_status, 200)

        metrics_status, metrics_payload, _ = self._get("/api/feed/profiles/guest-verify-003/verification/metrics")
        self.assertEqual(metrics_status, 200)
        self.assertEqual(metrics_payload.get("profile_id"), "guest-verify-003")
        self.assertEqual(metrics_payload.get("total_events"), 2)
        self.assertEqual(metrics_payload.get("actions", {}).get("submit"), 1)
        self.assertEqual(metrics_payload.get("actions", {}).get("reject"), 1)
        self.assertEqual(metrics_payload.get("states", {}).get("pending_verification"), 1)
        self.assertEqual(metrics_payload.get("states", {}).get("rejected"), 1)
        self.assertEqual(metrics_payload.get("rejected_with_reason"), 1)

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
        self.assertEqual(list_after_delete_payload["total"], 0)

    def test_comments_list_total_ignores_pagination_window(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Пост для проверки total в комментариях"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        for idx in range(3):
            create_status, _, _ = self._post(
                f"/api/feed/posts/{post_id}/comments",
                {
                    "guest_profile_id": f"guest-{idx}",
                    "author": f"Комментатор {idx}",
                    "text": f"Комментарий {idx}",
                },
            )
            self.assertEqual(create_status, 201)

        list_status, list_payload, _ = self._get(f"/api/feed/posts/{post_id}/comments?limit=1&offset=1")
        self.assertEqual(list_status, 200)
        self.assertEqual(len(list_payload["items"]), 1)
        self.assertEqual(list_payload["total"], 3)

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

    def test_patch_post_forbidden_for_foreign_author(self) -> None:
        created_post = repository.create_guest_feed_post(
            author="Owner",
            text="Чужой пост для PATCH",
            guest_profile_id="guest-owner-001",
        )

        status, payload, _ = self._patch(
            f"/api/feed/posts/{created_post['id']}",
            {
                "guest_profile_id": "guest-other-001",
                "author": "Intruder",
                "text": "Попытка изменить чужой пост",
            },
        )
        self.assertEqual(status, 403)
        self.assertIn("error", payload)

    def test_prod_moderator_api_key_can_update_and_delete_foreign_content(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"
        os.environ["API_AUTH_KEYS"] = "author-key"
        os.environ["MODERATOR_API_KEYS"] = "mod-key"

        post = repository.create_guest_feed_post(
            author="Owner",
            text="Пост владельца",
            guest_profile_id="guest-owner-001",
        )
        comment = repository.create_guest_feed_comment(
            post_id=post["id"],
            guest_profile_id="guest-owner-001",
            author="Owner",
            text="Комментарий владельца",
        )

        headers = {"Origin": "https://app.example.com", "X-API-Key": "mod-key"}
        patch_post_status, patch_post_payload, _ = self._patch(
            f"/api/feed/posts/{post['id']}",
            {"author": "Moderator", "text": "Пост изменён модератором"},
            headers=headers,
        )
        self.assertEqual(patch_post_status, 200)
        self.assertEqual(patch_post_payload.get("text"), "Пост изменён модератором")

        patch_comment_status, patch_comment_payload, _ = self._patch(
            f"/api/feed/posts/{post['id']}/comments/{comment['id']}",
            {"text": "Комментарий изменён модератором"},
            headers=headers,
        )
        self.assertEqual(patch_comment_status, 200)
        self.assertEqual(patch_comment_payload.get("text"), "Комментарий изменён модератором")

        delete_comment_status, _, _ = self._delete(
            f"/api/feed/posts/{post['id']}/comments/{comment['id']}",
            {},
            headers=headers,
        )
        self.assertEqual(delete_comment_status, 200)

        delete_post_status, _, _ = self._delete(
            f"/api/feed/posts/{post['id']}",
            {},
            headers=headers,
        )
        self.assertEqual(delete_post_status, 200)

    def test_prod_author_key_cannot_update_foreign_post(self) -> None:
        os.environ["APP_ENV"] = "prod"
        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"
        os.environ["API_AUTH_KEYS"] = "author-key"
        os.environ["MODERATOR_API_KEYS"] = "mod-key"
        post = repository.create_guest_feed_post(
            author="Owner",
            text="Пост владельца",
            guest_profile_id="guest-owner-001",
        )

        status, payload, _ = self._patch(
            f"/api/feed/posts/{post['id']}",
            {
                "guest_profile_id": "guest-other-001",
                "author": "Other",
                "text": "Попытка изменения чужого поста",
            },
            headers={"Origin": "https://app.example.com", "X-API-Key": "author-key"},
        )
        self.assertEqual(status, 403)
        self.assertIn("error", payload)


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

    def test_reactions_plural_endpoint_and_get_snapshot(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Пост для reactions endpoint"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        set_status, set_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/reactions",
            {"guest_profile_id": "guest-react-4", "type": "like"},
        )
        self.assertEqual(set_status, 200)
        self.assertEqual(set_payload["likes"], 1)
        self.assertEqual(set_payload["my_reaction"], "like")

        get_status, get_payload, _ = self._get(
            f"/api/feed/posts/{post_id}/reactions?guest_profile_id=guest-react-4"
        )
        self.assertEqual(get_status, 200)
        self.assertEqual(get_payload["likes"], 1)
        self.assertEqual(get_payload["my_reaction"], "like")
        self.assertEqual(get_payload["reactions"].get("like"), 1)

        delete_status, delete_payload, _ = self._delete(
            f"/api/feed/posts/{post_id}/reactions",
            {"guest_profile_id": "guest-react-4"},
        )
        self.assertEqual(delete_status, 200)
        self.assertIsNone(delete_payload["my_reaction"])
        self.assertEqual(delete_payload["reactions"], {})

    def test_legacy_react_endpoint_still_supported_for_backward_compatibility(self) -> None:
        post_status, post_payload, _ = self._post(
            "/api/feed/posts",
            {"author": "Valid Author", "text": "Пост для legacy react"},
        )
        self.assertEqual(post_status, 201)
        post_id = post_payload["id"]

        set_status, set_payload, _ = self._post(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-legacy", "type": "like"},
        )
        self.assertEqual(set_status, 200)
        self.assertEqual(set_payload["likes"], 1)

        delete_status, delete_payload, _ = self._delete(
            f"/api/feed/posts/{post_id}/react",
            {"guest_profile_id": "guest-react-legacy"},
        )
        self.assertEqual(delete_status, 200)
        self.assertEqual(delete_payload["likes"], 0)
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

    def test_create_post_with_multiple_media_and_legacy_fallback(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Media Author",
                "text": "Пост с несколькими медиа",
                "media": [
                    {"media_type": "image", "url": "https://example.com/image-1.jpg", "position": 1},
                    {"media_type": "video", "url": "https://example.com/video-1.mp4", "position": 0},
                ],
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual([item["media_type"] for item in payload["media"]], ["video", "image"])
        self.assertEqual(payload.get("image_url"), "https://example.com/image-1.jpg")

        list_status, list_payload, _ = self._get("/api/feed/posts")
        self.assertEqual(list_status, 200)
        self.assertEqual(len(list_payload["items"][0]["media"]), 2)

    def test_create_post_with_too_many_media_returns_413(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Media Author",
                "text": "Пост с лишними вложениями",
                "media": [{"media_type": "image", "url": f"https://example.com/{i}.jpg"} for i in range(9)],
            },
        )
        self.assertEqual(status, 413)
        self.assertIn("error", payload)

    def test_create_post_with_invalid_media_type_returns_400(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Media Author",
                "text": "Пост с невалидным типом",
                "media": [{"media_type": "audio", "url": "https://example.com/file.mp3"}],
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("Некорректный media_type", payload.get("error", ""))

    def test_legacy_image_url_post_is_exposed_as_media(self) -> None:
        created = repository.create_guest_feed_post(
            author="Legacy Author",
            text="Legacy image_url",
            image_url="https://example.com/legacy-only.jpg",
        )
        status, payload, _ = self._get("/api/feed/posts")
        self.assertEqual(status, 200)
        target = next(item for item in payload["items"] if item["id"] == created["id"])
        self.assertEqual(len(target["media"]), 1)
        self.assertEqual(target["media"][0]["url"], "https://example.com/legacy-only.jpg")
        self.assertEqual(target.get("image_url"), "https://example.com/legacy-only.jpg")

    def test_create_post_with_null_image_url_does_not_emit_none_media(self) -> None:
        status, payload, _ = self._post(
            "/api/feed/posts",
            {
                "author": "Null Image",
                "text": "Пост без изображения",
                "image_url": None,
            },
        )
        self.assertEqual(status, 201)
        self.assertNotEqual(payload.get("image_url"), "None")
        self.assertEqual(payload.get("media"), [])

    def test_legacy_string_none_image_url_is_not_used_as_media_fallback(self) -> None:
        created = repository.create_guest_feed_post(
            author="Legacy None",
            text="Пост с невалидным legacy image",
            image_url="None",
        )
        status, payload, _ = self._get("/api/feed/posts")
        self.assertEqual(status, 200)
        target = next(item for item in payload["items"] if item["id"] == created["id"])
        self.assertEqual(target.get("media"), [])

    def test_feed_cursor_pagination_first_and_next_page(self) -> None:
        for idx in range(5):
            repository.create_guest_feed_post(author=f"Author {idx}", text=f"Post {idx}", guest_profile_id="guest-cursor")

        first_status, first_payload, _ = self._get("/api/feed/posts?limit=2")
        self.assertEqual(first_status, 200)
        self.assertEqual(len(first_payload.get("items", [])), 2)
        self.assertTrue(first_payload.get("has_more"))
        self.assertTrue(first_payload.get("next_cursor"))

        next_cursor = first_payload["next_cursor"]
        second_status, second_payload, _ = self._get(f"/api/feed/posts?limit=2&cursor={next_cursor}")
        self.assertEqual(second_status, 200)
        self.assertEqual(len(second_payload.get("items", [])), 2)

        first_ids = {int(item["id"]) for item in first_payload["items"]}
        second_ids = {int(item["id"]) for item in second_payload["items"]}
        self.assertEqual(len(first_ids.intersection(second_ids)), 0)

    def test_feed_list_supports_search_query_with_offset(self) -> None:
        repository.create_guest_feed_post(author="Taxi Expert", text="Москва аэропорт", guest_profile_id="guest-search")
        repository.create_guest_feed_post(author="Food Lover", text="Лучшие рестораны", guest_profile_id="guest-search")
        repository.create_guest_feed_post(author="Taxi Helper", text="Поездка в центр", guest_profile_id="guest-search")

        status, payload, _ = self._get("/api/feed/posts?limit=10&offset=0&q=taxi")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("q"), "taxi")
        self.assertEqual(payload.get("total"), 2)
        self.assertEqual(len(payload.get("items", [])), 2)
        for item in payload["items"]:
            haystack = f"{item.get('author', '')} {item.get('text', '')}".lower()
            self.assertIn("taxi", haystack)

    def test_feed_cursor_pagination_respects_search_query(self) -> None:
        repository.create_guest_feed_post(author="Search One", text="alpha keyword", guest_profile_id="guest-search-cursor")
        repository.create_guest_feed_post(author="Search Two", text="beta keyword", guest_profile_id="guest-search-cursor")
        repository.create_guest_feed_post(author="Search Three", text="alpha second", guest_profile_id="guest-search-cursor")

        first_status, first_payload, _ = self._get("/api/feed/posts?limit=1&q=alpha")
        self.assertEqual(first_status, 200)
        self.assertEqual(first_payload.get("q"), "alpha")
        self.assertEqual(first_payload.get("total"), 2)
        self.assertEqual(len(first_payload.get("items", [])), 1)
        self.assertTrue(first_payload.get("next_cursor"))

        next_cursor = first_payload["next_cursor"]
        second_status, second_payload, _ = self._get(f"/api/feed/posts?limit=1&q=alpha&cursor={next_cursor}")
        self.assertEqual(second_status, 200)
        self.assertEqual(second_payload.get("q"), "alpha")
        self.assertEqual(len(second_payload.get("items", [])), 1)
        self.assertFalse(second_payload.get("has_more"))
        self.assertIsNone(second_payload.get("next_cursor"))

        first_ids = {int(item["id"]) for item in first_payload["items"]}
        second_ids = {int(item["id"]) for item in second_payload["items"]}
        self.assertEqual(len(first_ids.intersection(second_ids)), 0)
        for item in [*first_payload["items"], *second_payload["items"]]:
            haystack = f"{item.get('author', '')} {item.get('text', '')}".lower()
            self.assertIn("alpha", haystack)

    def test_feed_search_is_case_insensitive_for_cyrillic(self) -> None:
        repository.create_guest_feed_post(author="ИВАН", text="Поездка в МОСКВА", guest_profile_id="guest-search-ru")
        repository.create_guest_feed_post(author="Пётр", text="Маршрут до Казань", guest_profile_id="guest-search-ru")
        repository.create_guest_feed_post(author="Мария", text="Без совпадений", guest_profile_id="guest-search-ru")

        status, payload, _ = self._get("/api/feed/posts?limit=10&q=%D0%B8%D0%B2%D0%B0%D0%BD")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("total"), 1)
        self.assertEqual(len(payload.get("items", [])), 1)
        self.assertEqual(payload["items"][0]["author"], "ИВАН")

        status_city, payload_city, _ = self._get("/api/feed/posts?limit=10&q=%D0%BC%D0%BE%D1%81%D0%BA%D0%B2%D0%B0")
        self.assertEqual(status_city, 200)
        self.assertEqual(payload_city.get("total"), 1)
        self.assertEqual(len(payload_city.get("items", [])), 1)
        self.assertIn("МОСКВА", payload_city["items"][0]["text"])

    def test_feed_cursor_pagination_invalid_cursor_returns_400(self) -> None:
        repository.create_guest_feed_post(author="Author", text="Post", guest_profile_id="guest-cursor")
        status, payload, _ = self._get("/api/feed/posts?limit=2&cursor=not-valid")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_feed_cursor_pagination_empty_tail(self) -> None:
        repository.create_guest_feed_post(author="Author 1", text="Post 1", guest_profile_id="guest-cursor")
        repository.create_guest_feed_post(author="Author 2", text="Post 2", guest_profile_id="guest-cursor")
        first_status, first_payload, _ = self._get("/api/feed/posts?limit=1")
        self.assertEqual(first_status, 200)
        cursor = str(first_payload.get("next_cursor", "")).strip()
        self.assertTrue(cursor)

        second_status, second_payload, _ = self._get(f"/api/feed/posts?limit=1&cursor={cursor}")
        self.assertEqual(second_status, 200)
        last_item = second_payload["items"][-1]
        encoded_tail_cursor = urlsafe_b64encode(
            f"{last_item['created_at']}|{last_item['id']}".encode("utf-8")
        ).decode("ascii")

        tail_status, tail_payload, _ = self._get(f"/api/feed/posts?limit=1&cursor={encoded_tail_cursor}")
        self.assertEqual(tail_status, 200)
        self.assertEqual(tail_payload.get("items"), [])
        self.assertFalse(tail_payload.get("has_more"))
        self.assertIsNone(tail_payload.get("next_cursor"))

    def test_feed_cursor_pagination_single_page_returns_no_next_cursor(self) -> None:
        repository.create_guest_feed_post(author="Author", text="Post", guest_profile_id="guest-cursor")
        status, payload, _ = self._get("/api/feed/posts?limit=5")
        self.assertEqual(status, 200)
        self.assertFalse(payload.get("has_more"))
        self.assertIsNone(payload.get("next_cursor"))
        self.assertEqual(len(payload.get("items", [])), 1)

    def test_feed_cursor_and_offset_together_returns_400(self) -> None:
        repository.create_guest_feed_post(author="Author", text="Post", guest_profile_id="guest-cursor")
        first_status, first_payload, _ = self._get("/api/feed/posts?limit=1")
        self.assertEqual(first_status, 200)
        cursor = str(first_payload.get("next_cursor", "")).strip()
        status, payload, _ = self._get(f"/api/feed/posts?limit=1&offset=0&cursor={cursor}")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

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
