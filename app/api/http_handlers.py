import json
import logging
import os
import traceback
import uuid
from typing import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.config import get_api_settings
from app.db import repository
from app.logging_setup import configure_logging
from app.services.feed_service import FeedService


logger = logging.getLogger(__name__)


class FeedAPIHandler(BaseHTTPRequestHandler):
    request_id: str

    def _get_client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _request_log_extra(self) -> dict[str, str]:
        return {"request_id": getattr(self, "request_id", "-"), "client_ip": self._get_client_ip()}

    def _send_json(self, status: int, payload: dict, extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(FeedService.serialize_payload(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        self.send_header("X-Request-ID", getattr(self, "request_id", "-"))
        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_internal_error(self) -> None:
        self._send_json(
            500,
            {
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "request_id": getattr(self, "request_id", "-"),
                }
            },
        )

    def _parse_feed_request_payload(self) -> tuple[dict[str, object] | None, str | None]:
        try:
            raw_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raw_len = 0

        raw = self.rfile.read(raw_len) if raw_len > 0 else b""
        content_type_header = str(self.headers.get("Content-Type", ""))
        content_type = content_type_header.lower()

        if content_type.startswith("multipart/form-data"):
            try:
                payload = FeedService.parse_multipart_form_data(content_type=content_type_header, raw=raw)
            except ValueError as error:
                return None, str(error)
            return payload, None

        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except UnicodeDecodeError:
            return None, "Тело запроса должно быть в UTF-8"
        except json.JSONDecodeError:
            return None, "Некорректный JSON"

        if not isinstance(payload, dict):
            return None, "Некорректный формат payload: ожидается JSON-объект"

        try:
            image_url = FeedService.validate_image_url_metadata(payload)
            image_from_base64 = FeedService.extract_image_from_json_payload(payload)
        except ValueError as error:
            return None, str(error)

        if image_url and image_from_base64:
            return None, "Укажите только одно поле изображения: image_url или image_base64"

        if image_from_base64:
            payload["image_url"] = image_from_base64
        elif image_url is not None:
            payload["image_url"] = image_url

        return payload, None

    def _serve_stored_file(self, request_path: str) -> bool:
        file_path = FeedService.resolve_storage_path(request_path)
        if file_path is None or not os.path.isfile(file_path):
            return False

        extension = os.path.splitext(file_path)[1].lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(extension, "application/octet-stream")

        with open(file_path, "rb") as file_obj:
            body = file_obj.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Request-ID", getattr(self, "request_id", "-"))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _with_error_handling(self, handler: Callable[[], None]) -> None:
        self.request_id = self.headers.get("X-Request-ID", "") or str(uuid.uuid4())
        try:
            handler()
            logger.info("%s %s -> completed", self.command, self.path, extra=self._request_log_extra())
        except Exception:
            logger.error(
                "Unhandled error on %s %s\n%s",
                self.command,
                self.path,
                traceback.format_exc(),
                extra=self._request_log_extra(),
            )
            self._send_internal_error()

    def do_OPTIONS(self) -> None:  # noqa: N802
        def _impl() -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
            self.send_header("X-Request-ID", getattr(self, "request_id", "-"))
            self.end_headers()

        self._with_error_handling(_impl)

    def do_GET(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_get)

    def _handle_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            db_ok = repository.check_db_health()
            if db_ok:
                self._send_json(200, {"status": "ok", "process": "ok", "database": "ok"})
            else:
                self._send_json(503, {"status": "degraded", "process": "ok", "database": "unavailable"})
            return

        if path.startswith(FeedService.STORAGE_URL_PREFIX):
            if self._serve_stored_file(path):
                return
            self._send_json(404, {"error": "Файл не найден"})
            return

        if path == "/api/feed/posts":
            params = parse_qs(parsed.query)

            def _parse_int(name: str, default: int) -> int:
                raw = params.get(name, [str(default)])[0]
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return default

            limit = max(1, min(100, _parse_int("limit", 20)))
            offset = max(0, _parse_int("offset", 0))
            posts = repository.list_guest_feed_posts(limit=limit, offset=offset)
            total = repository.count_guest_feed_posts()
            self._send_json(200, {"items": posts, "limit": limit, "offset": offset, "total": total})
            return

        if path.startswith("/api/feed/profiles/"):
            profile_id = path[len("/api/feed/profiles/") :].strip()
            if not profile_id:
                self._send_json(400, {"error": "Некорректный id профиля"})
                return
            profile = repository.get_guest_profile(profile_id)
            if not profile:
                self._send_json(404, {"error": "Профиль не найден"})
                return
            self._send_json(200, profile)
            return


        if path == "/api/driver/documents":
            params = parse_qs(parsed.query)
            profile_id = str(params.get("profile_id", ["driver-main"])[0] or "driver-main").strip()
            items = repository.list_driver_documents(profile_id=profile_id)
            self._send_json(200, {"items": items, "profile_id": profile_id, "total": len(items)})
            return

        if path == "/api/feed/approved":
            self._send_json(200, {"items": repository.list_approved_posts(limit=50, offset=0, include_ads=True)})
            return

        if path == "/api/feed/publication-rules":
            self._send_json(200, FeedService.get_publication_rules())
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_post)

    def _handle_post(self) -> None:
        path = urlparse(self.path).path
        payload, error = self._parse_feed_request_payload()
        if error:
            self._send_json(400, {"error": error})
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return


        if path == "/api/driver/documents":
            cleaned, errors = FeedService.validate_driver_document_fields(payload)
            if errors:
                self._send_json(400, {"error": "validation_error", "fields": errors})
                return
            duplicate = repository.find_driver_document_duplicate(
                profile_id=str(cleaned["profile_id"]),
                type=str(cleaned["type"]),
                number=str(cleaned["number"]),
            )
            if duplicate:
                self._send_json(
                    409,
                    {
                        "error": "duplicate_document",
                        "message": "Документ с таким типом и номером уже существует",
                        "fields": {"number": "Документ с таким номером уже добавлен"},
                    },
                )
                return
            created = repository.create_driver_document(**cleaned)
            self._send_json(201, created)
            return

        if path == "/api/feed/profiles":
            try:
                profile = repository.upsert_guest_profile(**FeedService.validate_profile_fields(payload))
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            self._send_json(201, profile)
            return

        if path != "/api/feed/posts":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            item = FeedService.create_guest_post(payload, self._get_client_ip())
        except RuntimeError as retry_error:
            retry_after = int(str(retry_error))
            self._send_json(
                429,
                {
                    "error": "Слишком много публикаций. Пожалуйста, подождите перед следующей отправкой.",
                    "retry_after": retry_after,
                },
                extra_headers={"Retry-After": str(retry_after)},
            )
            return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return

        self._send_json(201, item)

    def do_PATCH(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_patch)

    def _handle_patch(self) -> None:
        path = urlparse(self.path).path

        docs_prefix = "/api/driver/documents/"
        if path.startswith(docs_prefix):
            doc_id_raw = path[len(docs_prefix) :]
            if not doc_id_raw.isdigit() or int(doc_id_raw) <= 0:
                self._send_json(400, {"error": "Некорректный id документа"})
                return

            payload, error = self._parse_feed_request_payload()
            if error:
                self._send_json(400, {"error": error})
                return
            if payload is None:
                self._send_json(400, {"error": "Некорректный payload"})
                return

            cleaned, errors = FeedService.validate_driver_document_fields(payload)
            if errors:
                self._send_json(400, {"error": "validation_error", "fields": errors})
                return

            updated = repository.update_driver_document(int(doc_id_raw), **cleaned)
            if not updated:
                self._send_json(404, {"error": "Документ не найден"})
                return
            self._send_json(200, updated)
            return

        prefix = "/api/feed/posts/"
        if not path.startswith(prefix):
            self._send_json(404, {"error": "Not found"})
            return
        post_id_raw = path[len(prefix) :]
        if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
            self._send_json(400, {"error": "Некорректный id поста"})
            return

        payload, error = self._parse_feed_request_payload()
        if error:
            self._send_json(400, {"error": error})
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        try:
            updated = FeedService.update_guest_post(int(post_id_raw), payload)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return

        if not updated:
            self._send_json(404, {"error": "Пост не найден"})
            return

        self._send_json(200, updated)



    def do_DELETE(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_delete)

    def _handle_delete(self) -> None:
        path = urlparse(self.path).path
        docs_prefix = "/api/driver/documents/"
        if not path.startswith(docs_prefix):
            self._send_json(404, {"error": "Not found"})
            return

        doc_id_raw = path[len(docs_prefix) :]
        if not doc_id_raw.isdigit() or int(doc_id_raw) <= 0:
            self._send_json(400, {"error": "Некорректный id документа"})
            return

        deleted = repository.delete_driver_document(int(doc_id_raw))
        if not deleted:
            self._send_json(404, {"error": "Документ не найден"})
            return
        self._send_json(200, {"ok": True})

def run_api() -> None:
    configure_logging("feed-api")
    repository.init_db()
    settings = get_api_settings()
    host = settings.host
    port = settings.port
    server = ThreadingHTTPServer((host, port), FeedAPIHandler)
    logger.info("Feed API server started on http://%s:%s", host, port, extra={"request_id": "startup", "client_ip": "-"})
    server.serve_forever()
