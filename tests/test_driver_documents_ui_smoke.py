import unittest
from pathlib import Path


class DriverDocumentsUISmokeTests(unittest.TestCase):
    def test_add_document_button_and_form_exist(self) -> None:
        html = Path('guest_feed.html').read_text(encoding='utf-8')
        self.assertIn('id="addDocumentBtn"', html)
        self.assertIn('id="addDocumentForm"', html)
        self.assertIn('Добавить документ', html)

    def test_documents_flow_functions_exist_in_script(self) -> None:
        script = Path('web/js/feed.js').read_text(encoding='utf-8')
        self.assertIn('loadDriverDocuments', script)
        self.assertIn('submitDriverDocument', script)
        self.assertIn('/api/driver/documents', script)


if __name__ == '__main__':
    unittest.main()
