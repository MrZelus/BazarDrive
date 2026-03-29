from app.services.driver_compliance_service import DriverComplianceService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError


class DriverGuardService:

    @staticmethod
    def ensure_can_go_online(profile_id: str):
        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_go_online:
            raise DriverOfflineBlockedError(reason=result.reason or "Нет допуска к выходу на линию")

        return result

    @staticmethod
    def ensure_can_accept_order(profile_id: str):
        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_accept_orders:
            raise DriverOrderBlockedError(reason=result.reason or "Нельзя принимать заказы")

        return result

    @staticmethod
    def get_mode(profile_id: str) -> str:
        """
        режим работы водителя:
        normal   — всё можно
        limited  — нельзя брать новые заказы
        blocked  — ничего нельзя
        """
        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_go_online:
            return "blocked"

        if not result.can_accept_orders:
            return "limited"

        return "normal"
