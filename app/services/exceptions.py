class DriverNotAllowedError(Exception):
    def __init__(self, reason: str, code: str = "driver_not_allowed"):
        self.reason = reason
        self.code = code
        super().__init__(reason)


class DriverOfflineBlockedError(DriverNotAllowedError):
    def __init__(self, reason: str, code: str = "driver_cannot_go_online"):
        super().__init__(reason=reason, code=code)


class DriverOrderBlockedError(DriverNotAllowedError):
    def __init__(self, reason: str, code: str = "driver_cannot_accept_orders"):
        super().__init__(reason=reason, code=code)
