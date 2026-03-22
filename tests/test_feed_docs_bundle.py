import unittest
from pathlib import Path


class FeedDocsBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = Path('README.md').read_text(encoding='utf-8')
        self.openapi = Path('docs/openapi.yaml').read_text(encoding='utf-8')
        self.flow = Path('docs/feed_navigation_publish_flow.md').read_text(encoding='utf-8')
        self.qa = Path('docs/feed_qa_regression.md').read_text(encoding='utf-8')

    def test_readme_contains_links_to_feed_docs_bundle(self) -> None:
        self.assertIn('docs/openapi.yaml', self.readme)
        self.assertIn('docs/feed_navigation_publish_flow.md', self.readme)
        self.assertIn('docs/feed_qa_regression.md', self.readme)

    def test_openapi_covers_core_feed_endpoints(self) -> None:
        self.assertIn('/api/feed/posts:', self.openapi)
        self.assertIn('/api/feed/profiles:', self.openapi)
        self.assertIn('/api/feed/publication-rules:', self.openapi)
        self.assertIn('/api/driver/documents:', self.openapi)

    def test_qa_doc_contains_smoke_and_regression_sections(self) -> None:
        self.assertIn('## 1) Smoke (быстрый прогон)', self.qa)
        self.assertIn('## 2) Регрессия (обязательный набор)', self.qa)
        self.assertIn('## 3) Автотесты (локальный минимум)', self.qa)

    def test_flow_doc_has_navigation_map_section(self) -> None:
        self.assertIn('## 1) Карта переходов между разделами', self.flow)


if __name__ == '__main__':
    unittest.main()
