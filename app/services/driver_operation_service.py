from app.services.driver_guard_service import DriverGuardService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError


class DriverOperationService:
    @staticmethod
    def go_online(driver_profile_id: str) -> dict[str, object]:
        try:
            DriverGuardService.ensure_can_go_online(driver_profile_id)
        except DriverOfflineBlockedError as error:
            return {"ok": False, "error": error.reason}

        return {
            "ok": True,
            "status": "online",
        }

    @staticmethod
    def accept_order(order_id: object, driver_profile_id: str) -> dict[str, object]:
        try:
            DriverGuardService.ensure_can_accept_order(driver_profile_id)
        except DriverOrderBlockedError as error:
            return {"ok": False, "error": error.reason}

        return {
            "ok": True,
            "order_id": order_id,
            "status": "accepted",
        }
