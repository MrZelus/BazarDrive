import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.driver_guard_service import DriverCapabilities, DriverGuardService
from app.services.driver_summary_service import DriverSummaryService


class DriverGuardServiceTests(unittest.TestCase):
    def test_get_capabilities_returns_soft_lock_when_accept_blocked(self) -> None:
        compliance = SimpleNamespace(can_go_online=True, can_accept_orders=False, reason="ОСАГО истекло")

        with patch(
            "app.services.driver_guard_service.WaybillService.get_active_waybill",
            return_value={"id": 1},
        ), patch(
            "app.services.driver_guard_service.DriverComplianceService.evaluate",
            return_value=compliance,
        ):
            caps = DriverGuardService.get_capabilities("driver-main")

        self.assertTrue(caps.can_go_online)
        self.assertFalse(caps.can_accept_orders)
        self.assertTrue(caps.can_complete_orders)
        self.assertEqual(caps.reason, "ОСАГО истекло")
        self.assertEqual(caps.code, "DRIVER_NOT_ALLOWED")
        self.assertEqual(caps.actions, [])

    def test_summary_returns_limited_mode_payload_for_soft_lock(self) -> None:
        compliance = SimpleNamespace(
            missing_documents=[],
            expired_documents=["osago"],
            expiring_documents=[],
            reason="ОСАГО истекло",
        )
        caps = DriverCapabilities(
            can_go_online=True,
            can_accept_orders=False,
            can_complete_orders=True,
            reason="ОСАГО истекло",
        )

        with patch(
            "app.services.driver_summary_service.DriverComplianceService.evaluate",
            return_value=compliance,
        ), patch(
            "app.services.driver_summary_service.DriverGuardService.get_capabilities",
            return_value=caps,
        ), patch(
            "app.services.driver_summary_service.DriverGuardService.get_mode",
            return_value="limited",
        ), patch(
            "app.services.driver_summary_service.WaybillService.get_active_waybill",
            return_value={"id": 1},
        ):
            summary = DriverSummaryService.build("driver-main")

        self.assertEqual(summary.level, "yellow")
        self.assertEqual(summary.title, "⚠️ Ограниченный режим")
        self.assertEqual(summary.reason, "ОСАГО истекло")


if __name__ == "__main__":
    unittest.main()
