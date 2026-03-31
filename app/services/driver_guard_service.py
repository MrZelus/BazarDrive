from dataclasses import dataclass

from app.models.driver_error_codes import DriverErrorCode
from app.services.driver_compliance_service import DriverComplianceService
from app.services.exceptions import DriverOfflineBlockedError, DriverOrderBlockedError
from app.services.waybill_service import WaybillService


@dataclass
class DriverCapabilities:
    can_go_online: bool
    can_accept_orders: bool
    can_complete_orders: bool
    reason: str | None = None
    code: str = DriverErrorCode.DRIVER_NOT_ELIGIBLE.value
    actions: list[str] | None = None


class DriverGuardService:
    @staticmethod
    def _resolve_block_payload(compliance) -> tuple[str, list[str]]:
        status = str(getattr(compliance, "status", "") or "").strip()
        if status == "profile_incomplete":
            return DriverErrorCode.DRIVER_NOT_ELIGIBLE.value, ["Заполнить профиль"]
        if status == "docs_under_review":
            return DriverErrorCode.DRIVER_NOT_ELIGIBLE.value, ["Дождаться проверки документов"]
        if status == "expired_documents":
            return DriverErrorCode.REQUIRED_DOCUMENT_MISSING.value, ["Обновить документы"]
        if status == "waybill_required":
            return DriverErrorCode.TRIP_SHEET_REQUIRED.value, ["Открыть смену"]
        if status == "blocked":
            return DriverErrorCode.PROFILE_BLOCKED.value, ["Обратиться в поддержку"]
        return DriverErrorCode.DRIVER_NOT_ELIGIBLE.value, []

    @staticmethod
    def get_capabilities(profile_id: str) -> DriverCapabilities:
        waybill = WaybillService.get_active_waybill(profile_id)
        compliance = DriverComplianceService.evaluate(profile_id)

        if not waybill:
            return DriverCapabilities(
                can_go_online=False,
                can_accept_orders=False,
                can_complete_orders=False,
                reason="Нет открытого путевого листа",
                code=DriverErrorCode.TRIP_SHEET_REQUIRED.value,
                actions=["Открыть смену"],
            )

        if not compliance.can_go_online:
            code, actions = DriverGuardService._resolve_block_payload(compliance)
            return DriverCapabilities(
                can_go_online=False,
                can_accept_orders=False,
                can_complete_orders=False,
                reason=compliance.reason,
                code=code,
                actions=actions,
            )

        if not compliance.can_accept_orders:
            code, actions = DriverGuardService._resolve_block_payload(compliance)
            return DriverCapabilities(
                can_go_online=True,
                can_accept_orders=False,
                can_complete_orders=True,
                reason=compliance.reason,
                code=code,
                actions=actions,
            )

        return DriverCapabilities(
            can_go_online=True,
            can_accept_orders=True,
            can_complete_orders=True,
        )

    @staticmethod
    def ensure_can_go_online(profile_id: str):
        caps = DriverGuardService.get_capabilities(profile_id)
        if not caps.can_go_online:
            raise DriverOfflineBlockedError(
                reason=caps.reason or "Нельзя выйти на линию",
                code=caps.code,
                actions=caps.actions or [],
            )
        return caps

    @staticmethod
    def ensure_can_accept_order(profile_id: str):
        caps = DriverGuardService.get_capabilities(profile_id)
        if not caps.can_accept_orders:
            raise DriverOrderBlockedError(
                reason=caps.reason or "Нельзя принимать заказы",
                code=caps.code,
                actions=caps.actions or [],
            )
        return caps

    @staticmethod
    def get_mode(profile_id: str) -> str:
        """
        режим работы водителя:
        normal   — всё можно
        limited  — нельзя брать новые заказы
        blocked  — ничего нельзя
        """
        caps = DriverGuardService.get_capabilities(profile_id)
        if not caps.can_go_online:
            return "blocked"
        if not caps.can_accept_orders:
            return "limited"
        return "normal"
