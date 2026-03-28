from app.services.driver_compliance_service import DriverComplianceService


class DriverGuardError(Exception):
    def __init__(self, message: str, code: str = "driver_not_allowed"):
        super().__init__(message)
        self.code = code


class DriverGuard:
    @staticmethod
    def ensure_can_go_online(profile_id: str) -> None:
        result = DriverComplianceService.evaluate(profile_id)
        if not result.can_go_online:
            raise DriverGuardError(
                result.reason or "Водитель не допущен к выходу на линию",
                code="driver_cannot_go_online",
            )

    @staticmethod
    def ensure_can_accept_orders(profile_id: str) -> None:
        result = DriverComplianceService.evaluate(profile_id)
        if not result.can_accept_orders:
            raise DriverGuardError(
                result.reason or "Водитель не может принимать заказы",
                code="driver_cannot_accept_orders",
            )
