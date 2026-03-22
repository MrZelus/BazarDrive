import unittest
from pathlib import Path


class FeedPublishProfileNavigationFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = Path("web/js/feed.js").read_text(encoding="utf-8")
        self.page = Path("guest_feed.html").read_text(encoding="utf-8")
        self.readme = Path("README.md").read_text(encoding="utf-8")
        self.flow_doc = Path("docs/feed_navigation_publish_flow.md").read_text(encoding="utf-8")

    def test_publish_redirects_to_profile_and_stores_draft_when_profile_invalid(self) -> None:
        self.assertIn("const PENDING_POST_DRAFT_STORAGE_KEY = 'bazardrive_pending_post_draft';", self.script)
        self.assertIn("storePendingPostDraft(text);", self.script)
        self.assertIn("setActiveScreen('profile');", self.script)
        self.assertIn("setActiveProfileTab('documents');", self.script)
        self.assertIn("После сохранения публикация продолжится автоматически.", self.script)

    def test_profile_save_resumes_pending_publication(self) -> None:
        self.assertIn("const pendingDraft = consumePendingPostDraft();", self.script)
        self.assertIn("setActiveScreen('feed');", self.script)
        self.assertIn("await addNewPost();", self.script)

    def test_rate_limit_429_has_retry_after_message(self) -> None:
        self.assertIn("if (response.status === 429) {", self.script)
        self.assertIn("payload.retry_after ?? response.headers.get('Retry-After')", self.script)
        self.assertIn("Слишком много публикаций за короткое время.", self.script)

    def test_docs_and_readme_describe_navigation_map_and_test_cases(self) -> None:
        self.assertIn("docs/feed_navigation_publish_flow.md", self.readme)
        self.assertIn("## 1) Карта переходов между разделами", self.flow_doc)
        self.assertIn("### Rate limit (`429 Too Many Requests`)", self.flow_doc)
        self.assertIn("### Навигация между разделами", self.flow_doc)

    def test_unified_notifications_are_used_instead_of_alert(self) -> None:
        self.assertIn("const appNotification = document.getElementById('appNotification');", self.script)
        self.assertIn("function showAppNotification(message = '', type = 'info') {", self.script)
        self.assertNotIn("alert(", self.script)
        self.assertIn('id="appNotification"', self.page)


if __name__ == "__main__":
    unittest.main()
