from app.services.driver_compliance_service import ComplianceResult, DriverComplianceService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError
from app.services.waybill_service import WaybillService


class DriverGuardService:
    @staticmethod
    def ensure_can_go_online(profile_id: str) -> ComplianceResult:
        active_waybill = WaybillService.get_active_waybill(profile_id)
        if not active_waybill:
            raise DriverOfflineBlockedError(reason="Нет открытого путевого листа")

        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_go_online:
            raise DriverOfflineBlockedError(reason=result.reason or "Недостаточно данных для выхода на линию")

        return result

    @staticmethod
    def ensure_can_accept_order(profile_id: str) -> ComplianceResult:
        active_waybill = WaybillService.get_active_waybill(profile_id)
        if not active_waybill:
            raise DriverOrderBlockedError(reason="Нет открытого путевого листа")

        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_accept_orders:
            raise DriverOrderBlockedError(reason=result.reason or "Водитель не может принимать заказы")

        return result
