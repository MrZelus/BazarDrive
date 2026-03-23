import json
import logging
import os
import traceback
import uuid
from dataclasses import dataclass
from typing import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.config import get_api_settings
from app.db import repository
from app.logging_setup import configure_logging
from app.services.feed_service import FeedService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SecuritySettings:
    app_env: str
    allowed_origins: tuple[str, ...]
    api_keys: tuple[str, ...]
    bearer_tokens: tuple[str, ...]


class FeedAPIHandler(BaseHTTPRequestHandler):
    request_id: str
    DEFAULT_MAX_REQUEST_BYTES = 5 * 1024 * 1024

    def _get_client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _request_log_extra(self) -> dict[str, str]:
        return {"request_id": getattr(self, "request_id", "-"), "client_ip": self._get_client_ip()}

    def _get_security_settings(self) -> SecuritySettings:
        app_env = os.getenv("APP_ENV", "dev").strip().lower() or "dev"
        if app_env not in {"dev", "prod"}:
            app_env = "dev"

        raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        allowed_origins = tuple(
            item.strip() for item in raw_origins.split(",") if item.strip()
        )

        if app_env == "prod" and any(origin == "*" for origin in allowed_origins):
            raise ValueError("CORS_ALLOWED_ORIGINS must not contain wildcard '*' in prod")

        raw_api_keys = os.getenv("API_AUTH_KEYS", "")
        api_keys = tuple(item.strip() for item in raw_api_keys.split(",") if item.strip())

        raw_bearer_tokens = os.getenv("API_AUTH_BEARER_TOKENS", "")
        bearer_tokens = tuple(item.strip() for item in raw_bearer_tokens.split(",") if item.strip())

        return SecuritySettings(
            app_env=app_env,
            allowed_origins=allowed_origins,
            api_keys=api_keys,
            bearer_tokens=bearer_tokens,
        )

    def _resolve_access_control_origin(self, settings: SecuritySettings) -> str | None:
        origin = str(self.headers.get("Origin", "")).strip()
        if settings.app_env != "prod":
            return "*"
        if not origin:
            return None
        return origin if origin in settings.allowed_origins else None

    def _is_origin_allowed(self, settings: SecuritySettings) -> bool:
        origin = str(self.headers.get("Origin", "")).strip()
        if settings.app_env != "prod":
            return True
        if not origin:
            return True
        return origin in settings.allowed_origins

    def _is_write_method(self) -> bool:
        return self.command in {"POST", "PATCH", "DELETE"}

    def _is_authorized_write_request(self, settings: SecuritySettings) -> bool:
        if settings.app_env != "prod" or not self._is_write_method():
            return True

        has_configured_credentials = bool(settings.api_keys or settings.bearer_tokens)
        if not has_configured_credentials:
            return False

        api_key = str(self.headers.get("X-API-Key", "")).strip()
        if api_key and api_key in settings.api_keys:
            return True

        auth_header = str(self.headers.get("Authorization", "")).strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token and token in settings.bearer_tokens:
                return True

        return False

    def _build_cors_headers(self, settings: SecuritySettings) -> dict[str, str]:
        headers: dict[str, str] = {
            "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Request-ID, X-API-Key, Authorization",
        }
        origin = self._resolve_access_control_origin(settings)
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
            if settings.app_env == "prod":
                headers["Vary"] = "Origin"
        return headers

    def _send_auth_error(self, status: int, code: str, message: str) -> None:
        self._send_json(
            status,
            {
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": getattr(self, "request_id", "-"),
                }
            },
        )

    def _send_json(self, status: int, payload: dict, extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(FeedService.serialize_payload(payload), ensure_ascii=False).encode("utf-8")
        settings = self._get_security_settings()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in self._build_cors_headers(settings).items():
            self.send_header(name, value)
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

    def _payload_too_large_error(self, max_request_bytes: int) -> dict[str, object]:
        return {
            "error": {
                "code": "payload_too_large",
                "message": "Payload Too Large",
                "max_request_bytes": max_request_bytes,
                "request_id": getattr(self, "request_id", "-"),
            }
        }

    def _get_max_request_bytes(self) -> int:
        raw = os.getenv("MAX_REQUEST_BYTES", str(self.DEFAULT_MAX_REQUEST_BYTES))
        try:
            parsed = int(raw)
        except ValueError:
            return self.DEFAULT_MAX_REQUEST_BYTES
        if parsed <= 0:
            return self.DEFAULT_MAX_REQUEST_BYTES
        return parsed

    def _parse_feed_request_payload(self) -> tuple[dict[str, object] | None, dict[str, object] | None, int]:
        max_request_bytes = self._get_max_request_bytes()
        try:
            raw_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raw_len = 0

        if raw_len > max_request_bytes:
            return None, self._payload_too_large_error(max_request_bytes), 413

        raw = self.rfile.read(raw_len) if raw_len > 0 else b""
        if len(raw) > max_request_bytes:
            return None, self._payload_too_large_error(max_request_bytes), 413
        content_type_header = str(self.headers.get("Content-Type", ""))
        content_type = content_type_header.lower()

        if content_type.startswith("multipart/form-data"):
            try:
                payload = FeedService.parse_multipart_form_data(content_type=content_type_header, raw=raw)
            except ValueError as error:
                return None, {"error": str(error)}, 400
            return payload, None, 200

        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except UnicodeDecodeError:
            return None, {"error": "Тело запроса должно быть в UTF-8"}, 400
        except json.JSONDecodeError:
            return None, {"error": "Некорректный JSON"}, 400

        if not isinstance(payload, dict):
            return None, {"error": "Некорректный формат payload: ожидается JSON-объект"}, 400

        try:
            image_url = FeedService.validate_image_url_metadata(payload)
            image_from_base64 = FeedService.extract_image_from_json_payload(payload)
        except ValueError as error:
            return None, {"error": str(error)}, 400

        if image_url and image_from_base64:
            return None, {"error": "Укажите только одно поле изображения: image_url или image_base64"}, 400

        if image_from_base64:
            payload["image_url"] = image_from_base64
        elif image_url is not None:
            payload["image_url"] = image_url

        return payload, None, 200

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
        settings = self._get_security_settings()
        for name, value in self._build_cors_headers(settings).items():
            self.send_header(name, value)
        self.send_header("X-Request-ID", getattr(self, "request_id", "-"))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _with_error_handling(self, handler: Callable[[], None]) -> None:
        self.request_id = self.headers.get("X-Request-ID", "") or str(uuid.uuid4())
        try:
            settings = self._get_security_settings()
            if not self._is_origin_allowed(settings):
                logger.warning(
                    "Blocked request due to origin policy: %s",
                    self.headers.get("Origin", ""),
                    extra=self._request_log_extra(),
                )
                self._send_auth_error(403, "forbidden_origin", "Origin is not allowed")
                return
            if not self._is_authorized_write_request(settings):
                logger.warning(
                    "Blocked write request due to missing/invalid credentials",
                    extra=self._request_log_extra(),
                )
                self._send_auth_error(401, "unauthorized", "Write operations require authentication")
                return
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
            settings = self._get_security_settings()
            self.send_response(204)
            for name, value in self._build_cors_headers(settings).items():
                self.send_header(name, value)
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
        payload, error_payload, error_status = self._parse_feed_request_payload()
        if error_payload is not None:
            self._send_json(error_status, error_payload)
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

            payload, error_payload, error_status = self._parse_feed_request_payload()
            if error_payload is not None:
                self._send_json(error_status, error_payload)
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

        payload, error_payload, error_status = self._parse_feed_request_payload()
        if error_payload is not None:
            self._send_json(error_status, error_payload)
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
