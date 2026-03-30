from __future__ import annotations

from enum import Enum
from .roles import UserRole


class Permission(str, Enum):
    FEED_MODERATE = "feed.moderate"
    PUBLICATION_PROFILE_REVIEW = "publication_profile.review"
    DRIVER_DOCUMENT_REVIEW = "driver_document.review"

    DRIVER_GO_ONLINE = "driver.go_online"
    DRIVER_ACCEPT_ORDER = "driver.accept_order"
    DRIVER_SHIFT_OPEN = "driver.shift.open"
    DRIVER_DOCUMENT_UPLOAD = "driver_document.upload"

    TAXI_ORDER_CREATE = "taxi_order.create"

    USER_ROLE_MANAGE = "user.role.manage"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.GUEST: set(),
    UserRole.PASSENGER: {
        Permission.TAXI_ORDER_CREATE,
    },
    UserRole.DRIVER: {
        Permission.DRIVER_GO_ONLINE,
        Permission.DRIVER_ACCEPT_ORDER,
        Permission.DRIVER_SHIFT_OPEN,
        Permission.DRIVER_DOCUMENT_UPLOAD,
    },
    UserRole.MODERATOR: {
        Permission.FEED_MODERATE,
        Permission.PUBLICATION_PROFILE_REVIEW,
        Permission.DRIVER_DOCUMENT_REVIEW,
    },
    UserRole.ADMIN: set(Permission),
}


def role_has_permission(role: UserRole | None, permission: Permission) -> bool:
    if role is None:
        return False
    if role == UserRole.ADMIN:
        return True
    return permission in ROLE_PERMISSIONS.get(role, set())
