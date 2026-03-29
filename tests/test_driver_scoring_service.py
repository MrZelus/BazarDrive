from types import SimpleNamespace
from unittest.mock import patch

from app.services.driver_scoring_service import DriverScoringService


def test_scoring_runs_without_crash() -> None:
    compliance = SimpleNamespace(expired_documents=[], expiring_documents=[])
    reminder = SimpleNamespace(type="waybill_open_too_long")
    with patch(
        "app.services.driver_scoring_service.DriverComplianceService.evaluate",
        return_value=compliance,
    ), patch(
        "app.services.driver_scoring_service.DriverReminderService.get_reminders",
        return_value=[reminder],
    ), patch(
        "app.services.driver_scoring_service.DriverGuardService.get_mode",
        return_value="limited",
    ):
        result = DriverScoringService.calculate("driver-main")
    assert isinstance(result.score, int)
