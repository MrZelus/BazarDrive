from app.services.driver_compliance_service import DriverComplianceService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError
from app.services.waybill_service import WaybillService


class DriverGuardService:

    @staticmethod
    def ensure_can_go_online(profile_id: str):
        waybill = WaybillService.get_active_waybill(profile_id)

        if not waybill:
            raise DriverOfflineBlockedError("Нет открытого путевого листа (смена не начата)")

        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_go_online:
            raise DriverOfflineBlockedError(reason=result.reason or "Нет допуска к выходу на линию")

        return result

    @staticmethod
    def ensure_can_accept_order(profile_id: str):
        waybill = WaybillService.get_active_waybill(profile_id)

        if not waybill:
            raise DriverOrderBlockedError("Нет активной смены — нельзя принимать заказы")

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
        waybill = WaybillService.get_active_waybill(profile_id)
        result = DriverComplianceService.evaluate(profile_id)

        if not waybill:
            return "blocked"

        if not result.can_go_online:
            return "blocked"

        if not result.can_accept_orders:
            return "limited"

        return "normal"
