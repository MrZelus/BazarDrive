from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    PASSENGER = "passenger"
    DRIVER = "driver"
    MODERATOR = "moderator"
    ADMIN = "admin"


def normalize_role(value: str | None) -> UserRole | None:
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    try:
        return UserRole(raw)
    except ValueError:
        return None


def is_privileged(role: UserRole | None) -> bool:
    return role in {UserRole.MODERATOR, UserRole.ADMIN}
