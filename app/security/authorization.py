from __future__ import annotations

from .roles import UserRole
from .permissions import Permission, ROLE_PERMISSIONS
from .exceptions import PermissionDenied


class AuthorizationService:
    def has_role(self, role: UserRole, allowed_roles: set[UserRole]) -> bool:
        return role in allowed_roles

    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        if role == UserRole.ADMIN:
            return True
        return permission in ROLE_PERMISSIONS.get(role, set())

    def require_role(self, role: UserRole, allowed_roles: set[UserRole]) -> None:
        if not self.has_role(role, allowed_roles):
            raise PermissionDenied(f"role_required: {allowed_roles}")

    def require_permission(self, role: UserRole, permission: Permission) -> None:
        if not self.has_permission(role, permission):
            raise PermissionDenied(permission)


authz = AuthorizationService()
