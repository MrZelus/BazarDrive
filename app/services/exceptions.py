class DriverNotAllowedError(Exception):
    def __init__(self, reason: str, code: str = "DRIVER_NOT_ALLOWED", actions: list[str] | None = None):
        self.reason = reason
        self.code = code
        self.actions = list(actions or [])
        super().__init__(reason)


class DriverOfflineBlockedError(DriverNotAllowedError):
    pass


class DriverOrderBlockedError(DriverNotAllowedError):
    pass
