import base64
import binascii
import os
import time
import uuid
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default as default_policy
from math import ceil
from threading import Lock
from urllib.parse import urlparse

from app.config import get_feed_upload_dir
from app.db import repository
from app.models.feed import (
    ABOUT_MAX_LEN,
    ALLOWED_PROFILE_ROLES,
    ALLOWED_PROFILE_STATUSES,
    ALLOWED_DRIVER_DOCUMENT_STATUSES,
    ALLOWED_DRIVER_DOCUMENT_TYPES,
    AUTHOR_MAX_LEN,
    AUTHOR_MIN_LEN,
    DISPLAY_NAME_MAX_LEN,
    DISPLAY_NAME_MIN_LEN,
    EMAIL_MAX_LEN,
    LOCAL_IMAGE_PATH_PREFIX,
    MAX_GUEST_FEED_IMAGE_DATA_URL_LENGTH,
    MAX_GUEST_FEED_IMAGE_URL_LENGTH,
    PHONE_MAX_LEN,
    DRIVER_DOCUMENT_FILE_URL_MAX_LEN,
    DRIVER_DOCUMENT_NUMBER_MAX_LEN,
    DRIVER_DOCUMENT_NUMBER_MIN_LEN,
    TEXT_MAX_LEN,
    TEXT_MIN_LEN,
)


class FeedService:
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_MAX_POSTS_PER_IP = 8
    RATE_LIMIT_MAX_POSTS_PER_AUTHOR = 5
    RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = 30
    MAX_IMAGE_BYTES = 3 * 1024 * 1024
    STORAGE_DIR = os.path.abspath(get_feed_upload_dir())
    STORAGE_URL_PREFIX = "/uploads/feed/"
    SUPPORTED_IMAGE_MIME_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    MAX_URLS_PER_POST = 2
    MAX_DUPLICATE_TOKEN_OCCURRENCES = 4
    COMMENT_AUTHOR_MIN_LEN = AUTHOR_MIN_LEN
    COMMENT_AUTHOR_MAX_LEN = AUTHOR_MAX_LEN
    COMMENT_TEXT_MIN_LEN = 1
    COMMENT_TEXT_MAX_LEN = 300
    MODERATOR_ROLES = {"moderator", "admin"}
    ALLOWED_REACTION_TYPES = {"like", "dislike", "fire", "heart", "laugh", "wow"}
    FORBIDDEN_PATTERNS = (
        ("казино", "Контент с упоминанием азартных игр запрещён правилами публикации."),
        ("наркот", "Контент с упоминанием запрещённых веществ не допускается."),
        ("ставк", "Публикации с рекламой ставок и букмекерских услуг запрещены."),
        ("18+", "Контент 18+ запрещён в гостевой ленте."),
    )

    _rate_limit_lock = Lock()
    _rate_limit_timestamps: dict[str, list[float]] = {}
    _rate_limit_expire_at: dict[str, float] = {}
    _rate_limit_last_cleanup_at = 0.0

    @staticmethod
    def validate_image_url_metadata(payload: dict[str, object]) -> str | None:
        raw_value = payload.get("image_url")
        if raw_value is None:
            return None
        image_url = str(raw_value).strip()
        if not image_url:
            return None

        if image_url.startswith("data:"):
            if len(image_url) > MAX_GUEST_FEED_IMAGE_DATA_URL_LENGTH:
                raise ValueError(
                    f"Изображение в формате data URL слишком большое (максимум {MAX_GUEST_FEED_IMAGE_DATA_URL_LENGTH} символов)"
                )
            return image_url

        if image_url.startswith(LOCAL_IMAGE_PATH_PREFIX):
            if len(image_url) > MAX_GUEST_FEED_IMAGE_URL_LENGTH:
                raise ValueError(
                    f"Локальный путь изображения слишком длинный (максимум {MAX_GUEST_FEED_IMAGE_URL_LENGTH} символов)"
                )
            return image_url

        if len(image_url) > MAX_GUEST_FEED_IMAGE_URL_LENGTH:
            raise ValueError(f"Ссылка на изображение слишком длинная (максимум {MAX_GUEST_FEED_IMAGE_URL_LENGTH} символов)")

        parsed = urlparse(image_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Некорректный формат image_url: поддерживаются только http/https URL")
        return image_url

    @classmethod
    def ensure_storage_dir(cls) -> None:
        os.makedirs(cls.STORAGE_DIR, mode=0o700, exist_ok=True)

    @classmethod
    def image_bytes_to_stored_url(cls, image_bytes: bytes, mime_type: str) -> str:
        extension = cls.SUPPORTED_IMAGE_MIME_TYPES.get(mime_type)
        if extension is None:
            raise ValueError("Неподдерживаемый MIME-тип изображения. Допустимые значения: image/jpeg, image/png, image/webp")
        if len(image_bytes) > cls.MAX_IMAGE_BYTES:
            raise ValueError(f"Изображение слишком большое (максимум {cls.MAX_IMAGE_BYTES} байт)")

        cls.ensure_storage_dir()
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = os.path.join(cls.STORAGE_DIR, filename)
        with open(destination, "xb") as file_obj:
            file_obj.write(image_bytes)
        return f"{cls.STORAGE_URL_PREFIX}{filename}"

    @classmethod
    def extract_image_from_json_payload(cls, payload: dict[str, object]) -> str | None:
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

        return cls.image_bytes_to_stored_url(image_bytes=image_bytes, mime_type=mime_type)

    @classmethod
    def parse_multipart_form_data(cls, content_type: str, raw: bytes) -> dict[str, object]:
        if not raw:
            return {}
        envelope = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw
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
                payload["image_url"] = cls.image_bytes_to_stored_url(image_bytes=image_bytes, mime_type=mime_type)
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
    def resolve_storage_path(cls, request_path: str) -> str | None:
        from urllib.parse import unquote
        import os.path

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

    @staticmethod
    def isoformat_timestamp(value: object) -> object:
        if not isinstance(value, str):
            return value
        raw = value.strip()
        if not raw:
            return raw
        normalized = raw.replace(" ", "T")
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
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

    @classmethod
    def serialize_payload(cls, payload: object) -> object:
        if isinstance(payload, dict):
            result: dict[str, object] = {}
            for key, value in payload.items():
                result[key] = cls.isoformat_timestamp(value) if key in {"created_at", "updated_at"} else cls.serialize_payload(value)
            return result
        if isinstance(payload, list):
            return [cls.serialize_payload(item) for item in payload]
        return payload

    @staticmethod
    def _normalize_author(author: str) -> str:
        return " ".join(author.casefold().split())

    @staticmethod
    def _cleanup_rate_limit_locked(now: float) -> None:
        cls = FeedService
        if now - cls._rate_limit_last_cleanup_at < cls.RATE_LIMIT_CLEANUP_INTERVAL_SECONDS:
            return
        expired = [key for key, expires_at in cls._rate_limit_expire_at.items() if expires_at <= now]
        for key in expired:
            cls._rate_limit_expire_at.pop(key, None)
            cls._rate_limit_timestamps.pop(key, None)
        cls._rate_limit_last_cleanup_at = now

    @staticmethod
    def _consume_rate_limit_token_locked(key: str, limit: int, now: float) -> int:
        cls = FeedService
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
    def check_rate_limit(cls, ip: str, author: str) -> int:
        author_key = cls._normalize_author(author)
        now = time.monotonic()
        with cls._rate_limit_lock:
            cls._cleanup_rate_limit_locked(now)
            ip_retry = cls._consume_rate_limit_token_locked(f"ip:{ip}", cls.RATE_LIMIT_MAX_POSTS_PER_IP, now)
            author_retry = cls._consume_rate_limit_token_locked(
                f"author:{author_key}", cls.RATE_LIMIT_MAX_POSTS_PER_AUTHOR, now
            ) if author_key else 0
        return max(ip_retry, author_retry)

    @staticmethod
    def validate_post_fields(author: str, text: str) -> tuple[str, str]:
        author_clean = author.strip()
        text_clean = text.strip()
        if not author_clean or not text_clean:
            raise ValueError("Поля author и text обязательны")
        if len(author_clean) < AUTHOR_MIN_LEN:
            raise ValueError("Имя должно содержать минимум 2 символа")
        if len(text_clean) < TEXT_MIN_LEN:
            raise ValueError("Сообщение должно содержать минимум 5 символов")
        if len(author_clean) > AUTHOR_MAX_LEN or len(text_clean) > TEXT_MAX_LEN:
            raise ValueError("Превышена максимальная длина полей")
        FeedService.validate_publication_rules(text_clean)
        return author_clean, text_clean

    @classmethod
    def get_publication_rules(cls) -> dict[str, object]:
        return {
            "title": "Правила публикации в гостевой ленте",
            "version": 1,
            "rules": [
                {"id": "no-spam", "text": "Не публикуйте однотипные повторяющиеся сообщения и флуд."},
                {"id": "no-prohibited", "text": "Запрещены наркотики, ставки/казино и контент 18+."},
                {"id": "links-limit", "text": f"Допускается не более {cls.MAX_URLS_PER_POST} ссылок в одном посте."},
                {
                    "id": "meaningful-text",
                    "text": "Текст должен быть осмысленным: избегайте длинных цепочек из одинаковых слов/символов.",
                },
            ],
        }

    @classmethod
    def validate_publication_rules(cls, text: str) -> None:
        lowered = text.casefold()
        for marker, message in cls.FORBIDDEN_PATTERNS:
            if marker in lowered:
                raise ValueError(message)

        links_count = lowered.count("http://") + lowered.count("https://")
        if links_count > cls.MAX_URLS_PER_POST:
            raise ValueError(f"Слишком много ссылок в одном посте (максимум {cls.MAX_URLS_PER_POST}).")

        tokens = [token for token in lowered.split() if len(token) >= 3]
        if tokens:
            frequencies: dict[str, int] = {}
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
            if max(frequencies.values()) > cls.MAX_DUPLICATE_TOKEN_OCCURRENCES:
                raise ValueError("Пост выглядит как спам: слишком много повторяющихся слов.")

    @staticmethod
    def validate_profile_fields(payload: dict[str, object]) -> dict[str, object]:
        profile_id = str(payload.get("id", "")).strip()
        display_name = str(payload.get("display_name", "")).strip()
        email = str(payload.get("email", "")).strip() or None
        phone = str(payload.get("phone", "")).strip() or None
        about = str(payload.get("about", "")).strip() or None
        role = str(payload.get("role", "guest_author")).strip() or "guest_author"
        status = str(payload.get("status", "active")).strip() or "active"
        is_verified = bool(payload.get("is_verified", False))

        if len(profile_id) < 8:
            raise ValueError("Некорректный id профиля")
        if len(display_name) < DISPLAY_NAME_MIN_LEN:
            raise ValueError("display_name должен содержать минимум 2 символа")
        if len(display_name) > DISPLAY_NAME_MAX_LEN:
            raise ValueError("display_name слишком длинный (максимум 60 символов)")
        if not email and not phone:
            raise ValueError("Укажите email или phone")
        if email and len(email) > EMAIL_MAX_LEN:
            raise ValueError("email слишком длинный")
        if phone and len(phone) > PHONE_MAX_LEN:
            raise ValueError("phone слишком длинный")
        if about and len(about) > ABOUT_MAX_LEN:
            raise ValueError("about слишком длинный (максимум 400 символов)")
        if role not in ALLOWED_PROFILE_ROLES:
            raise ValueError("Некорректное значение role")
        if status not in ALLOWED_PROFILE_STATUSES:
            raise ValueError("Некорректное значение status")

        return {
            "profile_id": profile_id,
            "display_name": display_name,
            "email": email,
            "phone": phone,
            "about": about,
            "role": role,
            "status": status,
            "is_verified": is_verified,
        }



    @classmethod
    def validate_reaction_type(cls, reaction_type: str) -> str:
        normalized = reaction_type.strip().lower()
        if normalized not in cls.ALLOWED_REACTION_TYPES:
            allowed = ", ".join(sorted(cls.ALLOWED_REACTION_TYPES))
            raise ValueError(f"Некорректный тип реакции. Допустимые значения: {allowed}")
        return normalized

    @classmethod
    def enrich_posts_with_reactions(
        cls,
        posts: list[dict[str, object]],
        guest_profile_id: str | None = None,
    ) -> list[dict[str, object]]:
        if not posts:
            return posts

        post_ids = [int(post.get("id", 0)) for post in posts if int(post.get("id", 0)) > 0]
        aggregated = repository.aggregate_guest_feed_reactions(post_ids)
        my_reactions = repository.get_guest_feed_my_reactions(post_ids, guest_profile_id or "")

        for post in posts:
            post_id = int(post.get("id", 0))
            post_reactions = dict(aggregated.get(post_id, {}))
            post["reactions"] = post_reactions
            post["likes"] = int(post_reactions.get("like", 0))
            post["my_reaction"] = my_reactions.get(post_id)

        return posts

    @classmethod
    def get_post_reactions(cls, post_id: int, guest_profile_id: str | None = None) -> dict[str, object]:
        post = repository.get_guest_feed_post(post_id)
        if not post:
            raise LookupError("Пост не найден")

        reactions = repository.aggregate_guest_feed_reactions([post_id]).get(post_id, {})
        my_reaction = repository.get_guest_feed_post_my_reaction(post_id, guest_profile_id or "")
        return {
            "post_id": post_id,
            "reactions": reactions,
            "likes": int(reactions.get("like", 0)),
            "my_reaction": my_reaction,
        }

    @classmethod
    def set_post_reaction(cls, post_id: int, payload: dict[str, object]) -> dict[str, object]:
        post = repository.get_guest_feed_post(post_id)
        if not post:
            raise LookupError("Пост не найден")

        guest_profile_id = str(payload.get("guest_profile_id", "")).strip()
        if not guest_profile_id:
            raise ValueError("Поле guest_profile_id обязательно")

        reaction_type = cls.validate_reaction_type(str(payload.get("type", payload.get("reaction_type", ""))))
        current = repository.get_guest_feed_post_my_reaction(post_id, guest_profile_id)

        if current != reaction_type:
            repository.set_guest_feed_reaction(post_id=post_id, guest_profile_id=guest_profile_id, reaction_type=reaction_type)

        return cls.get_post_reactions(post_id=post_id, guest_profile_id=guest_profile_id)

    @classmethod
    def delete_post_reaction(cls, post_id: int, payload: dict[str, object]) -> dict[str, object]:
        post = repository.get_guest_feed_post(post_id)
        if not post:
            raise LookupError("Пост не найден")

        guest_profile_id = str(payload.get("guest_profile_id", "")).strip()
        if not guest_profile_id:
            raise ValueError("Поле guest_profile_id обязательно")

        repository.delete_guest_feed_reaction(post_id=post_id, guest_profile_id=guest_profile_id)
        return cls.get_post_reactions(post_id=post_id, guest_profile_id=guest_profile_id)

    @staticmethod
    def validate_driver_document_fields(payload: dict[str, object]) -> tuple[dict[str, object], dict[str, str]]:
        profile_id = str(payload.get("profile_id", "driver-main")).strip() or "driver-main"
        document_type = str(payload.get("type", "")).strip()
        number = str(payload.get("number", "")).strip()
        valid_until = str(payload.get("valid_until", "")).strip() or None
        file_url = str(payload.get("file_url", "")).strip() or None
        status = str(payload.get("status", "uploaded")).strip() or "uploaded"

        errors: dict[str, str] = {}

        if document_type not in ALLOWED_DRIVER_DOCUMENT_TYPES:
            errors["type"] = "Некорректный тип документа"
        if len(number) < DRIVER_DOCUMENT_NUMBER_MIN_LEN:
            errors["number"] = "Номер документа должен содержать минимум 3 символа"
        if len(number) > DRIVER_DOCUMENT_NUMBER_MAX_LEN:
            errors["number"] = "Номер документа слишком длинный"
        if valid_until:
            try:
                datetime.strptime(valid_until, "%Y-%m-%d")
            except ValueError:
                errors["valid_until"] = "Дата должна быть в формате YYYY-MM-DD"
        if file_url and len(file_url) > DRIVER_DOCUMENT_FILE_URL_MAX_LEN:
            errors["file_url"] = "Ссылка на файл слишком длинная"
        if status not in ALLOWED_DRIVER_DOCUMENT_STATUSES:
            errors["status"] = "Некорректный статус документа"

        cleaned = {
            "profile_id": profile_id,
            "type": document_type,
            "number": number,
            "valid_until": valid_until,
            "file_url": file_url,
            "status": status,
        }
        return cleaned, errors

    @staticmethod
    def extract_profile_payload(payload: dict[str, object]) -> dict[str, object]:
        profile_raw = payload.get("guest_profile")
        return profile_raw if isinstance(profile_raw, dict) else {}

    @classmethod
    def create_guest_post(cls, payload: dict[str, object], client_ip: str) -> dict[str, object]:
        author, text = cls.validate_post_fields(str(payload.get("author", "")), str(payload.get("text", "")))
        image_url = str(payload.get("image_url", "")).strip() or None

        retry_after = cls.check_rate_limit(client_ip, author)
        if retry_after > 0:
            raise RuntimeError(str(retry_after))

        guest_profile = cls.extract_profile_payload(payload)
        guest_profile_id = str(guest_profile.get("id", "")).strip() if guest_profile else None
        if guest_profile:
            profile_data = cls.validate_profile_fields(guest_profile)
            repository.upsert_guest_profile(**profile_data)
            guest_profile_id = profile_data["profile_id"]

        return repository.create_guest_feed_post(author=author, text=text, image_url=image_url, guest_profile_id=guest_profile_id)

    @classmethod
    def update_guest_post(cls, post_id: int, payload: dict[str, object]) -> dict[str, object] | None:
        author, text = cls.validate_post_fields(str(payload.get("author", "")), str(payload.get("text", "")))
        image_url = str(payload.get("image_url", "")).strip() or None
        guest_profile_id = str(payload.get("guest_profile_id", "")).strip() or None
        return repository.update_guest_feed_post(post_id=post_id, author=author, text=text, image_url=image_url, guest_profile_id=guest_profile_id)

    @classmethod
    def validate_comment_fields(cls, author: str, text: str) -> tuple[str, str]:
        author_clean = author.strip()
        text_clean = text.strip()
        if not author_clean or not text_clean:
            raise ValueError("Поля author и text обязательны")
        if len(author_clean) < cls.COMMENT_AUTHOR_MIN_LEN:
            raise ValueError(f"Имя должно содержать минимум {cls.COMMENT_AUTHOR_MIN_LEN} символа")
        if len(author_clean) > cls.COMMENT_AUTHOR_MAX_LEN:
            raise ValueError(f"Имя слишком длинное (максимум {cls.COMMENT_AUTHOR_MAX_LEN} символов)")
        if len(text_clean) < cls.COMMENT_TEXT_MIN_LEN:
            raise ValueError(f"Комментарий должен содержать минимум {cls.COMMENT_TEXT_MIN_LEN} символ")
        if len(text_clean) > cls.COMMENT_TEXT_MAX_LEN:
            raise ValueError(f"Комментарий слишком длинный (максимум {cls.COMMENT_TEXT_MAX_LEN} символов)")
        cls.validate_publication_rules(text_clean)
        return author_clean, text_clean

    @classmethod
    def _is_moderator_profile(cls, guest_profile_id: str) -> bool:
        profile = repository.get_guest_profile(guest_profile_id)
        if not profile:
            return False
        role = str(profile.get("role", "")).strip().lower()
        return role in cls.MODERATOR_ROLES

    @classmethod
    def can_manage_post(cls, post: dict[str, object], actor_guest_profile_id: str) -> bool:
        normalized_actor = actor_guest_profile_id.strip()
        if not normalized_actor:
            return False
        author_profile_id = str(post.get("guest_profile_id", "")).strip()
        return normalized_actor == author_profile_id or cls._is_moderator_profile(normalized_actor)

    @classmethod
    def can_manage_comment(cls, comment: dict[str, object], actor_guest_profile_id: str) -> bool:
        normalized_actor = actor_guest_profile_id.strip()
        if not normalized_actor:
            return False
        author_profile_id = str(comment.get("guest_profile_id", "")).strip()
        return normalized_actor == author_profile_id or cls._is_moderator_profile(normalized_actor)

    @classmethod
    def delete_guest_post(cls, post_id: int, payload: dict[str, object]) -> bool:
        post = repository.get_guest_feed_post(post_id)
        if not post:
            raise LookupError("Пост не найден")
        actor_guest_profile_id = str(payload.get("guest_profile_id", "")).strip()
        if not actor_guest_profile_id:
            raise PermissionError("Недостаточно прав для удаления поста")
        if not cls.can_manage_post(post, actor_guest_profile_id):
            raise PermissionError("Недостаточно прав для удаления поста")
        deleted = repository.delete_guest_feed_post(post_id=post_id)
        if not deleted:
            raise LookupError("Пост не найден")
        return True

    @classmethod
    def create_guest_comment(cls, post_id: int, payload: dict[str, object]) -> dict[str, object]:
        if not repository.get_guest_feed_post(post_id):
            raise LookupError("Пост не найден")
        author, text = cls.validate_comment_fields(str(payload.get("author", "")), str(payload.get("text", "")))
        guest_profile_id = str(payload.get("guest_profile_id", "")).strip() or None
        return repository.create_guest_feed_comment(
            post_id=post_id,
            guest_profile_id=guest_profile_id,
            author=author,
            text=text,
        )

    @staticmethod
    def list_guest_comments(post_id: int, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
        if not repository.get_guest_feed_post(post_id):
            raise LookupError("Пост не найден")
        return repository.list_guest_feed_comments(post_id=post_id, limit=limit, offset=offset)

    @classmethod
    def update_guest_comment(cls, post_id: int, comment_id: int, payload: dict[str, object]) -> dict[str, object]:
        if not repository.get_guest_feed_post(post_id):
            raise LookupError("Пост не найден")
        comment = repository.get_guest_feed_comment(comment_id)
        if not comment or int(comment.get("post_id", 0)) != post_id:
            raise LookupError("Комментарий не найден")

        actor_guest_profile_id = str(payload.get("guest_profile_id", "")).strip()
        if not actor_guest_profile_id:
            raise PermissionError("Недостаточно прав для изменения комментария")
        if not cls.can_manage_comment(comment, actor_guest_profile_id):
            raise PermissionError("Недостаточно прав для изменения комментария")

        text = str(payload.get("text", "")).strip()
        if not text:
            raise ValueError("Поле text обязательно")
        if len(text) > cls.COMMENT_TEXT_MAX_LEN:
            raise ValueError(f"Комментарий слишком длинный (максимум {cls.COMMENT_TEXT_MAX_LEN} символов)")
        cls.validate_publication_rules(text)

        updated = repository.update_guest_feed_comment(comment_id=comment_id, text=text)
        if not updated:
            raise LookupError("Комментарий не найден")
        return updated

    @classmethod
    def delete_guest_comment(cls, post_id: int, comment_id: int, payload: dict[str, object]) -> bool:
        if not repository.get_guest_feed_post(post_id):
            raise LookupError("Пост не найден")
        comment = repository.get_guest_feed_comment(comment_id)
        if not comment or int(comment.get("post_id", 0)) != post_id:
            raise LookupError("Комментарий не найден")
        actor_guest_profile_id = str(payload.get("guest_profile_id", "")).strip()
        if not actor_guest_profile_id:
            raise PermissionError("Недостаточно прав для удаления комментария")
        if not cls.can_manage_comment(comment, actor_guest_profile_id):
            raise PermissionError("Недостаточно прав для удаления комментария")
        return repository.delete_guest_feed_comment(comment_id=comment_id)
