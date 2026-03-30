class AuthorizationDenied(Exception):
    def __init__(self, code: str = "authorization_denied", message: str = "Access denied", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class PermissionDenied(AuthorizationDenied):
    def __init__(self, permission: str):
        super().__init__(code="permission_denied", message=f"Missing permission: {permission}")


class PolicyDenied(AuthorizationDenied):
    def __init__(self, reason: str):
        super().__init__(code="policy_denied", message=reason)
