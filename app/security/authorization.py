from __future__ import annotations

from .roles import UserRole
from .permissions import Permission, role_has_permission
from .exceptions import PermissionDenied


class AuthorizationService:
    @staticmethod
    def has_role(role: UserRole | None, allowed: set[UserRole]) -> bool:
        return role in allowed

    @staticmethod
    def has_permission(role: UserRole | None, permission: Permission) -> bool:
        return role_has_permission(role, permission)

    @staticmethod
    def require_permission(role: UserRole | None, permission: Permission) -> None:
        if not role_has_permission(role, permission):
            raise PermissionDenied(permission.value)


# Singleton-like helper

authz = AuthorizationService()
