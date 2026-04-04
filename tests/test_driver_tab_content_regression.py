import unittest
from pathlib import Path


class DriverTabContentRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = Path("public/guest_feed.html").read_text(encoding="utf-8")
        self.script = Path("public/web/js/feed.js").read_text(encoding="utf-8")

    def _driver_tab_block(self) -> str:
        start_token = 'id="role-driver"'
        end_token = 'id="role-common"'
        start = self.html.find(start_token)
        end = self.html.find(end_token)
        self.assertNotEqual(start, -1, "Could not locate #role-driver block in public/guest_feed.html")
        self.assertNotEqual(end, -1, "Could not locate #role-common block in public/guest_feed.html")
        self.assertLess(start, end, "#role-driver block should be placed before #role-common")
        return self.html[start:end]

    def test_driver_tab_renders_expected_documents_content(self) -> None:
        block = self._driver_tab_block()
        self.assertIn("Профиль водителя", block)
        self.assertIn("Документы водителя", block)
        self.assertIn('id="driverOverviewDocuments"', block)
        self.assertIn('id="driverAddDocumentBtn"', block)
        self.assertIn("Добавить/обновить документы", block)
        self.assertIn("580-ФЗ", self.html)
        self.assertIn("ОСГОП", self.html)
        self.assertIn("Журнал заказов", self.html)

    def test_driver_tab_does_not_render_financial_block(self) -> None:
        block = self._driver_tab_block()
        forbidden_tokens = [
            "Доход за день",
            "Доход за неделю",
            "Доход за месяц",
            "Налоговый резерв",
            "Открыть выплаты",
        ]
        for token in forbidden_tokens:
            self.assertNotIn(token, block, f"Found forbidden finance token in driver tab: {token}")

    def test_feed_script_has_same_origin_api_fallback_without_query_param(self) -> None:
        self.assertIn("const locationOrigin = normalizeApiBase(window.location.origin);", self.script)
        self.assertIn("if (locationOrigin) return locationOrigin;", self.script)
        self.assertIn("const FEED_API_PREFIX = normalizeApiBase(FEED_API_BASE) === normalizeApiBase(window.location.origin) ? '' : FEED_API_BASE;", self.script)


if __name__ == "__main__":
    unittest.main()
