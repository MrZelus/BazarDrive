from __future__ import annotations

from dataclasses import dataclass

from app.services.driver_compliance_service import DriverComplianceService
from app.services.driver_guard_service import DriverGuardService
from app.services.driver_reminder_service import DriverReminderService


@dataclass
class DriverScore:
    score: int
    level: str  # green / yellow / red
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "level": self.level,
            "reasons": self.reasons,
        }


class DriverScoringService:
    BASE_SCORE = 100

    @classmethod
    def calculate(cls, profile_id: str) -> DriverScore:
        score = cls.BASE_SCORE
        reasons: list[str] = []

        compliance = DriverComplianceService.evaluate(profile_id)
        reminders = DriverReminderService.get_reminders(profile_id)
        mode = DriverGuardService.get_mode(profile_id)

        if mode == "blocked":
            score -= 40
            reasons.append("Водитель заблокирован")
        elif mode == "limited":
            score -= 20
            reasons.append("Ограниченный режим")

        if compliance.expired_documents:
            score -= 30
            reasons.append("Просроченные документы")

        if compliance.expiring_documents:
            score -= 10
            reasons.append("Скоро истекают документы")

        for reminder in reminders:
            if reminder.type == "waybill_open_too_long":
                score -= 10
                reasons.append("Смена долго не закрыта")

        score = max(0, min(100, score))

        if score >= 80:
            level = "green"
        elif score >= 50:
            level = "yellow"
        else:
            level = "red"

        return DriverScore(score=score, level=level, reasons=list(dict.fromkeys(reasons)))
