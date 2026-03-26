import unittest
from pathlib import Path
import re


class DriverDocumentsUISmokeTests(unittest.TestCase):
    def test_add_document_button_and_form_exist(self) -> None:
        html = Path('guest_feed.html').read_text(encoding='utf-8')
        self.assertIn('id="addDocumentBtn"', html)
        self.assertIn('id="addDocumentForm"', html)
        self.assertIn('Добавить документ', html)
        self.assertIn('id="driverOverviewDocuments"', html)
        self.assertIn('Профиль водителя', html)
        self.assertNotIn('Добавить поездку', html)

    def test_documents_flow_functions_exist_in_script(self) -> None:
        script = Path('web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('loadDriverDocuments', script)
        self.assertIn('submitDriverDocument', script)
        self.assertIn('/api/driver/documents', script)
        self.assertIn('renderDriverOverviewDocuments', script)
        self.assertIn('mapDocumentStatus', script)
        self.assertRegex(
            script,
            re.compile(r"function setActiveProfileTab\(tab\)[\s\S]+if \(tab === 'documents'\)\s*\{\s*loadDriverDocuments\(\);", re.MULTILINE),
        )

    def test_documents_list_has_explicit_loading_state(self) -> None:
        html = Path('guest_feed.html').read_text(encoding='utf-8')
        script = Path('web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="driverDocumentsLoadingState"', html)
        self.assertIn('Загружаем документы...', html)
        self.assertIn('function setDriverDocumentsListLoading(isLoading)', script)
        self.assertRegex(
            script,
            re.compile(
                r"async function loadDriverDocuments\(\)\s*\{\s*setDriverDocumentsListLoading\(true\);[\s\S]+finally\s*\{\s*setDriverDocumentsListLoading\(false\);",
                re.MULTILINE,
            ),
        )

    def test_documents_tab_has_trust_signals_prepared_for_verification_states(self) -> None:
        html = Path('guest_feed.html').read_text(encoding='utf-8')
        script = Path('web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('id="profileVerificationBadge"', html)
        self.assertIn('id="profileTrustBadge"', html)
        self.assertIn('function resolveVerificationState(profile)', script)
        self.assertIn('function renderProfileTrustSignals(profile)', script)
        self.assertIn('pending_verification', script)
        self.assertIn('verification_state', script)


if __name__ == '__main__':
    unittest.main()
