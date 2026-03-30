from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    PASSENGER = "passenger"
    DRIVER = "driver"
    MODERATOR = "moderator"
    ADMIN = "admin"


def normalize_role(value: str | None) -> UserRole | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    try:
        return UserRole(normalized)
    except ValueError:
        return None


def resolve_domain_role(transport_role: str | None) -> UserRole:
    normalized = str(transport_role or "").strip().lower()
    if normalized == "moderator":
        return UserRole.MODERATOR
    if normalized == "admin":
        return UserRole.ADMIN
    if normalized == "author":
        return UserRole.DRIVER
    return UserRole.GUEST
