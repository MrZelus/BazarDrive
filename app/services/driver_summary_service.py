from dataclasses import dataclass
from typing import List

from app.services.driver_compliance_service import DriverComplianceService
from app.services.driver_guard_service import DriverGuardService
from app.services.driver_scoring_service import DriverScoringService
from app.services.waybill_service import WaybillService


@dataclass
class DriverSummary:
    level: str  # green / yellow / red
    title: str
    reason: str
    problems: List[str]
    actions: List[str]
    score: int | None = None
    score_level: str | None = None
    score_reasons: List[str] | None = None

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "title": self.title,
            "reason": self.reason,
            "problems": self.problems,
            "actions": self.actions,
            "score": self.score,
            "score_level": self.score_level,
            "score_reasons": self.score_reasons or [],
        }


class DriverSummaryService:
    @staticmethod
    def build(profile_id: str) -> DriverSummary:
        compliance = DriverComplianceService.evaluate(profile_id)
        caps = DriverGuardService.get_capabilities(profile_id)
        mode = DriverGuardService.get_mode(profile_id)
        waybill = WaybillService.get_active_waybill(profile_id)
        score = DriverScoringService.calculate(profile_id)

        problems: list[str] = []
        actions: list[str] = []

        if not waybill:
            problems.append("Нет открытого путевого листа")
            actions.append("Открыть смену")

        if compliance.missing_documents:
            problems.append("Не загружены обязательные документы")
            actions.append("Загрузить документы")

        if compliance.expired_documents:
            problems.append("Есть просроченные документы")
            if "Обновить документы" not in actions:
                actions.append("Обновить документы")

        if compliance.expiring_documents:
            problems.append("Есть документы с истекающим сроком")
            if "Проверить документы" not in actions:
                actions.append("Проверить документы")

        if mode == "blocked":
            return DriverSummary(
                level="red",
                title="⛔ Выход на линию запрещён",
                reason=compliance.reason or "Нет допуска к работе",
                problems=problems,
                actions=actions,
                score=score.score,
                score_level=score.level,
                score_reasons=score.reasons,
            )

        if not caps.can_accept_orders and caps.can_complete_orders:
            return DriverSummary(
                level="yellow",
                title="⚠️ Ограниченный режим",
                reason=caps.reason or "Нельзя принимать новые заказы",
                problems=problems,
                actions=actions,
                score=score.score,
                score_level=score.level,
                score_reasons=score.reasons,
            )

        if compliance.expiring_documents:
            return DriverSummary(
                level="yellow",
                title="⚠️ Требуется внимание",
                reason="Документы скоро истекают",
                problems=problems,
                actions=actions,
                score=score.score,
                score_level=score.level,
                score_reasons=score.reasons,
            )

        return DriverSummary(
            level="green",
            title="✅ Можно работать",
            reason="Все проверки пройдены",
            problems=[],
            actions=[],
            score=score.score,
            score_level=score.level,
            score_reasons=score.reasons,
        )
