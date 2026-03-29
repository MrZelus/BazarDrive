class DriverNotAllowedError(Exception):
    def __init__(self, reason: str, code: str = "driver_not_allowed"):
        self.reason = reason
        self.code = code
        super().__init__(reason)


class DriverOfflineBlockedError(DriverNotAllowedError):
    pass


class DriverOrderBlockedError(DriverNotAllowedError):
    pass
