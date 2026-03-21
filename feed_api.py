import base64
import binascii
import json
import os
import time
import uuid
from email.parser import BytesParser
from email.policy import default as default_policy
from math import ceil
from threading import Lock
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from db import (
    MAX_GUEST_FEED_IMAGE_URL_LENGTH,
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
    MAX_IMAGE_BYTES = 3 * 1024 * 1024
    STORAGE_DIR = os.path.abspath(os.getenv("FEED_UPLOAD_DIR", "storage/feed_images"))
    STORAGE_URL_PREFIX = "/uploads/feed/"
    SUPPORTED_IMAGE_MIME_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    _rate_limit_lock = Lock()
    _rate_limit_timestamps: dict[str, list[float]] = {}
    _rate_limit_expire_at: dict[str, float] = {}
    _rate_limit_last_cleanup_at = 0.0

    @staticmethod
    def _validate_image_url_metadata(payload: dict[str, object]) -> str | None:
        raw_value = payload.get("image_url")
        if raw_value is None:
            return None

        image_url = str(raw_value).strip()
        if not image_url:
            return None

        if len(image_url) > MAX_GUEST_FEED_IMAGE_URL_LENGTH:
            raise ValueError(
                f"Ссылка на изображение слишком длинная (максимум {MAX_GUEST_FEED_IMAGE_URL_LENGTH} символов)"
            )

        parsed = urlparse(image_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Некорректный формат image_url: поддерживаются только http/https URL")

        return image_url

    @classmethod
    def _ensure_storage_dir(cls) -> None:
        os.makedirs(cls.STORAGE_DIR, mode=0o700, exist_ok=True)

    @classmethod
    def _image_bytes_to_stored_url(cls, image_bytes: bytes, mime_type: str) -> str:
        extension = cls.SUPPORTED_IMAGE_MIME_TYPES.get(mime_type)
        if extension is None:
            raise ValueError(
                "Неподдерживаемый MIME-тип изображения. Допустимые значения: image/jpeg, image/png, image/webp"
            )

        if len(image_bytes) > cls.MAX_IMAGE_BYTES:
            raise ValueError(f"Изображение слишком большое (максимум {cls.MAX_IMAGE_BYTES} байт)")

        cls._ensure_storage_dir()
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = os.path.join(cls.STORAGE_DIR, filename)
        with open(destination, "xb") as file_obj:
            file_obj.write(image_bytes)

        return f"{cls.STORAGE_URL_PREFIX}{filename}"

    @classmethod
    def _extract_image_from_json_payload(cls, payload: dict[str, object]) -> str | None:
        image_base64_raw = payload.get("image_base64")
        if image_base64_raw is None:
            return None

        image_base64 = str(image_base64_raw).strip()
        if not image_base64:
            return None

        if image_base64.startswith("data:"):
            try:
                meta, encoded = image_base64.split(",", 1)
            except ValueError as error:
                raise ValueError("Некорректный формат image_base64 (ожидается data URL)") from error

            if ";base64" not in meta:
                raise ValueError("Некорректный формат image_base64: отсутствует ;base64")

            mime_type = meta[5:].split(";", 1)[0].strip().lower()
        else:
            mime_type = str(payload.get("image_mime_type", "")).strip().lower()
            if not mime_type:
                raise ValueError("Для image_base64 без data URL необходимо поле image_mime_type")
            encoded = image_base64

        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("Некорректный формат image_base64: неверная base64-строка") from error

        return cls._image_bytes_to_stored_url(image_bytes=image_bytes, mime_type=mime_type)

    @classmethod
    def _parse_multipart_form_data(cls, content_type: str, raw: bytes) -> dict[str, object]:
        if not raw:
            return {}

        envelope = (
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw
        )
        message = BytesParser(policy=default_policy).parsebytes(envelope)
        if not message.is_multipart():
            raise ValueError("Некорректный multipart/form-data")

        payload: dict[str, object] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition") or ""
            filename = part.get_filename()
            mime_type = part.get_content_type().lower()
            is_image_part = name in {"image", "photo"} or (filename and part.get_content_maintype() == "image")

            if is_image_part:
                image_bytes = part.get_payload(decode=True) or b""
                payload["image_url"] = cls._image_bytes_to_stored_url(image_bytes=image_bytes, mime_type=mime_type)
                continue

            if not name:
                continue

            value = part.get_payload(decode=True)
            if value is None:
                continue
            try:
                payload[name] = value.decode(part.get_content_charset() or "utf-8").strip()
            except UnicodeDecodeError as error:
                raise ValueError(f"Поле {name} содержит некорректные байты (ожидается текст UTF-8)") from error

        return payload

    @classmethod
    def _resolve_storage_path(cls, request_path: str) -> str | None:
        decoded_path = unquote(request_path)
        if not decoded_path.startswith(cls.STORAGE_URL_PREFIX):
            return None

        filename = decoded_path[len(cls.STORAGE_URL_PREFIX) :]
        if not filename:
            return None

        normalized = os.path.basename(filename)
        if normalized != filename:
            return None

        candidate = os.path.abspath(os.path.join(cls.STORAGE_DIR, normalized))
        if os.path.commonpath([candidate, cls.STORAGE_DIR]) != cls.STORAGE_DIR:
            return None

        return candidate

    def _serve_stored_file(self, request_path: str) -> bool:
        file_path = self._resolve_storage_path(request_path)
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
        self.end_headers()
        self.wfile.write(body)
        return True

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
                payload = self._parse_multipart_form_data(content_type=content_type_header, raw=raw)
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
            image_url = self._validate_image_url_metadata(payload)
            image_from_base64 = self._extract_image_from_json_payload(payload)
        except ValueError as error:
            return None, str(error)

        if image_url and image_from_base64:
            return None, "Укажите только одно поле изображения: image_url или image_base64"

        if image_from_base64:
            payload["image_url"] = image_from_base64
        elif image_url is not None:
            payload["image_url"] = image_url

        return payload, None

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

        if path.startswith(self.STORAGE_URL_PREFIX):
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

        payload, error = self._parse_feed_request_payload()
        if error:
            self._send_json(400, {"error": error})
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        author = str(payload.get("author", "")).strip()
        text = str(payload.get("text", "")).strip()
        image_url = str(payload.get("image_url", "")).strip() or None

        if not author or not text:
            self._send_json(400, {"error": "Поля author и text обязательны"})
            return

        if len(author) < 2:
            self._send_json(400, {"error": "Имя должно содержать минимум 2 символа"})
            return

        if len(text) < 5:
            self._send_json(400, {"error": "Сообщение должно содержать минимум 5 символов"})
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

        try:
            item = create_guest_feed_post(author, text, image_url=image_url)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
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

        payload, error = self._parse_feed_request_payload()
        if error:
            self._send_json(400, {"error": error})
            return
        if payload is None:
            self._send_json(400, {"error": "Некорректный payload"})
            return

        author = str(payload.get("author", "")).strip()
        text = str(payload.get("text", "")).strip()
        image_url = str(payload.get("image_url", "")).strip() or None

        if not author or not text:
            self._send_json(400, {"error": "Поля author и text обязательны"})
            return

        if len(author) < 2:
            self._send_json(400, {"error": "Имя должно содержать минимум 2 символа"})
            return

        if len(text) < 5:
            self._send_json(400, {"error": "Сообщение должно содержать минимум 5 символов"})
            return

        try:
            updated = update_guest_feed_post(post_id=post_id, author=author, text=text, image_url=image_url)
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
