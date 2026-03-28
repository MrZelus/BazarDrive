from app.services.driver_compliance_service import ComplianceResult, DriverComplianceService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError
from app.services.driver_score_service import DriverScoreService
from app.services.waybill_service import WaybillService


class DriverGuardService:

    @staticmethod
    def get_mode(profile_id: str) -> str:
        score_payload = DriverScoreService.calculate(profile_id)
        score = int(score_payload.get("score", 0))

        if score < 40:
            return "blocked"
        if score < 70:
            return "limited"
        return "normal"

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
        mode = DriverGuardService.get_mode(profile_id)
        if mode != "normal":
            raise DriverOrderBlockedError(reason="Нельзя принимать новые заказы")

        active_waybill = WaybillService.get_active_waybill(profile_id)
        if not active_waybill:
            raise DriverOrderBlockedError(reason="Нет открытого путевого листа")

        result = DriverComplianceService.evaluate(profile_id)

        if not result.can_accept_orders:
            raise DriverOrderBlockedError(reason=result.reason or "Водитель не может принимать заказы")

        return result
