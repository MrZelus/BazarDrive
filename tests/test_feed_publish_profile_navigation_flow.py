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

    def test_publish_precheck_hint_and_local_moderation_guard_are_present(self) -> None:
        self.assertIn('id="publishPrecheckHint"', self.page)
        self.assertIn("aria-describedby=\"publishPrecheckHint\"", self.page)
        self.assertIn('id="feedSearch"', self.page)
        self.assertIn('id="feedSearchStatus"', self.page)
        self.assertIn("function getPublishPrecheckState(textValue = '') {", self.script)
        self.assertIn("applyPublishPrecheckHint(getPublishPrecheckState(newPostInput.value));", self.script)
        self.assertIn("if (precheckState.type === 'warning') {", self.script)

    def test_moderation_error_messages_are_unified_for_ui(self) -> None:
        self.assertIn("const MODERATION_ERROR_COPY = {", self.script)
        self.assertIn("function resolveModerationErrorMessage(rawMessage = '') {", self.script)
        self.assertIn("throw new Error(resolveModerationErrorMessage(", self.script)

    def test_interaction_error_messages_are_unified_for_comments_and_reactions(self) -> None:
        self.assertIn("const INTERACTION_ERROR_COPY = {", self.script)
        self.assertIn(
            "function resolveInteractionErrorMessage(rawMessage = '', rawCode = '', fallbackMessage = 'Не удалось выполнить действие.') {",
            self.script,
        )
        self.assertIn("forbiddenCommentEdit: 'Можно редактировать только свои комментарии.'", self.script)
        self.assertIn("forbiddenCommentDelete: 'Можно удалять только свои комментарии.'", self.script)
        self.assertIn("if (code === 'comment_edit_forbidden') return INTERACTION_ERROR_COPY.forbiddenCommentEdit;", self.script)
        self.assertIn("if (code === 'comment_delete_forbidden') return INTERACTION_ERROR_COPY.forbiddenCommentDelete;", self.script)
        self.assertIn(
            "throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось установить реакцию (HTTP ${response.status})`));",
            self.script,
        )
        self.assertIn(
            "throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось добавить комментарий (HTTP ${response.status})`));",
            self.script,
        )

    def test_feed_search_input_triggers_server_side_query_reload(self) -> None:
        self.assertIn("let feedSearchQuery = '';", self.script)
        self.assertIn("let feedPendingReset = false;", self.script)
        self.assertIn("params.set('q', feedSearchQuery);", self.script)
        self.assertIn("feedSearch?.addEventListener('input', (event) => {", self.script)
        self.assertIn("loadPosts({ reset: true });", self.script)
        self.assertIn("Введите ещё ${2 - raw.length} символ(а), чтобы включить поиск.", self.script)
        self.assertIn("if (feedIsLoading) {", self.script)
        self.assertIn("if (reset) {", self.script)
        self.assertIn("feedPendingReset = true;", self.script)
        self.assertIn("if (feedPendingReset) {", self.script)
        self.assertIn("feedSearchQuery = raw;", self.script)

    def test_docs_and_readme_describe_navigation_map_and_test_cases(self) -> None:
        self.assertIn("docs/feed_navigation_publish_flow.md", self.readme)
        self.assertIn("## 1) Карта переходов между разделами", self.flow_doc)
        self.assertIn("### Rate limit (`429 Too Many Requests`)", self.flow_doc)
        self.assertIn("### Навигация между разделами", self.flow_doc)
        self.assertIn("## 5) Ролевая матрица профиля (актуально для #160)", self.flow_doc)
        self.assertIn("`driver`: `overview`, `taxi_ip`, `documents`, `payouts`, `security`.", self.flow_doc)
        self.assertIn("`passenger`: `overview`, `documents`, `security`.", self.flow_doc)
        self.assertIn("`guest`: `overview`, `documents`, `security`.", self.flow_doc)

    def test_unified_notifications_are_used_instead_of_alert(self) -> None:
        self.assertIn("const appNotification = document.getElementById('appNotification');", self.script)
        self.assertIn("function showAppNotification(message = '', type = 'info') {", self.script)
        self.assertNotIn("alert(", self.script)
        self.assertIn('id="appNotification"', self.page)

    def test_role_matrix_and_documents_blocks_match_issue_160(self) -> None:
        self.assertIn("const ROLE_TABS = {", self.script)
        self.assertIn("driver: ['overview', 'taxi_ip', 'documents', 'payouts', 'security']", self.script)
        self.assertIn("passenger: ['overview', 'documents', 'security']", self.script)
        self.assertIn("guest: ['overview', 'documents', 'security']", self.script)
        self.assertIn("const activeTab = allowedTabs.has(requestedTab) ? requestedTab : PROFILE_TAB_FALLBACK;", self.script)
        self.assertIn("if (!allowedTabs.has(currentActiveTab)) {", self.script)
        self.assertIn('id="guestProfileStatus"', self.page)
        self.assertIn('id="driverDocumentsSection"', self.page)


if __name__ == "__main__":
    unittest.main()
