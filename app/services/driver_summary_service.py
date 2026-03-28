from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.driver_compliance_service import DriverComplianceService
from app.services.waybill_service import WaybillService


@dataclass
class DriverSummary:
    level: str
    title: str
    reason: str
    problems: list[str]
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "title": self.title,
            "reason": self.reason,
            "problems": self.problems,
            "actions": self.actions,
        }


class DriverSummaryService:
    @staticmethod
    def build(profile_id: str) -> DriverSummary:
        compliance = DriverComplianceService.evaluate(profile_id)
        waybill = WaybillService.get_active_waybill(profile_id)

        problems: list[str] = []
        actions: list[str] = []

        if not waybill:
            problems.append("Нет открытого путевого листа")
            actions.append("Открыть смену")

        if compliance.missing_documents:
            problems.append("Не все документы загружены")
            actions.append("Загрузить документы")

        if compliance.expired_documents:
            problems.append("Есть просроченные документы")
            actions.append("Обновить документы")

        if compliance.expiring_documents:
            expiring_list = ", ".join(sorted(compliance.expiring_documents))
            problems.append(f"Скоро истекают документы: {expiring_list}")
            actions.append("Проверить сроки и обновить документы")

        if not waybill or not compliance.can_go_online:
            return DriverSummary(
                level="red",
                title="⛔ Выход на линию запрещён",
                reason=compliance.reason or "Нет допуска",
                problems=problems,
                actions=actions,
            )

        if compliance.expiring_documents:
            return DriverSummary(
                level="yellow",
                title="⚠️ Требуется внимание",
                reason="Документы скоро истекают",
                problems=problems,
                actions=actions,
            )

        return DriverSummary(
            level="green",
            title="✅ Можно работать",
            reason="Все проверки пройдены",
            problems=[],
            actions=[],
        )
