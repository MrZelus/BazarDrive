import unittest
from pathlib import Path


class DocumentsTrustDocsSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = Path("README.md").read_text(encoding="utf-8")
        self.publish_flow_doc = Path("docs/feed_navigation_publish_flow.md").read_text(encoding="utf-8")
        self.wireframe_doc = Path("docs/driver_profile_wireframe_spec.md").read_text(encoding="utf-8")
        self.plan_doc = Path("docs/issues/172-documents-trust-automation-plan.md").read_text(encoding="utf-8")

    def test_document_statuses_are_present_in_readme_and_spec(self) -> None:
        statuses = ["uploaded", "checking", "approved", "rejected", "expired"]
        for status in statuses:
            self.assertIn(status, self.readme)
            self.assertIn(status, self.wireframe_doc)

    def test_publish_flow_doc_covers_role_visibility_requirements(self) -> None:
        self.assertIn("блок профиля публикации для всех ролей", self.publish_flow_doc)
        self.assertIn("Блок документов водителя отображается только для роли `driver`", self.publish_flow_doc)
        self.assertIn("profileVerificationBadge", self.publish_flow_doc)
        self.assertIn("profileTrustBadge", self.publish_flow_doc)

    def test_automation_plan_has_ci_project_and_reporting_sections(self) -> None:
        self.assertIn("## CI-проверки для #172", self.plan_doc)
        self.assertIn("## Проект и подзадачи", self.plan_doc)
        self.assertIn("## Автообновление Project", self.plan_doc)
        self.assertIn("## Зависимости между issues (blocked / blocking)", self.plan_doc)
        self.assertIn("Пометить как заблокированный", self.plan_doc)
        self.assertIn("Пометить как блокировку", self.plan_doc)
        self.assertIn("## Еженедельный отчёт", self.plan_doc)


if __name__ == "__main__":
    unittest.main()
