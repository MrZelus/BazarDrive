from __future__ import annotations

from enum import Enum
from .roles import UserRole


class Permission(str, Enum):
    FEED_MODERATE = "feed.moderate"
    DOCUMENT_REVIEW = "document.review"
    DRIVER_GO_ONLINE = "driver.go_online"
    DRIVER_ACCEPT_ORDER = "driver.accept_order"
    DRIVER_SHIFT_OPEN = "driver.shift.open"
    DRIVER_DOCUMENT_UPLOAD = "driver.document.upload"
    USER_ROLE_MANAGE = "user.role.manage"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.GUEST: set(),
    UserRole.PASSENGER: set(),
    UserRole.DRIVER: {
        Permission.DRIVER_GO_ONLINE,
        Permission.DRIVER_ACCEPT_ORDER,
        Permission.DRIVER_SHIFT_OPEN,
        Permission.DRIVER_DOCUMENT_UPLOAD,
    },
    UserRole.MODERATOR: {
        Permission.FEED_MODERATE,
        Permission.DOCUMENT_REVIEW,
    },
    UserRole.ADMIN: set(Permission),
}
