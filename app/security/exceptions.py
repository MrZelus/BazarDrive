class AuthorizationDenied(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class PermissionDenied(AuthorizationDenied):
    def __init__(self, permission: str):
        super().__init__(
            code="permission_denied",
            message=f"Permission '{permission}' is required",
            details={"permission": permission},
        )


class PolicyDenied(AuthorizationDenied):
    pass
