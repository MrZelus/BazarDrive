import json
import logging
import os
import traceback
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as default_policy
from typing import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.config import get_api_settings
from app.db import repository
from app.logging_setup import configure_logging
from app.services.driver_compliance_service import DriverComplianceService
from app.services.driver_operation_service import DriverOperationService
from app.services.driver_guard_service import DriverGuardService
from app.services.driver_reminder_service import DriverReminderService
from app.services.driver_score_service import DriverScoreService
from app.services.driver_summary_service import DriverSummaryService
from app.services.exceptions import DriverNotAllowedError
from app.services.feed_service import FeedAccessDeniedError, FeedPayloadTooLargeError, FeedService
from app.services.waybill_service import WaybillService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SecuritySettings:
    app_env: str
    allowed_origins: tuple[str, ...]
    api_keys: tuple[str, ...]
    bearer_tokens: tuple[str, ...]
    moderator_api_keys: tuple[str, ...]
    moderator_bearer_tokens: tuple[str, ...]


@dataclass(frozen=True)
class WriteAuthContext:
    is_authorized: bool
    subject: str
    role: str

    @property
    def is_moderator(self) -> bool:
        return self.role == "moderator"


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
        raw_moderator_api_keys = os.getenv("MODERATOR_API_KEYS", "")
        moderator_api_keys = tuple(item.strip() for item in raw_moderator_api_keys.split(",") if item.strip())
        raw_moderator_bearer_tokens = os.getenv("MODERATOR_BEARER_TOKENS", "")
        moderator_bearer_tokens = tuple(item.strip() for item in raw_moderator_bearer_tokens.split(",") if item.strip())

        return SecuritySettings(
            app_env=app_env,
            allowed_origins=allowed_origins,
            api_keys=api_keys,
            bearer_tokens=bearer_tokens,
            moderator_api_keys=moderator_api_keys,
            moderator_bearer_tokens=moderator_bearer_tokens,
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

    def _resolve_write_auth_context(self, settings: SecuritySettings) -> WriteAuthContext:
        if settings.app_env != "prod" or not self._is_write_method():
            return WriteAuthContext(is_authorized=True, subject="dev", role="author")

        has_configured_credentials = bool(
            settings.api_keys
            or settings.bearer_tokens
            or settings.moderator_api_keys
            or settings.moderator_bearer_tokens
        )
        if not has_configured_credentials:
            return WriteAuthContext(is_authorized=False, subject="anonymous", role="anonymous")
        api_key = str(self.headers.get("X-API-Key", "")).strip()
        if api_key:
            if api_key in settings.moderator_api_keys:
                return WriteAuthContext(is_authorized=True, subject=f"api_key:{api_key}", role="moderator")
            if api_key in settings.api_keys:
                return WriteAuthContext(is_authorized=True, subject=f"api_key:{api_key}", role="author")

        auth_header = str(self.headers.get("Authorization", "")).strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token:
                if token in settings.moderator_bearer_tokens:
                    return WriteAuthContext(is_authorized=True, subject=f"bearer:{token}", role="moderator")
                if token in settings.bearer_tokens:
                    return WriteAuthContext(is_authorized=True, subject=f"bearer:{token}", role="author")

        return WriteAuthContext(is_authorized=False, subject="anonymous", role="anonymous")

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

    def _send_interaction_error(self, status: int, message: str, default_code: str) -> None:
        self._send_json(
            status,
            {
                "error": message,
                "error_code": self._resolve_interaction_error_code(message, default=default_code),
            },
        )

    @staticmethod
    def _resolve_interaction_error_code(message: str, default: str) -> str:
        normalized = str(message or "").strip().lower()
        if not normalized:
            return default
        if "guest_profile_id" in normalized and "обязательно" in normalized:
            return "guest_profile_required"
        if "тип реакции" in normalized and "допустимые значения" in normalized:
            return "reaction_type_invalid"
        if "некорректный id поста" in normalized:
            return "post_id_invalid"
        if "некорректный id комментария" in normalized:
            return "comment_id_invalid"
        if "пост не найден" in normalized:
            return "post_not_found"
        if "комментарий не найден" in normalized:
            return "comment_not_found"
        if "недостаточно прав для изменения комментария" in normalized:
            return "comment_edit_forbidden"
        if "недостаточно прав для удаления комментария" in normalized:
            return "comment_delete_forbidden"
        if "поле text обязательно" in normalized:
            return "comment_text_required"
        if "поля author и text обязательны" in normalized:
            return "comment_text_required"
        if "комментарий слишком длинный" in normalized:
            return "comment_text_too_long"
        if "комментарий должен содержать минимум" in normalized:
            return "comment_text_too_short"
        return default

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
        except FeedPayloadTooLargeError as error:
            return None, {"error": str(error)}, 413
        except ValueError as error:
            return None, {"error": str(error)}, 400

        if payload.get("media") is not None and image_from_base64:
            return None, {"error": "Поле image_base64 нельзя использовать вместе с media[]"}, 400
        if image_url and image_from_base64:
            return None, {"error": "Укажите только одно поле изображения: image_url или image_base64"}, 400

        if image_from_base64:
            payload["image_url"] = image_from_base64
        elif image_url is not None:
            payload["image_url"] = image_url

        return payload, None, 200

    @staticmethod
    def _encode_posts_cursor(item: dict[str, object]) -> str | None:
        created_at = str(item.get("created_at", "")).strip()
        post_id = item.get("id")
        if not created_at:
            return None
        try:
            normalized_post_id = int(post_id)
        except (TypeError, ValueError):
            return None
        raw = f"{created_at}|{normalized_post_id}".encode("utf-8")
        return urlsafe_b64encode(raw).decode("ascii")

    @staticmethod
    def _decode_posts_cursor(raw_cursor: str) -> tuple[str, int]:
        normalized = str(raw_cursor or "").strip()
        if not normalized:
            raise ValueError("cursor is empty")
        try:
            decoded = urlsafe_b64decode(normalized.encode("ascii")).decode("utf-8")
        except Exception as error:
            raise ValueError("cursor has invalid encoding") from error
        parts = decoded.split("|", 1)
        if len(parts) != 2:
            raise ValueError("cursor must contain created_at and id")
        created_at = parts[0].strip()
        if not created_at:
            raise ValueError("cursor.created_at is empty")
        try:
            cursor_id = int(parts[1].strip())
        except ValueError as error:
            raise ValueError("cursor.id must be an integer") from error
        if cursor_id <= 0:
            raise ValueError("cursor.id must be positive")
        return created_at, cursor_id

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
            ".pdf": "application/pdf",
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
            write_auth_context = self._resolve_write_auth_context(settings)
            self.write_auth_context = write_auth_context
            if not write_auth_context.is_authorized:
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
            guest_profile_id = str(params.get("guest_profile_id", [""])[0]).strip()
            search_query = str(params.get("q", [""])[0]).strip()
            cursor = str(params.get("cursor", [""])[0]).strip()
            use_cursor = bool(cursor)
            if use_cursor and "offset" in params:
                self._send_json(400, {"error": "Нельзя одновременно передавать cursor и offset"})
                return

            if use_cursor:
                try:
                    cursor_created_at, cursor_id = self._decode_posts_cursor(cursor)
                except ValueError:
                    self._send_json(400, {"error": "Некорректный cursor"})
                    return
                cursor_batch = repository.list_guest_feed_posts_by_cursor(
                    limit=limit + 1,
                    cursor_created_at=cursor_created_at,
                    cursor_id=cursor_id,
                    search_query=search_query,
                )
                has_more = len(cursor_batch) > limit
                posts = cursor_batch[:limit]
            else:
                posts = repository.list_guest_feed_posts(limit=limit, offset=offset, search_query=search_query)
                has_more = False
            enriched_posts = FeedService.enrich_posts_with_reactions(posts, guest_profile_id=guest_profile_id)
            total = repository.count_guest_feed_posts(search_query=search_query)
            if not use_cursor:
                has_more = (offset + len(enriched_posts)) < total
            next_cursor = self._encode_posts_cursor(enriched_posts[-1]) if enriched_posts else None
            self._send_json(
                200,
                {
                    "items": enriched_posts,
                    "limit": limit,
                    "offset": offset,
                    "q": search_query,
                    "total": total,
                    "next_cursor": next_cursor if has_more else None,
                    "has_more": has_more,
                },
            )
            return

        reactions_prefix = "/api/feed/posts/"
        if path.startswith(reactions_prefix) and path.endswith("/reactions"):
            post_id_raw = path[len(reactions_prefix) : -len("/reactions")]
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_json(400, {"error": "Некорректный id поста"})
                return
            params = parse_qs(parsed.query)
            guest_profile_id = str(params.get("guest_profile_id", [""])[0]).strip() or None
            try:
                item = FeedService.get_post_reactions(post_id=int(post_id_raw), guest_profile_id=guest_profile_id)
            except LookupError as error:
                self._send_json(404, {"error": str(error)})
                return
            self._send_json(200, item)
            return

        comments_prefix = "/api/feed/posts/"
        if path.startswith(comments_prefix) and path.endswith("/comments"):
            suffix = path[len(comments_prefix) :]
            post_id_raw = suffix[: -len("/comments")]
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_json(400, {"error": "Некорректный id поста"})
                return

            params = parse_qs(parsed.query)

            def _parse_int(name: str, default: int) -> int:
                raw = params.get(name, [str(default)])[0]
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return default

            limit = max(1, min(200, _parse_int("limit", 100)))
            offset = max(0, _parse_int("offset", 0))
            try:
                items = FeedService.list_guest_comments(post_id=int(post_id_raw), limit=limit, offset=offset)
                total = FeedService.count_guest_comments(post_id=int(post_id_raw))
            except LookupError as error:
                self._send_json(404, {"error": str(error)})
                return
            self._send_json(200, {"items": items, "limit": limit, "offset": offset, "total": total})
            return

        verification_history_suffix = "/verification/history"
        if path.startswith("/api/feed/profiles/") and path.endswith(verification_history_suffix):
            profile_id = path[len("/api/feed/profiles/") : -len(verification_history_suffix)].strip()
            if not profile_id:
                self._send_json(400, {"error": "Некорректный id профиля"})
                return
            history = repository.get_guest_profile_verification_history(profile_id)
            self._send_json(200, {"items": history, "total": len(history)})
            return

        verification_metrics_suffix = "/verification/metrics"
        if path.startswith("/api/feed/profiles/") and path.endswith(verification_metrics_suffix):
            profile_id = path[len("/api/feed/profiles/") : -len(verification_metrics_suffix)].strip()
            if not profile_id:
                self._send_json(400, {"error": "Некорректный id профиля"})
                return
            metrics = repository.get_guest_profile_verification_metrics(profile_id)
            self._send_json(200, metrics)
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
            profile["verification_history"] = repository.get_guest_profile_verification_history(profile_id)
            self._send_json(200, profile)
            return

        if path == "/api/driver/compliance":
            self._handle_driver_compliance_get()
            return

        if path == "/api/driver/documents":
            params = parse_qs(parsed.query)
            profile_id = str(params.get("profile_id", ["driver-main"])[0] or "driver-main").strip()
            items = repository.list_driver_documents(profile_id=profile_id)
            self._send_json(200, {"items": items, "profile_id": profile_id, "total": len(items)})
            return

        if path in {"/api/driver/summary", "/driver/summary"}:
            params = parse_qs(parsed.query)
            profile_id = str(params.get("profile_id", ["driver-main"])[0] or "driver-main").strip() or "driver-main"
            summary = DriverSummaryService.build(profile_id)
            self._send_json(200, summary.to_dict())
            return

        if path in {"/api/driver/dashboard", "/driver/dashboard"}:
            params = parse_qs(parsed.query)
            profile_id = str(params.get("profile_id", ["driver-main"])[0] or "driver-main").strip() or "driver-main"
            summary = DriverSummaryService.build(profile_id)
            score = DriverScoreService.calculate(profile_id)
            reminders = DriverReminderService.get_reminders_as_dicts(profile_id)
            mode = DriverGuardService.get_mode(profile_id)
            self._send_json(
                200,
                {
                    "summary": summary.to_dict(),
                    "score": score,
                    "reminders": reminders,
                    "mode": mode,
                },
            )
            return

        if path == "/api/driver/order-journal":
            self._handle_driver_order_journal_get(parsed.query)
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

        if path == "/api/driver/compliance/profile":
            self._handle_driver_compliance_profile_upsert()
            return

        if path == "/api/driver/compliance/document":
            self._handle_driver_document_upsert()
            return

        if path == "/api/driver/compliance/check":
            self._handle_driver_compliance_check()
            return

        if path == "/api/driver/go-online":
            self._handle_driver_go_online()
            return

        if path == "/api/driver/accept-order":
            self._handle_driver_accept_order()
            return

        if path == "/api/driver/assign-order":
            self._handle_driver_assign_order()
            return

        if path == "/api/driver/complete-order":
            self._handle_driver_complete_order()
            return

        if path == "/api/driver/cancel-order":
            self._handle_driver_cancel_order()
            return

        if path in {"/api/driver/shift/open", "/driver/shift/open"}:
            self._handle_driver_shift_open()
            return

        if path in {"/api/driver/shift/close", "/driver/shift/close"}:
            self._handle_driver_shift_close()
            return

        if path == "/api/driver/documents/upload":
            content_type_header = str(self.headers.get("Content-Type", "")).strip()
            content_type = content_type_header.lower()
            if content_type.startswith("multipart/form-data"):
                max_request_bytes = self._get_max_request_bytes()
                try:
                    raw_len = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    raw_len = 0
                if raw_len <= 0:
                    self._send_json(400, {"error": "Пустой файл документа"})
                    return
                if raw_len > max_request_bytes:
                    self._send_json(413, self._payload_too_large_error(max_request_bytes))
                    return
                raw = self.rfile.read(raw_len)
                if len(raw) > max_request_bytes:
                    self._send_json(413, self._payload_too_large_error(max_request_bytes))
                    return

                envelope = f"Content-Type: {content_type_header}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw
                message = BytesParser(policy=default_policy).parsebytes(envelope)
                if not message.is_multipart():
                    self._send_json(400, {"error": "Некорректный multipart/form-data"})
                    return

                for part in message.iter_parts():
                    name = str(part.get_param("name", header="content-disposition") or "").strip().strip('"').lower()
                    filename = str(part.get_filename() or "").strip()
                    mime_type = str(part.get_content_type() or "").strip().lower()
                    looks_like_file = (
                        "file" in name
                        or name in {"document", "waybill"}
                        or bool(filename)
                        or mime_type in {"application/pdf", "application/octet-stream"}
                    )
                    if not looks_like_file:
                        continue
                    file_bytes = part.get_payload(decode=True) or b""
                    if not file_bytes:
                        continue
                    try:
                        file_url = FeedService.document_bytes_to_stored_url(
                            file_bytes=file_bytes,
                            mime_type="application/pdf" if mime_type == "application/octet-stream" else mime_type,
                            filename=filename or "upload.pdf",
                        )
                    except FeedPayloadTooLargeError as error:
                        self._send_json(413, {"error": str(error)})
                        return
                    except ValueError as error:
                        self._send_json(400, {"error": str(error)})
                        return
                    self._send_json(201, {"file_url": file_url})
                    return

                self._send_json(400, {"error": "Не найден файл документа (ожидается поле file в multipart/form-data)"})
                return

            if content_type.startswith("application/pdf") or content_type.startswith("application/octet-stream"):
                max_request_bytes = self._get_max_request_bytes()
                try:
                    raw_len = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    raw_len = 0
                if raw_len <= 0:
                    self._send_json(400, {"error": "Пустой файл документа"})
                    return
                if raw_len > max_request_bytes:
                    self._send_json(413, self._payload_too_large_error(max_request_bytes))
                    return
                raw = self.rfile.read(raw_len)
                if len(raw) > max_request_bytes:
                    self._send_json(413, self._payload_too_large_error(max_request_bytes))
                    return

                filename = str(self.headers.get("X-File-Name", "")).strip()
                mime_type = "application/pdf"
                try:
                    file_url = FeedService.document_bytes_to_stored_url(raw, mime_type=mime_type, filename=filename)
                except FeedPayloadTooLargeError as error:
                    self._send_json(413, {"error": str(error)})
                    return
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                    return
                self._send_json(201, {"file_url": file_url})
                return

            self._send_json(
                400,
                {
                    "error": "Неподдерживаемый Content-Type для загрузки документа. Используйте multipart/form-data или application/pdf",
                },
            )
            return

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
            if str(cleaned.get("type", "")).strip() == "waybill" and not str(cleaned.get("status", "")).strip():
                cleaned["status"] = "open"
            if str(cleaned.get("type", "")).strip() == "waybill" and str(cleaned.get("status", "")).strip() == "uploaded":
                cleaned["status"] = "open"
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

        verification_prefix = "/api/feed/profiles/"
        if path.startswith(verification_prefix) and path.endswith("/verification/submit"):
            profile_id = path[len(verification_prefix) : -len("/verification/submit")].strip()
            if not profile_id:
                self._send_json(400, {"error": "Некорректный id профиля"})
                return
            actor = str(payload.get("actor", getattr(self, "write_auth_context", None).subject if getattr(self, "write_auth_context", None) else "anonymous")).strip() or "anonymous"
            try:
                updated = repository.apply_guest_profile_verification_action(profile_id=profile_id, action="submit", actor=actor)
            except ValueError as error:
                self._send_json(409, {"error": str(error)})
                return
            if not updated:
                self._send_json(404, {"error": "Профиль не найден"})
                return
            logger.info(
                "verification.transition",
                extra={
                    **self._request_log_extra(),
                    "verification_action": "submit",
                    "verification_profile_id": profile_id,
                    "verification_actor": actor,
                    "verification_to_state": str(updated.get("verification_state", "")),
                },
            )
            self._send_json(200, updated)
            return

        if path.startswith(verification_prefix) and (path.endswith("/verification/approve") or path.endswith("/verification/reject")):
            profile_id = path[len(verification_prefix) :]
            action = "approve" if profile_id.endswith("/verification/approve") else "reject"
            profile_id = profile_id[: -len(f"/verification/{action}")].strip()
            if not profile_id:
                self._send_json(400, {"error": "Некорректный id профиля"})
                return
            if not (getattr(self, "write_auth_context", None) and self.write_auth_context.is_moderator):
                self._send_json(403, {"error": "Недостаточно прав: требуется модератор"})
                return
            actor = str(payload.get("actor", getattr(self, "write_auth_context", None).subject if getattr(self, "write_auth_context", None) else "anonymous")).strip() or "anonymous"
            reason = str(payload.get("reason", "")).strip() or None
            try:
                updated = repository.apply_guest_profile_verification_action(
                    profile_id=profile_id,
                    action=action,
                    actor=actor,
                    reason=reason,
                )
            except ValueError as error:
                self._send_json(409, {"error": str(error)})
                return
            if not updated:
                self._send_json(404, {"error": "Профиль не найден"})
                return
            logger.info(
                "verification.transition",
                extra={
                    **self._request_log_extra(),
                    "verification_action": action,
                    "verification_profile_id": profile_id,
                    "verification_actor": actor,
                    "verification_reason_present": bool(reason),
                    "verification_to_state": str(updated.get("verification_state", "")),
                },
            )
            self._send_json(200, updated)
            return

        react_prefix = "/api/feed/posts/"
        react_path_suffix = "/react"
        reactions_path_suffix = "/reactions"
        if path.startswith(react_prefix) and (path.endswith(react_path_suffix) or path.endswith(reactions_path_suffix)):
            suffix = path[len(react_prefix) :]
            if suffix.endswith(reactions_path_suffix):
                post_id_raw = suffix[: -len(reactions_path_suffix)]
            else:
                post_id_raw = suffix[: -len(react_path_suffix)]
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id поста", "post_id_invalid")
                return
            try:
                item = FeedService.set_post_reaction(post_id=int(post_id_raw), payload=payload)
            except LookupError as error:
                self._send_interaction_error(404, str(error), "post_not_found")
                return
            except ValueError as error:
                self._send_interaction_error(400, str(error), "reaction_payload_invalid")
                return
            self._send_json(200, item)
            return

        comments_prefix = "/api/feed/posts/"
        if path.startswith(comments_prefix) and path.endswith("/comments"):
            suffix = path[len(comments_prefix) :]
            post_id_raw = suffix[: -len("/comments")]
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id поста", "post_id_invalid")
                return
            try:
                item = FeedService.create_guest_comment(post_id=int(post_id_raw), payload=payload)
            except LookupError as error:
                self._send_interaction_error(404, str(error), "post_not_found")
                return
            except ValueError as error:
                self._send_interaction_error(400, str(error), "comment_payload_invalid")
                return
            self._send_json(201, item)
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
        except FeedPayloadTooLargeError as error:
            self._send_json(413, {"error": str(error)})
            return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return

        self._send_json(201, item)

    def do_PATCH(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_patch)

    def _handle_patch(self) -> None:
        path = urlparse(self.path).path
        comment_prefix = "/api/feed/posts/"
        if path.startswith(comment_prefix) and "/comments/" in path:
            suffix = path[len(comment_prefix) :]
            post_id_raw, separator, comment_id_raw = suffix.partition("/comments/")
            if separator != "/comments/":
                self._send_json(404, {"error": "Not found"})
                return
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id поста", "post_id_invalid")
                return
            if not comment_id_raw.isdigit() or int(comment_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id комментария", "comment_id_invalid")
                return

            payload, error_payload, error_status = self._parse_feed_request_payload()
            if error_payload is not None:
                self._send_json(error_status, error_payload)
                return
            if payload is None:
                self._send_json(400, {"error": "Некорректный payload"})
                return
            payload["_actor_is_moderator"] = bool(getattr(self, "write_auth_context", None) and self.write_auth_context.is_moderator)

            try:
                updated = FeedService.update_guest_comment(
                    post_id=int(post_id_raw),
                    comment_id=int(comment_id_raw),
                    payload=payload,
                )
            except LookupError as error:
                self._send_interaction_error(404, str(error), "comment_not_found")
                return
            except FeedAccessDeniedError as error:
                self._send_interaction_error(403, str(error), "comment_edit_forbidden")
                return
            except ValueError as error:
                self._send_interaction_error(400, str(error), "comment_payload_invalid")
                return

            self._send_json(200, updated)
            return

        docs_prefix = "/api/driver/documents/"
        if path.startswith(docs_prefix):
            doc_suffix = path[len(docs_prefix) :]
            is_close_action = doc_suffix.endswith("/close")
            is_verification_approve_action = doc_suffix.endswith("/approve")
            is_verification_reject_action = doc_suffix.endswith("/reject")
            doc_id_raw = doc_suffix[:-len("/close")] if is_close_action else doc_suffix
            if is_verification_approve_action:
                doc_id_raw = doc_suffix[:-len("/approve")]
            if is_verification_reject_action:
                doc_id_raw = doc_suffix[:-len("/reject")]
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

            if is_close_action:
                closure_cleaned, closure_errors = FeedService.validate_waybill_close_payload(payload)
                if closure_errors:
                    self._send_json(400, {"error": "validation_error", "fields": closure_errors})
                    return
                try:
                    closed = repository.close_driver_waybill(int(doc_id_raw), closure_cleaned)
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                    return
                if not closed:
                    self._send_json(404, {"error": "Документ не найден"})
                    return
                self._send_json(200, closed)
                return

            if is_verification_approve_action or is_verification_reject_action:
                action = "approve" if is_verification_approve_action else "reject"
                actor = str(
                    payload.get(
                        "actor",
                        getattr(self, "write_auth_context", None).subject if getattr(self, "write_auth_context", None) else "system",
                    )
                ).strip() or "system"
                rejection_reason = str(payload.get("rejection_reason", "")).strip() or None
                try:
                    verified = repository.apply_driver_document_verification_action(
                        int(doc_id_raw),
                        action=action,
                        actor=actor,
                        rejection_reason=rejection_reason,
                    )
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                    return
                if not verified:
                    self._send_json(404, {"error": "Документ не найден"})
                    return
                self._send_json(200, verified)
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
        payload["_actor_is_moderator"] = bool(getattr(self, "write_auth_context", None) and self.write_auth_context.is_moderator)

        try:
            updated = FeedService.update_guest_post(int(post_id_raw), payload)
        except FeedPayloadTooLargeError as error:
            self._send_json(413, {"error": str(error)})
            return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        except LookupError as error:
            self._send_json(404, {"error": str(error)})
            return
        except FeedAccessDeniedError as error:
            self._send_json(403, {"error": str(error)})
            return

        self._send_json(200, updated)



    def do_DELETE(self) -> None:  # noqa: N802
        self._with_error_handling(self._handle_delete)

    def _handle_delete(self) -> None:
        path = urlparse(self.path).path
        posts_prefix = "/api/feed/posts/"
        react_path_suffix = "/react"
        reactions_path_suffix = "/reactions"
        if path.startswith(posts_prefix) and (path.endswith(react_path_suffix) or path.endswith(reactions_path_suffix)):
            if path.endswith(reactions_path_suffix):
                post_id_raw = path[len(posts_prefix) : -len(reactions_path_suffix)]
            else:
                post_id_raw = path[len(posts_prefix) : -len(react_path_suffix)]
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id поста", "post_id_invalid")
                return

            payload, error_payload, error_status = self._parse_feed_request_payload()
            if error_payload is not None:
                self._send_json(error_status, error_payload)
                return
            if payload is None:
                self._send_json(400, {"error": "Некорректный payload"})
                return

            try:
                item = FeedService.delete_post_reaction(post_id=int(post_id_raw), payload=payload)
            except LookupError as error:
                self._send_interaction_error(404, str(error), "post_not_found")
                return
            except ValueError as error:
                self._send_interaction_error(400, str(error), "reaction_payload_invalid")
                return

            self._send_json(200, item)
            return

        if path.startswith(posts_prefix) and "/comments/" in path:
            suffix = path[len(posts_prefix) :]
            post_id_raw, separator, comment_id_raw = suffix.partition("/comments/")
            if separator != "/comments/":
                self._send_json(404, {"error": "Not found"})
                return
            if not post_id_raw.isdigit() or int(post_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id поста", "post_id_invalid")
                return
            if not comment_id_raw.isdigit() or int(comment_id_raw) <= 0:
                self._send_interaction_error(400, "Некорректный id комментария", "comment_id_invalid")
                return

            payload, error_payload, error_status = self._parse_feed_request_payload()
            if error_payload is not None:
                self._send_json(error_status, error_payload)
                return
            if payload is None:
                self._send_json(400, {"error": "Некорректный payload"})
                return
            payload["_actor_is_moderator"] = bool(getattr(self, "write_auth_context", None) and self.write_auth_context.is_moderator)

            try:
                FeedService.delete_guest_comment(post_id=int(post_id_raw), comment_id=int(comment_id_raw), payload=payload)
            except LookupError as error:
                self._send_interaction_error(404, str(error), "comment_not_found")
                return
            except FeedAccessDeniedError as error:
                self._send_interaction_error(403, str(error), "comment_delete_forbidden")
                return

            self._send_json(200, {"ok": True})
            return

        if path.startswith(posts_prefix):
            post_id_raw = path[len(posts_prefix) :]
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
            payload["_actor_is_moderator"] = bool(getattr(self, "write_auth_context", None) and self.write_auth_context.is_moderator)

            try:
                FeedService.delete_guest_post(post_id=int(post_id_raw), payload=payload)
            except LookupError as error:
                self._send_json(404, {"error": str(error)})
                return
            except FeedAccessDeniedError as error:
                self._send_json(403, {"error": str(error)})
                return

            self._send_json(200, {"ok": True})
            return

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

    def _handle_driver_compliance_get(self) -> None:
        try:
            query = parse_qs(urlparse(self.path).query)
            profile_id = query.get("profile_id", ["driver-main"])[0]
            result = DriverComplianceService.evaluate(profile_id)
            self._send_json(200, {"ok": True, "data": result.to_dict()})
        except Exception:
            logger.exception("compliance get failed")
            self._send_internal_error()

    def _handle_driver_compliance_profile_upsert(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return

        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        try:
            profile_id = str(payload.get("profile_id", "driver-main")).strip() or "driver-main"
            repository.upsert_driver_compliance_profile(profile_id=profile_id, payload=payload)
            self._send_json(200, {"ok": True})
        except Exception:
            logger.exception("profile upsert failed")
            self._send_internal_error()

    def _handle_driver_document_upsert(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return

        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        doc_type = str(payload.get("type", "")).strip()
        number = str(payload.get("number", "")).strip()
        if not doc_type or not number:
            self._send_json(400, {"error": "Поля type и number обязательны"})
            return

        try:
            repository.upsert_driver_document(
                profile_id=str(payload.get("profile_id", "driver-main")).strip() or "driver-main",
                doc_type=doc_type,
                number=number,
                valid_until=payload.get("valid_until"),
                file_url=payload.get("file_url"),
                status=str(payload.get("status", "uploaded")),
            )
            self._send_json(200, {"ok": True})
        except Exception:
            logger.exception("document upsert failed")
            self._send_internal_error()

    def _handle_driver_compliance_check(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return

        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        try:
            profile_id = payload.get("profile_id", "driver-main")
            result = DriverComplianceService.evaluate(profile_id)
            self._send_json(
                200,
                {
                    "ok": True,
                    "can_accept_orders": result.can_accept_orders,
                    "can_go_online": result.can_go_online,
                    "status": result.status,
                    "reason": result.reason,
                },
            )
        except Exception:
            logger.exception("compliance check failed")
            self._send_internal_error()

    def _handle_driver_go_online(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return

        try:
            profile_id = payload.get("profile_id", "driver-main")
            result = DriverOperationService.go_online(profile_id)
            if not result.get("ok"):
                self._send_json(
                    403,
                    {
                        "ok": False,
                        "code": result.get("code", "DRIVER_NOT_ALLOWED"),
                        "reason": result.get("reason", "Нет допуска к выходу на линию"),
                        "actions": result.get("actions", []),
                    },
                )
                return
            self._send_json(200, result)
        except DriverNotAllowedError as e:
            self._send_json(
                403,
                {
                    "ok": False,
                    "code": e.code,
                    "reason": e.reason,
                    "actions": e.actions,
                },
            )
        except Exception:
            logger.exception("go-online failed")
            self._send_internal_error()

    def _handle_driver_accept_order(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return

        try:
            profile_id = payload.get("profile_id", "driver-main")
            order_id = payload.get("order_id")
            if not order_id:
                self._send_json(400, {"error": "order_id required"})
                return
            result = DriverOperationService.accept_order(order_id, profile_id)
            if not result.get("ok"):
                self._send_json(
                    403,
                    {
                        "ok": False,
                        "code": result.get("code", "DRIVER_NOT_ALLOWED"),
                        "reason": result.get("reason", "Нельзя принимать заказы"),
                        "actions": result.get("actions", []),
                    },
                )
                return
            self._send_json(200, result)
        except DriverNotAllowedError as e:
            self._send_json(
                403,
                {
                    "ok": False,
                    "code": e.code,
                    "reason": e.reason,
                    "actions": e.actions,
                },
            )
        except Exception:
            logger.exception("accept order failed")
            self._send_internal_error()

    def _handle_driver_assign_order(self) -> None:
        self._handle_driver_order_transition("assigned")

    def _handle_driver_complete_order(self) -> None:
        self._handle_driver_order_transition("completed")

    def _handle_driver_cancel_order(self) -> None:
        self._handle_driver_order_transition("canceled")

    def _handle_driver_order_transition(self, status: str) -> None:
        payload, error, response_status = self._parse_feed_request_payload()
        if error:
            self._send_json(response_status, error)
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return
        try:
            profile_id = str(payload.get("profile_id", "driver-main")).strip() or "driver-main"
            order_id = payload.get("order_id")
            if not order_id:
                self._send_json(400, {"error": "order_id required"})
                return
            if status == "assigned":
                result = DriverOperationService.assign_order(order_id, profile_id, payload)
            elif status == "completed":
                result = DriverOperationService.complete_order(order_id, profile_id, payload)
            else:
                result = DriverOperationService.cancel_order(order_id, profile_id, payload)
            self._send_json(200, result)
        except Exception:
            logger.exception("order transition failed")
            self._send_internal_error()

    def _handle_driver_order_journal_get(self, query: str) -> None:
        params = parse_qs(query)
        profile_id = str(params.get("profile_id", ["driver-main"])[0] or "driver-main").strip() or "driver-main"
        status_filter = str(params.get("status", [""])[0]).strip() or None
        date_from = str(params.get("date_from", [""])[0]).strip() or None
        date_to = str(params.get("date_to", [""])[0]).strip() or None
        try:
            limit = max(1, min(200, int(str(params.get("limit", ["100"])[0]))))
        except (TypeError, ValueError):
            limit = 100
        try:
            offset = max(0, int(str(params.get("offset", ["0"])[0])))
        except (TypeError, ValueError):
            offset = 0
        items = repository.list_order_journal_records(
            profile_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        self._send_json(
            200,
            {
                "items": items,
                "total": len(items),
                "profile_id": profile_id,
                "filters": {"status": status_filter, "date_from": date_from, "date_to": date_to},
            },
        )

    def _handle_driver_shift_open(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        try:
            profile_id = str(payload.get("profile_id", "driver-main")).strip() or "driver-main"
            vehicle_condition = str(payload.get("vehicle_condition", "")).strip()
            waybill_id = WaybillService.open_shift(
                profile_id=profile_id,
                vehicle_condition=vehicle_condition,
            )
            self._send_json(200, {"waybill_id": waybill_id})
        except ValueError as error:
            self._send_json(409, {"error": str(error)})
        except Exception:
            logger.exception("shift open failed")
            self._send_internal_error()

    def _handle_driver_shift_close(self) -> None:
        payload, error, status = self._parse_feed_request_payload()
        if error:
            self._send_json(status, error)
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        try:
            profile_id = str(payload.get("profile_id", "driver-main")).strip() or "driver-main"
            closure_cleaned, closure_errors = FeedService.validate_waybill_close_payload(payload)
            if closure_errors:
                self._send_json(400, {"error": "validation_error", "fields": closure_errors})
                return
            waybill_id = WaybillService.close_shift(
                profile_id=profile_id,
                data=closure_cleaned,
            )
            self._send_json(200, {"waybill_id": waybill_id})
        except ValueError as error:
            self._send_json(404, {"error": str(error)})
        except Exception:
            logger.exception("shift close failed")
            self._send_internal_error()

def run_api() -> None:
    configure_logging("feed-api")
    repository.init_db()
    settings = get_api_settings()
    host = settings.host
    port = settings.port
    server = ThreadingHTTPServer((host, port), FeedAPIHandler)
    logger.info("Feed API server started on http://%s:%s", host, port, extra={"request_id": "startup", "client_ip": "-"})
    server.serve_forever()
