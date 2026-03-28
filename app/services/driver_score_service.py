from __future__ import annotations

from app.services.driver_compliance_service import DriverComplianceService
from app.services.waybill_service import WaybillService


class DriverScoreService:
    @staticmethod
    def calculate(profile_id: str) -> dict[str, object]:
        score = 100
        reasons: list[str] = []

        compliance = DriverComplianceService.evaluate(profile_id)
        waybill = WaybillService.get_active_waybill(profile_id)

        if not waybill:
            score -= 40
            reasons.append("Нет смены")

        if compliance.missing_documents:
            score -= 30
            reasons.append("Нет документов")

        if compliance.expired_documents:
            score -= 30
            reasons.append("Просрочены документы")

        if compliance.expiring_documents:
            score -= 10
            reasons.append("Скоро истекают документы")

        return {
            "score": max(score, 0),
            "reasons": reasons,
        }
